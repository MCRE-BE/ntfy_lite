"""Tests for NtfyHandler initialization."""

import logging
from pathlib import Path

import pytest

import ntfy_lite as ntfy
from ntfy_lite.config import Priority, level2priority, level2tags


def test_handler_init_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test NtfyHandler initialization with default values."""
    # Mock Path.home to avoid touching user's home directory
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    # Ensure environment doesn't disable buffer
    monkeypatch.delenv("NTFY_LITE_DISABLE_BUFFER", raising=False)

    topic = "test_topic"
    handler = ntfy.NtfyHandler(topic)

    assert handler._topic == topic
    assert handler._url == "https://ntfy.sh"
    assert handler._last_messages is None  # twice_in_a_row=True by default
    assert handler._level2tags == level2tags
    assert handler._level2priority == level2priority
    assert handler._level2filepath == {}
    assert handler._level2email == {}
    assert handler._error_callback is None
    assert handler._formatter is None
    assert handler._buffer is not None
    assert handler._buffer.db_path == home_dir / ".ntify" / "ntfy_buffer.sqlite"


def test_handler_init_custom_args(tmp_path: Path):
    """Test NtfyHandler initialization with custom values."""
    topic = "custom_topic"
    url = "https://example.com"
    twice_in_a_row = False

    def my_callback(e: Exception):
        pass

    custom_tags = {logging.INFO: ("custom",)}
    custom_priority = {
        logging.CRITICAL: Priority.MAX,
        logging.ERROR: Priority.HIGH,
        logging.WARNING: Priority.HIGH,
        logging.INFO: Priority.DEFAULT,
        logging.DEBUG: Priority.LOW,
        logging.NOTSET: Priority.MIN,
    }
    custom_filepath = {logging.ERROR: tmp_path / "error.log"}
    custom_email = {logging.CRITICAL: "admin@example.com"}
    custom_formatter = ntfy.TruncationFormatter()

    handler = ntfy.NtfyHandler(
        topic,
        url=url,
        twice_in_a_row=twice_in_a_row,
        error_callback=my_callback,
        level2tags=custom_tags,
        level2priority=custom_priority,
        level2filepath=custom_filepath,
        level2email=custom_email,
        formatter=custom_formatter,
        db_path=False,  # Disable buffer to simplify
    )

    assert handler._topic == topic
    assert handler._url == url
    assert handler._last_messages == {}
    assert handler._level2tags == custom_tags
    assert handler._level2priority == custom_priority
    assert handler._level2filepath == custom_filepath
    assert handler._level2email == custom_email
    assert handler._error_callback == my_callback
    assert handler._formatter == custom_formatter
    assert handler._buffer is None


def test_handler_init_db_path_variations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test various db_path configurations."""
    topic = "test_topic"

    # db_path=False
    handler_no_buf = ntfy.NtfyHandler(topic, db_path=False)
    assert handler_no_buf._buffer is None

    # db_path as string
    custom_db_path_str = str(tmp_path / "custom.sqlite")
    handler_str_path = ntfy.NtfyHandler(topic, db_path=custom_db_path_str)
    assert handler_str_path._buffer is not None
    assert handler_str_path._buffer.db_path == Path(custom_db_path_str)

    # db_path as Path
    custom_db_path = tmp_path / "custom_path.sqlite"
    handler_path = ntfy.NtfyHandler(topic, db_path=custom_db_path)
    assert handler_path._buffer is not None
    assert handler_path._buffer.db_path == custom_db_path

    # db_path=True (should use default)
    home_dir = tmp_path / "home_v2"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    handler_true = ntfy.NtfyHandler(topic, db_path=True)
    assert handler_true._buffer is not None
    assert handler_true._buffer.db_path == home_dir / ".ntify" / "ntfy_buffer.sqlite"


def test_handler_init_disable_buffer_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test NTFY_LITE_DISABLE_BUFFER environment variable."""
    topic = "test_topic"
    monkeypatch.setenv("NTFY_LITE_DISABLE_BUFFER", "1")

    # Even if db_path is provided, it should be disabled
    custom_db_path = tmp_path / "should_not_exist.sqlite"
    handler = ntfy.NtfyHandler(topic, db_path=custom_db_path)
    assert handler._buffer is None

    # Try "true" instead of "1"
    monkeypatch.setenv("NTFY_LITE_DISABLE_BUFFER", "true")
    handler_true = ntfy.NtfyHandler(topic)
    assert handler_true._buffer is None


def test_handler_init_invalid_priority():
    """Test initialization with missing logging levels in level2priority."""
    topic = "test_topic"
    # level2priority defaults include several levels. If we pass a dict missing one of them, it should raise ValueError.
    # Wait, the code checks:
    # for logging_level in level2priority:
    #     if logging_level not in self._level2priority:
    #         ... raise ValueError ...
    # It checks against the GLOBAL level2priority.

    incomplete_priority = {logging.ERROR: Priority.HIGH}
    with pytest.raises(ValueError, match="missing mapping from logging level"):
        ntfy.NtfyHandler(topic, level2priority=incomplete_priority)
