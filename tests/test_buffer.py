import logging
import sqlite3
import time
import uuid
from pathlib import Path
from unittest import mock

import pytest

from ntfy_lite.buffer import NtfyBuffer


def test_ntfy_buffer_add_success(tmp_path: Path):
    db_path = tmp_path / "test_buffer.sqlite"
    buffer = NtfyBuffer(db_path)

    topic = "test_topic"
    url = "https://ntfy.sh"
    data = "test_data"
    headers = {"X-Title": "Test"}

    buffer.add(topic, url, data, headers)

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, url, data, headers FROM buffer")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == topic
        assert row[1] == url
        assert row[2] == data
        assert '"X-Title": "Test"' in row[3]


def test_ntfy_buffer_add_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    db_path = tmp_path / "test_buffer_error.sqlite"
    buffer = NtfyBuffer(db_path)

    def mock_connect(*args, **kwargs):
        msg = "Connection failed"
        raise sqlite3.Error(msg)

    # Monkeypatch sqlite3.connect ONLY for the add call
    monkeypatch.setattr("ntfy_lite.buffer.sqlite3.connect", mock_connect)

    with caplog.at_level(logging.ERROR):
        buffer.add("topic", "url", "data", {})

    assert "Failed to buffer NTFY message" in caplog.text


def test_ntfy_buffer_flush_no_429(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
):

    db_path = tmp_path / "test_buffer_flush_429_integration.sqlite"

    # Patch Thread.start to prevent flusher from auto-running on init/add
    # so we can control exactly when it starts
    with mock.patch("threading.Thread.start"):
        buffer = NtfyBuffer(db_path)
        topic = f"test_ntfy_flush_{uuid.uuid4().hex}"
        url = "https://ntfy.sh"

        # Add multiple messages
        buffer.add(topic, url, "data1", {})
        buffer.add(topic, url, "data2", {})
        buffer.add(topic, url, "data3", {})
        buffer.add(topic, url, "data4", {})
        buffer.add(topic, url, "data5", {})
        buffer.add(topic, url, "data6", {})

    # Clear the caplog before starting the flush
    caplog.clear()

    # Ensure running is False so _trigger_buffer_flush actually starts a thread
    # (The __init__ call set it to True but the mock prevented the thread from starting)
    buffer._flusher_state["running"] = False

    # Now we start the REAL background thread to verify it works with real ntfy.sh
    buffer._trigger_buffer_flush()

    # Wait for the background thread to finish
    # It will take ~4-5 seconds normally, but 60s if it hits a 429
    timeout = 80
    start_time = time.time()
    while buffer._flusher_state["running"] and time.time() - start_time < timeout:
        time.sleep(1)

    assert not buffer._flusher_state["running"], "Integration flusher thread did not finish in time"

    # Check that no 429 warning was logged
    assert "NTFY buffer fast retry rate limited" not in caplog.text

    # Check that DB is empty, meaning all messages successfully flushed
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM buffer")
        rows = cursor.fetchall()
        assert len(rows) == 0
