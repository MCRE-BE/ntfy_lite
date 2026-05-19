import logging
import runpy
import sqlite3
import sys
from pathlib import Path
from unittest import mock

import pytest
import responses

import ntfy_lite
import ntfy_lite.error
from ntfy_lite import NtfyHandler, push
from ntfy_lite.buffer import NtfyBuffer
from ntfy_lite.cli import main
from ntfy_lite.formatter import AttachmentFormatter, TruncationFormatter
from ntfy_lite.version import __version__


def test_version_coverage():
    """Cover version.py."""
    assert __version__ is not None


def test_cli_main_coverage(monkeypatch):
    """Cover cli.py main() and __main__ block."""
    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["ntfy-lite", "topic", "title", "-m", "message"])

    # Mock push to avoid network calls
    with mock.patch("ntfy_lite.cli.push"):
        # runpy.run_module executes the module, covering the if __name__ == "__main__" block
        runpy.run_module("ntfy_lite.cli", run_name="__main__", alter_sys=True)

    # Test error path
    monkeypatch.setattr(sys, "argv", ["ntfy-lite", "topic", "title"])
    with mock.patch("ntfy_lite.cli.push", side_effect=Exception("Error")):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_formatter_edge_cases():
    """Cover formatter.py lines 118 and 194 (max_length <= 0)."""
    af = AttachmentFormatter(max_length=0)
    res = af.process("too long")
    assert res["message_header"] == af.truncation_message

    tf = TruncationFormatter(max_length=0)
    res = tf.process("too long")
    assert res["data"] == tf.truncation_message


def test_handler_db_path_string(tmp_path):
    """Cover handler.py lines 128-129 (db_path as string)."""
    db_file = tmp_path / "test.db"
    handler = NtfyHandler("topic", db_path=str(db_file))
    assert handler._buffer is not None
    assert isinstance(handler._buffer.db_path, Path)
    assert handler._buffer.db_path == db_file


def test_handler_no_buffer_warning():
    """Cover handler.py lines 136-142 (_HAS_BUFFER is False)."""
    with mock.patch("ntfy_lite.handler._HAS_BUFFER", False), pytest.warns(UserWarning, match="Buffering requested"):
        handler = NtfyHandler("topic", db_path=True)
    assert handler._buffer is None


def test_handler_validation_error():
    """Cover handler.py lines 147-151 (validation error)."""
    # Level 50 (CRITICAL) has tags but no priority
    with pytest.raises(ValueError, match="missing mapping from logging level 50"):
        NtfyHandler("topic", level2tags={50: ("tag",)}, level2priority={})


def test_handler_extra_logger_name():
    """Cover handler.py line 177 (record.extra['logger_name'])."""
    handler = NtfyHandler("topic")
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", (), None)
    record.extra = {"logger_name": "custom_title"}

    with mock.patch("ntfy_lite.handler.push") as mock_push:
        handler.emit(record)
        mock_push.assert_called_once()
        assert mock_push.call_args[1]["title"] == "custom_title"


def test_ntfy_push_exception_message():
    """Cover ntfy.py line 88 (Exception as message)."""
    e = ValueError("test error")
    # We just want to see it formatted
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message=e)
        data = mock_put.call_args[1]["data"]
        assert "ValueError: test error" in data


def test_ntfy_push_object_message():
    """Cover ntfy.py line 90 (Non-string object as message)."""
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message=[1, 2, 3])
        data = mock_put.call_args[1]["data"]
        assert data == "[1, 2, 3]"


def test_ntfy_push_both_message_and_file(tmp_path):
    """Cover ntfy.py line 100 (Both message and filepath)."""
    f = tmp_path / "test.txt"
    f.write_text("file content")

    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message="msg content", filepath=f)
        headers = mock_put.call_args[1]["headers"]
        # message_header should be set in headers['Message'] (b64 encoded)
        assert "Message" in headers
        assert headers["Message"].startswith("=?UTF-8?B?")


