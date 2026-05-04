import sqlite3
import time

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
    # We need to prevent the flusher from running immediately or wait for it.
    # Since _trigger_buffer_flush starts a thread, we might need to wait a bit.

    # Actually, NtfyBuffer.__init__ calls _trigger_buffer_flush.
    # But it might finish before we add the message if the DB is empty.

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
