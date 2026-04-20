# ruff: noqa: PT011
"""Tests."""

####################
# IMPORT STATEMENT #
####################
import logging
import sqlite3
import tempfile
import typing
from pathlib import Path

import pytest

import ntfy_lite as ntfy
from ntfy_lite.buffer import NtfyBuffer


####################
# INDIVIDUAL TESTS #
####################
def test_minimal_message_push():
    """Test a minimal push with only a topic, title, and message."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    ntfy.push(topic, title, message=message, dry_run=ntfy.DryRun.on)


def test_minimal_filepath_push():
    """Test a minimal push with a filepath."""

    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"

    with tempfile.TemporaryDirectory() as tmp:
        filepath = Path(tmp) / "test.txt"
        with open(filepath, "w") as f:
            f.write("test content")

        ntfy.push(topic, title, filepath=filepath, dry_run=ntfy.DryRun.on)


def test_tags_push():
    """Test a push with tags."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    tags = ["heart", "rainbow"]
    ntfy.push(topic, title, tags=tags, message=message, dry_run=ntfy.DryRun.on)


def test_click_push():
    """Test a push with a clickable URL."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    click = "https://is.mpg.de"
    ntfy.push(topic, title, click=click, message=message, dry_run=ntfy.DryRun.on)


def test_click_no_url_push():
    """Test a push with an invalid URL for click."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    click = "this is not an url"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, click=click, message=message, dry_run=ntfy.DryRun.on)


def test_email_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    email = "camembert@fromage.fr"
    ntfy.push(topic, title, email=email, message=message, dry_run=ntfy.DryRun.on)


def test_icon_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    icon = "https://styles.redditmedia.com/t5_32uhe/styles/communityIcon_xnt6chtnr2j21.png"
    ntfy.push(topic, title, icon=icon, message=message, dry_run=ntfy.DryRun.on)


def test_icon_not_url_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    icon = "not an url to an icon"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, icon=icon, message=message, dry_run=ntfy.DryRun.on)


def test_attach_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    attach = "https://ntfy.sh/flowers"
    ntfy.push(topic, title, attach=attach, message=message, dry_run=ntfy.DryRun.on)


def test_attach_not_an_url_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    attach = "not an url to an image"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, attach=attach, message=message, dry_run=ntfy.DryRun.on)


