import sqlite3
import time
from pathlib import Path
from unittest import mock

import requests

from ntfy_lite.buffer import NtfyBuffer


def test_flusher_handles_request_exception(tmp_path, monkeypatch, caplog):
    """Verify that the flusher handles requests.RequestException and stops."""
    # Mock sleep to avoid waiting
    monkeypatch.setattr(time, "sleep", lambda _: None)

    # Mock requests.put to raise an exception
    def mock_put(*args, **kwargs):
        raise requests.RequestException("Connection error")

    monkeypatch.setattr(requests, "put", mock_put)

    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)

    # Add a message to the buffer
    buffer.add("topic", "http://localhost", "data", {"header": "value"})

    # Wait for the flusher thread to potentially run and exit
    max_wait = 5
    start_time = time.time()
    while buffer._flusher_state["running"] and time.time() - start_time < max_wait:
        time.sleep(0.1)

    assert not buffer._flusher_state["running"]
    assert "NTFY async flusher exception." in caplog.text


def test_flusher_handles_json_decode_error(tmp_path, monkeypatch, caplog):
    """Verify that the flusher handles json.JSONDecodeError (though unlikely with current code)."""
    monkeypatch.setattr(time, "sleep", lambda _: None)

    db_path = tmp_path / "test_buffer_json.sqlite"

    # Manually insert invalid JSON into the database
    db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                url TEXT,
                headers TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "INSERT INTO buffer (topic, url, headers, data) VALUES (?, ?, ?, ?)",
            ("topic", "http://localhost", "invalid-json", "data"),
        )

    buffer = NtfyBuffer(db_path)
    # The flusher is triggered on init

    max_wait = 5
    start_time = time.time()
    while buffer._flusher_state["running"] and time.time() - start_time < max_wait:
        time.sleep(0.1)

    assert not buffer._flusher_state["running"]
    assert "NTFY async flusher exception." in caplog.text


def test_flush_buffer_thread_exception(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh/", "test_data_1", {"Header": "value1"})
    buffer.add("test_topic", "https://ntfy.sh/", "test_data_2", {"Header": "value2"})

    buffer._flusher_state["running"] = True

    with (
        mock.patch("ntfy_lite.buffer.requests.put", side_effect=Exception("Test Error")),
        mock.patch("ntfy_lite.buffer.time.sleep"),
    ):
        buffer._flush_buffer_thread()

    assert not buffer._flusher_state["running"]


def test_flush_buffer_thread_batch_delete_exception(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)
    buffer.add("test_topic", "https://ntfy.sh/", "test_data", {"Header": "value"})

    class MockResponse:
        ok = True
        status_code = 200

    buffer._flusher_state["running"] = True

    # Patch the sqlite connect only for the delete path.
    # The first connect is the select which we let pass.

    original_connect = sqlite3.connect
    connect_calls = 0

    def mocked_connect(*args, **kwargs):
        nonlocal connect_calls
        connect_calls += 1
        if connect_calls == 3:  # 1st: add(), 2nd: SELECT, 3rd: DELETE
            raise Exception("Delete Error")
        return original_connect(*args, **kwargs)

    with (
        mock.patch("ntfy_lite.buffer.requests.put", return_value=MockResponse()),
        mock.patch("ntfy_lite.buffer.time.sleep"),
        mock.patch("ntfy_lite.buffer.sqlite3.connect", side_effect=mocked_connect),
    ):
        buffer._flush_buffer_thread()

    assert not buffer._flusher_state["running"]
