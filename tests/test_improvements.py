"""Unit tests for recent improvements."""

from pathlib import Path
from unittest.mock import patch

from ntfy_lite.actions import Action, ViewAction
from ntfy_lite.buffer import NtfyBuffer
from ntfy_lite.config import Priority
from ntfy_lite.ntfy import _build_headers, _DataPayload


def test_trigger_buffer_flush_starts_thread():
    """Verify that _trigger_buffer_flush starts a thread only when not running."""
    # We need to mock sqlite3.connect to avoid creating a real file
    # and threading.Thread to avoid actually spawning a background worker.
    with patch("ntfy_lite.buffer.sqlite3.connect"), patch("ntfy_lite.buffer.threading.Thread") as mock_thread:
        buffer = NtfyBuffer(Path("test_dummy.sqlite"))

        # Initial call in __init__ should have started the thread
        assert mock_thread.call_count == 1

        # Reset mock and call again while running state is True
        mock_thread.reset_mock()
        buffer._flusher_state["running"] = True
        buffer._trigger_buffer_flush()
        mock_thread.assert_not_called()

        # Call again after resetting running state to False
        buffer._flusher_state["running"] = False
        buffer._trigger_buffer_flush()
        mock_thread.assert_called_once()
        assert buffer._flusher_state["running"] is True


def test_build_headers_branches():
    """Verify _build_headers covers all branches including tags and actions."""
    payload = _DataPayload(data="body")

    # 1. Basic configuration
    h = _build_headers("Title", Priority.DEFAULT, None, None, None, None, [], None, payload)
    assert h["Title"] == "Title"
    assert h["Priority"] == "3"
    assert "Tags" not in h
    assert "Actions" not in h

    # 2. Tags as string
    h = _build_headers("T", Priority.HIGH, "tag1", None, None, None, [], None, payload)
    assert h["Tags"] == "tag1"

    # 3. Tags as list
    h = _build_headers("T", Priority.HIGH, ["t1", "t2"], None, None, None, [], None, payload)
    assert h["Tags"] == "t1,t2"

    # 4. Actions (single instance)
    action = ViewAction("label", "https://example.com")
    h = _build_headers("T", Priority.DEFAULT, None, None, None, None, action, None, payload)
    assert "Actions" in h
    assert "label=label" in h["Actions"]
    assert "url=https://example.com" in h["Actions"]

    # 5. Actions (sequence)
    h = _build_headers("T", Priority.DEFAULT, None, None, None, None, [action, action], None, payload)
    assert h["Actions"].count("view") == 2
    assert ";" in h["Actions"]

    # 6. Message header (base64 encoding)
    payload.message_header = "Hello World"
    h = _build_headers("T", Priority.DEFAULT, None, None, None, None, [], None, payload)
    assert "Message" in h
    assert "=?UTF-8?B?" in h["Message"]

    # 7. Filename header
    payload.filename_header = "file.txt"
    h = _build_headers("T", Priority.DEFAULT, None, None, None, None, [], None, payload)
    assert h["Filename"] == "file.txt"


def test_quote_robustness():
    """Test improved quoting for backslashes and newlines in action attributes."""
    # Backslash escaping
    assert Action._quote("a\\b") == '"a\\\\b"'

    # Quote and backslash escaping
    assert Action._quote('a"\\b') == '"a\\"\\\\b"'

    # Newline replacement
    assert Action._quote("a\nb") == "a b"
    assert Action._quote("a\rb") == "ab"

    # Combination of characters requiring quoting and replacement
    # "a, b" -> contains comma, should be quoted. Newline should be replaced by space.
    assert Action._quote("a,\nb") == '"a, b"'

    # Semicolon requiring quoting
    assert Action._quote("a;b") == '"a;b"'