def test_ntfy_temp_file_cleanup():
    """Cover ntfy.py lines 125-126 (_temp_file_path cleanup)."""

    # We need a formatter that returns a temp_file_path
    class TempFileFormatter(ntfy_lite.formatter.Formatter):
        def process(self, message: str) -> ntfy_lite.formatter.FormatterPayload:
            del message
            res = self._default_payload()
            res["temp_file_path"] = "non_existent_file_to_trigger_suppress"
            return res

    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message="msg", formatter=TempFileFormatter())
        # Should not raise even if file doesn't exist due to suppress(OSError)


def test_ntfy_tags_single_string():
    """Cover ntfy.py line 201 (tags as a single string)."""
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message="msg", tags="skull")
        headers = mock_put.call_args[1]["headers"]
        assert headers["Tags"] == "skull"


@responses.activate
def test_ntfy_push_429_no_buffer():
    """Cover ntfy.py line 231 (HTTP 429 with buffer=None)."""
    responses.add(responses.PUT, "https://ntfy.sh/topic", status=429)

    with pytest.raises(ntfy_lite.error.NtfyError) as exc:
        push("topic", "title", message="msg", buffer=None)
    assert exc.value.status_code == 429


def test_ntfy_filename_header():
    """Cover ntfy.py line 193 (Filename header)."""
    # AttachmentFormatter sets filename_header when truncation happens
    af = AttachmentFormatter(max_length=5)
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push("topic", "title", message="very long message", formatter=af)
        headers = mock_put.call_args[1]["headers"]
        assert headers["Filename"] == "traceback.txt"


def test_buffer_batch_delete_exception(tmp_path):
    """Cover buffer.py lines 162-163 (Exception in batch delete)."""
    db_path = tmp_path / "test.db"

    # Disable background thread by mocking _trigger_buffer_flush
    with mock.patch("ntfy_lite.buffer.NtfyBuffer._trigger_buffer_flush"):
        buffer = NtfyBuffer(db_path)
        # Manually add a row to the DB
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute(
                "INSERT INTO buffer (topic, url, headers, data) VALUES (?, ?, ?, ?)",
                ("topic", "url", '{"h": "v"}', "data"),
            )

    # Mock sqlite3.connect to return a mock connection that raises on executemany
    # We need to be careful because _flush_buffer_thread calls connect twice
    mock_conn = mock.MagicMock()
    mock_conn.cursor.return_value.fetchall.return_value = [(1, "topic", "url", '{"h": "v"}', "data")]
    mock_conn.executemany.side_effect = sqlite3.Error("Mock error")
    mock_conn.__enter__.return_value = mock_conn

    with (
        mock.patch("sqlite3.connect", return_value=mock_conn),
        mock.patch("ntfy_lite.buffer.requests.Session.put") as mock_put,
        mock.patch("logging.exception") as mock_log,
    ):
        mock_put.return_value.ok = True
        buffer._flush_buffer_thread()
        mock_log.assert_called_with("Failed to batch delete buffered messages.")


def test_handler_url_trailing_slash() -> None:
    """Cover handler.py line 115 (warning and stripping of trailing slash in URL)."""
    with pytest.warns(
        expected_warning=UserWarning,
        match="Trailing slash detected in NtfyHandler URL",
    ):
        handler = NtfyHandler(
            "topic",
            url="https://example.com/foo/",
            db_path=False,
        )
    assert handler._url == "https://example.com/foo"


def test_ntfy_push_url_none() -> None:
    """Cover ntfy.py line 306 (url is None)."""
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        push(
            "topic",
            "title",
            message="msg",
            url=None,
        )
        # Should default to https://ntfy.sh
        assert mock_put.call_args[0][0] == "https://ntfy.sh/topic"


def test_ntfy_push_url_trailing_slash() -> None:
    """Cover ntfy.py line 310 (warning and stripping of trailing slash in push)."""
    with mock.patch("ntfy_lite.ntfy._session.put") as mock_put:
        mock_put.return_value.ok = True
        with pytest.warns(
            expected_warning=UserWarning,
            match="Trailing slash detected in ntfy URL",
        ):
            push(
                "topic",
                "title",
                message="msg",
                url="https://example.com/bar/",
            )
        assert mock_put.call_args[0][0] == "https://example.com/bar/topic"
