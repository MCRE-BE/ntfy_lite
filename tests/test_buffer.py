import logging
import sqlite3
from pathlib import Path

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
        raise sqlite3.Error("Connection failed")

    # Monkeypatch sqlite3.connect ONLY for the add call
    monkeypatch.setattr("ntfy_lite.buffer.sqlite3.connect", mock_connect)

    with caplog.at_level(logging.ERROR):
        buffer.add("topic", "url", "data", {})

    assert "Failed to buffer NTFY message" in caplog.text
