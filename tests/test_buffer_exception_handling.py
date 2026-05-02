"""Tests for exception handling in NtfyBuffer."""

import logging
import sqlite3
from pathlib import Path

import pytest

from ntfy_lite.buffer import NtfyBuffer


def test_init_db_exception(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that NtfyBuffer._init_db handles and logs sqlite3 exceptions properly."""
    db_path = tmp_path / "buffer.sqlite"

    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock database connection error")

    monkeypatch.setattr(sqlite3, "connect", mock_connect)

    with caplog.at_level(logging.ERROR):
        _ = NtfyBuffer(db_path)

    assert "Failed to initialize ntfy SQLite buffer" in caplog.text