@pytest.mark.parametrize("clear", [True, False])
def test_action_view_push(clear):
    """Test ViewAction with clear flag."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    ntfy.push(topic, title, message=message, actions=action, dry_run=ntfy.DryRun.on)


@pytest.mark.parametrize("clear", [True, False])
def test_actions_view_push(clear):
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action1 = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    action2 = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    ntfy.push(topic, title, message=message, actions=[action1, action2], dry_run=ntfy.DryRun.on)


@pytest.mark.parametrize("clear", [True, False])
def test_action_view_not_url(clear):
    with pytest.raises(ValueError):
        ntfy.ViewAction("ntfy_lite view action", "not a valid url !", clear=clear)


@pytest.mark.parametrize("clear", [True, False])
def test_action_http_push(clear):
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action = ntfy.HttpAction(
        "ntfy_lite http action",
        "https://is.mpg.de",
        clear=clear,
        method=ntfy.HttpMethod.PUT,
        headers={"Authorization": "Bearer zAzsx1sk.."},
        body='{"action": "close"}',
    )
    ntfy.push(topic, title, message=message, actions=action, dry_run=ntfy.DryRun.on)


def test_extended_ascii_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test extended ascii push"
    message = "ntfy_extended_ascii_push message: (°_°)"
    ntfy.push(topic, title, message=message, dry_run=ntfy.DryRun.on)


def test_unicode_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test unicode push"
    message = "ntfy unicode push message: 🐋💐🪂"
    ntfy.push(topic, title, message=message, dry_run=ntfy.DryRun.on)


@pytest.mark.parametrize("clear", [True, False])
def test_actions_view_http_push(clear: bool):
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action1 = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    action2 = ntfy.HttpAction(
        "ntfy_lite http action",
        "https://is.mpg.de",
        clear=clear,
        method=ntfy.HttpMethod.PUT,
        headers={"Authorization": "Bearer zAzsx1sk.."},
        body='{"action": "close"}',
    )
    ntfy.push(topic, title, message=message, actions=[action1, action2], dry_run=ntfy.DryRun.on)


def test_at_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    at = "1 minute"
    ntfy.push(topic, title, at=at, message=message, dry_run=ntfy.DryRun.on)


# required for mypy
_callback_called: bool = False


################
# COMPLEX TEST #
################
@pytest.mark.parametrize("logging_level", [logging.ERROR, logging.INFO])
@pytest.mark.parametrize("use_callback", [True, False])
def test_handler(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    logging_level: int,
    use_callback: bool,
):
    """Test handler behavior with varying configuration."""
    topic = "ntfy_lite handler test"
    record = logging.LogRecord("test record", logging_level, "", -1, "record message", None, None)

    _callback_called = [False]

    def _callback(e: Exception) -> None:
        _callback_called[0] = True

    callback = _callback if use_callback else None
    logging.raiseExceptions = False

    with tempfile.TemporaryDirectory() as tmp:
        level2tags: dict[ntfy.LoggingLevel, tuple[str, ...]] = {
            logging.ERROR: ("broken_heart",),
        }

        level2priority: dict[ntfy.LoggingLevel, ntfy.Priority] = {
            logging.CRITICAL: ntfy.Priority.MAX,
            logging.ERROR: ntfy.Priority.HIGH,
            logging.WARNING: ntfy.Priority.HIGH,
            logging.INFO: ntfy.Priority.DEFAULT,
            logging.DEBUG: ntfy.Priority.LOW,
            logging.NOTSET: ntfy.Priority.MIN,
        }

        handler = ntfy.NtfyHandler(
            topic,
            error_callback=callback,
            level2tags=level2tags,
            level2priority=level2priority,
        )
        handler.emit(record)

    if not use_callback:
        assert not _callback_called[0]


def test_rate_limit_buffering_and_logging(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """Test that HTTP 429 triggers buffering and logs via standard logging."""

    # --- Classes ---
    class MockResponse:
        ok = False
        status_code = 429
        reason = "Too Many Requests"

    class ListHandler(logging.Handler):
        def emit(
            self,
            record: logging.LogRecord,
        ) -> None:
            logs.append(self.format(record))

    # --- Functions ---
    def mock_put(*args: typing.Any, **kwargs) -> MockResponse:
        return MockResponse()

    # --- Variables ---
    monkeypatch.setattr("requests.Session.put", mock_put)

    logs = []
    test_handler = ListHandler()
    # Get the named logger from ntfy_lite.ntfy
    from ntfy_lite.ntfy import logger as ntfy_logger

    ntfy_logger.addHandler(test_handler)
    original_level = ntfy_logger.level
    ntfy_logger.setLevel(logging.DEBUG)

    topic = "ntfy_test_rate_limit"
    title = "Test 429"
    message = "Rate limit test message"

    db_path = tmp_path / "ntfy_buffer.sqlite"
    buffer = NtfyBuffer(db_path)

    # --- Script ---
    ntfy.push(
        topic,
        title,
        message=message,
        dry_run=ntfy.DryRun.off,
        buffer=buffer,
    )

    ntfy_logger.removeHandler(test_handler)
    ntfy_logger.setLevel(original_level)
    assert any("NTFY rate limit exceeded (HTTP 429)" in log for log in logs), "Expected rate limit warning in logs."

    # Verify that the SQLite buffer has been updated
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, topic FROM buffer WHERE topic = ?", (topic,))
        rows = cursor.fetchall()
        assert len(rows) > 0, "Expected buffered message in SQLite database."
        # Clean up
        conn.execute("DELETE FROM buffer WHERE topic = ?", (topic,))


def test_handler_default_db_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from pathlib import Path

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    # Ensure environment is clear
    monkeypatch.delenv("NTFY_LITE_DISABLE_BUFFER", raising=False)

    handler = ntfy.NtfyHandler("test_topic", twice_in_a_row=False)
    assert handler._buffer is not None
    assert handler._buffer.db_path == home_dir / ".ntify" / "ntfy_buffer.sqlite"


def test_handler_disable_db_path_arg(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("NTFY_LITE_DISABLE_BUFFER", raising=False)
    handler = ntfy.NtfyHandler("test_topic", db_path=False)
    assert handler._buffer is None


def test_handler_disable_db_path_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NTFY_LITE_DISABLE_BUFFER", "1")
    handler = ntfy.NtfyHandler("test_topic")
    assert handler._buffer is None


def test_long_message_truncation_no_attachment(
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that a long message is truncated and no attachment is sent."""

    class MockResponse:
        ok = True
        status_code = 200
        reason = "OK"

    call_args = []

    def mock_put(*args: typing.Any, **kwargs: typing.Any) -> MockResponse:
        data = kwargs.get("data")
        if data is not None and hasattr(data, "read"):
            kwargs["data"] = data.read().decode("utf-8")
        call_args.append((args, kwargs))
        return MockResponse()

    monkeypatch.setattr("requests.Session.put", mock_put)

    topic = "ntfy_test_long_message"
    title = "Test long message"
    long_msg = "A" * 4500

    ntfy.push(
        topic,
        title,
        message=long_msg,
        dry_run=ntfy.DryRun.off,
    )

    assert len(call_args) == 1
    _, kwargs = call_args[0]
    headers = kwargs["headers"]
    data = kwargs["data"]

    # Since we are using TruncationFormatter by default, the truncated text
    # is placed in the HTTP body (data) instead of the Message header.
    assert "Message" not in headers
    assert "[truncated]" in data
    assert len(data) < 4500


def test_data_manager_missing_args():
    from ntfy_lite.ntfy import _DataManager

    with pytest.raises(ValueError, match="must push either a message or a filepath"):
        _DataManager(message=None, filepath=None)


def test_data_manager_invalid_filepath(tmp_path: Path):
    from ntfy_lite.ntfy import _DataManager

    non_existent_file = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError, match="failed to find file to attach"):
        _DataManager(message=None, filepath=non_existent_file)
