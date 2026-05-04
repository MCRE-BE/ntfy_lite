import logging
import sqlite3
from pathlib import Path
from unittest import mock

import pytest

from ntfy_lite.buffer import NtfyBuffer


def test_flush_buffer_thread_success(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh", "test_data", {"Header": "value"})

    class MockResponse:
        ok = True
        status_code = 200

    buffer._flusher_state["running"] = True

    with (
        mock.patch("ntfy_lite.buffer.requests.put", return_value=MockResponse()) as mock_put,
        mock.patch("ntfy_lite.buffer.time.sleep") as mock_sleep,
    ):
        buffer._flush_buffer_thread()

    assert mock_put.called
    assert mock_sleep.called

    # Verify db is empty
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM buffer")
        count = cursor.fetchone()[0]
        assert count == 0

    assert not buffer._flusher_state["running"]


def test_flush_buffer_thread_429(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh", "test_data_1", {"Header": "value1"})
    buffer.add("test_topic", "https://ntfy.sh", "test_data_2", {"Header": "value2"})

    class MockResponse:
        ok = False
        status_code = 429

    buffer._flusher_state["running"] = True

    with (
        mock.patch("ntfy_lite.buffer.requests.put", return_value=MockResponse()) as mock_put,
        mock.patch("ntfy_lite.buffer.time.sleep") as mock_sleep,
    ):
        buffer._flush_buffer_thread()

    assert mock_put.call_count == 1  # Should break after first 429
    assert mock_sleep.call_count == 1

    # Verify db still has both records
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM buffer")
        count = cursor.fetchone()[0]
        assert count == 2

    assert not buffer._flusher_state["running"]


def test_flush_buffer_thread_other_error(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh", "test_data", {"Header": "value"})

    class MockResponse:
        ok = False
        status_code = 500
        reason = "Internal Server Error"

    buffer._flusher_state["running"] = True

    with (
        mock.patch("ntfy_lite.buffer.requests.put", return_value=MockResponse()) as mock_put,
        mock.patch("ntfy_lite.buffer.time.sleep") as mock_sleep,
    ):
        buffer._flush_buffer_thread()

    assert mock_put.called
    assert mock_sleep.called

    # Verify db is empty because it discards the record
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM buffer")
        count = cursor.fetchone()[0]
        assert count == 0

    assert not buffer._flusher_state["running"]


def test_flush_buffer_thread_exception(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh", "test_data_1", {"Header": "value1"})
    buffer.add("test_topic", "https://ntfy.sh", "test_data_2", {"Header": "value2"})

    buffer._flusher_state["running"] = True

    with (
        mock.patch("ntfy_lite.buffer.requests.put", side_effect=Exception("Test Error")) as mock_put,
        mock.patch("ntfy_lite.buffer.time.sleep") as mock_sleep,
    ):
        buffer._flush_buffer_thread()

    assert mock_put.call_count == 1  # Should break after first exception
    assert mock_sleep.call_count == 1

    # Verify db still has both records since we break on exception
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM buffer")
        count = cursor.fetchone()[0]
        assert count == 2

    assert not buffer._flusher_state["running"]


def test_flush_buffer_thread_batch_delete_exception(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh", "test_data", {"Header": "value"})

    class MockResponse:
        ok = True
        status_code = 200

    buffer._flusher_state["running"] = True

    # Patch the sqlite connect only for the delete path.
    # The first connect is the select which we let pass.
    # We can mock sqlite3.connect and track calls, or easier:
    # Just cause an exception when it tries to delete by mocking `conn.executemany`.
    # Actually, we can patch `ntfy_lite.buffer.sqlite3.connect`.

    original_connect = sqlite3.connect
    connect_calls = 0

    def mocked_connect(*args, **kwargs):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 3:  # 1st: add(), 2nd: SELECT, 3rd: DELETE
            msg = "Delete Error"
            raise Exception(msg)
        return original_connect(*args, **kwargs)

    with (
        mock.patch("ntfy_lite.buffer.requests.put", return_value=MockResponse()),
        mock.patch("ntfy_lite.buffer.time.sleep"),
        mock.patch("ntfy_lite.buffer.sqlite3.connect", side_effect=mocked_connect),
    ):
        buffer._flush_buffer_thread()

    # If it handled the exception properly, it shouldn't crash, and `running` state is False
    assert not buffer._flusher_state["running"]


def test_init_db_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that NtfyBuffer._init_db handles and logs sqlite3 exceptions properly."""
    db_path = tmp_path / "buffer.sqlite"

    def mock_connect(*args, **kwargs):
        msg = "Mock database connection error"
        raise sqlite3.Error(msg)

    monkeypatch.setattr(
        sqlite3,
        "connect",
        mock_connect,
    )

    with caplog.at_level(logging.ERROR):
        _ = NtfyBuffer(db_path)

    assert "Failed to initialize ntfy SQLite buffer" in caplog.text
