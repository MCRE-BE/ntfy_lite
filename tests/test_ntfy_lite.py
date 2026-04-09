# ruff: noqa: ANN201, S101, ARG001, PLW0603, PT011
"""Tests."""

####################
# IMPORT STATEMENT #
####################
import logging
import sqlite3
import tempfile
import typing
from pathlib import Path

import ntfy_lite as ntfy
import pytest
from ntfy_lite.buffer import NtfyBuffer


####################
# INDIVIDUAL TESTS #
####################
def test_minimal_message_push():
    """Test a minimal push with only a topic, title, and message."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    ntfy.push(topic, title, message=message, dry_run=True)


def test_minimal_filepath_push():
    """Test a minimal push with a filepath."""

    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"

    with tempfile.TemporaryDirectory() as tmp:
        filepath = Path(tmp) / "test.txt"
        with open(filepath, "w") as f:
            f.write("test content")

        ntfy.push(topic, title, filepath=filepath, dry_run=True)


def test_tags_push():
    """Test a push with tags."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    tags = ["heart", "rainbow"]
    ntfy.push(topic, title, tags=tags, message=message, dry_run=True)


def test_click_push():
    """Test a push with a clickable URL."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    click = "https://is.mpg.de"
    ntfy.push(topic, title, click=click, message=message, dry_run=True)


def test_click_no_url_push():
    """Test a push with an invalid URL for click."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    click = "this is not an url"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, click=click, message=message, dry_run=True)


def test_email_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    email = "camembert@fromage.fr"
    ntfy.push(topic, title, email=email, message=message, dry_run=True)


def test_icon_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    icon = "https://styles.redditmedia.com/t5_32uhe/styles/communityIcon_xnt6chtnr2j21.png"
    ntfy.push(topic, title, icon=icon, message=message, dry_run=True)


def test_icon_not_url_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    icon = "not an url to an icon"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, icon=icon, message=message, dry_run=True)


def test_attach_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    attach = "https://ntfy.sh/flowers"
    ntfy.push(topic, title, attach=attach, message=message, dry_run=True)


def test_attach_not_an_url_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    attach = "not an url to an image"
    with pytest.raises(ValueError):
        ntfy.push(topic, title, attach=attach, message=message, dry_run=True)


@pytest.mark.parametrize("clear", [True, False])
def test_action_view_push(clear):
    """Test ViewAction with clear flag."""
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    ntfy.push(topic, title, message=message, actions=action, dry_run=True)


@pytest.mark.parametrize("clear", [True, False])
def test_actions_view_push(clear):
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    action1 = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    action2 = ntfy.ViewAction("ntfy_lite view action", "https://is.mpg.de", clear=clear)
    ntfy.push(topic, title, message=message, actions=[action1, action2], dry_run=True)


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
    ntfy.push(topic, title, message=message, actions=action, dry_run=True)


def test_extended_ascii_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test extended ascii push"
    message = "ntfy_extended_ascii_push message: (°_°)"
    ntfy.push(topic, title, message=message, dry_run=True)


def test_unicode_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test unicode push"
    message = "ntfy unicode push message: 🐋💐🪂"
    ntfy.push(topic, title, message=message, dry_run=True)


@pytest.mark.parametrize("clear", [True, False])
def test_actions_view_http_push(clear):
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
    ntfy.push(topic, title, message=message, actions=[action1, action2], dry_run=True)


def test_at_push():
    topic = "ntfy_lite_test"
    title = "ntfy lite test mimimal push"
    message = "ntfy lite test mimimal push: message"
    at = "1 minute"
    ntfy.push(topic, title, at=at, message=message, dry_run=True)


# required for mypy
_callback_called: bool


################
# COMPLEX TEST #
################
@pytest.mark.parametrize("twice_in_a_row", [True, False])
@pytest.mark.parametrize("logging_level", [logging.ERROR, logging.INFO])
@pytest.mark.parametrize("use_callback", [True, False])
@pytest.mark.parametrize("dry_run", [ntfy.DryRun.on, ntfy.DryRun.error])
def test_handler(
    twice_in_a_row: bool,
    logging_level: ntfy.LoggingLevel,
    use_callback: bool,
    dry_run: ntfy.DryRun,
):
    """Test handler behavior with varying configuration."""
    topic = "ntfy_lite handler test"
    record = logging.LogRecord("test record", logging_level, "", -1, "record message", None, None)

    global _callback_called
    _callback_called = False

    def _callback(e: Exception) -> None:
        global _callback_called
        _callback_called = True

    callback = _callback if use_callback else None
    logging.raiseExceptions = False

    with tempfile.TemporaryDirectory() as tmp:
        filepath = Path(tmp) / "test.txt"
        with open(filepath, "w") as f:
            f.write("test content")

        level2tags: typing.Dict[ntfy.LoggingLevel, tuple[str, ...]] = {
            logging.ERROR: ("broken_heart",),
        }

        level2priority: typing.Dict[ntfy.LoggingLevel, ntfy.Priority] = {
            logging.CRITICAL: ntfy.Priority.MAX,
            logging.ERROR: ntfy.Priority.HIGH,
            logging.WARNING: ntfy.Priority.HIGH,
            logging.INFO: ntfy.Priority.DEFAULT,
            logging.DEBUG: ntfy.Priority.LOW,
            logging.NOTSET: ntfy.Priority.MIN,
        }

        level2filepath: typing.Dict[ntfy.LoggingLevel, Path] = {
            logging.ERROR: filepath,
        }

        level2email: typing.Dict[ntfy.LoggingLevel, str] = {
            logging.ERROR: "mimolette@fromage.fr",
        }

        handler = ntfy.NtfyHandler(
            topic,
            twice_in_a_row=twice_in_a_row,
            error_callback=callback,
            level2tags=level2tags,
            level2filepath=level2filepath,
            level2priority=level2priority,
            level2email=level2email,
            dry_run=dry_run,
        )
        handler.emit(record)

    if not use_callback:
        assert not _callback_called
    elif dry_run in (ntfy.DryRun.on, ntfy.DryRun.error):
        assert _callback_called


def test_rate_limit_buffering_and_logging(monkeypatch, tmp_path):
    """Test that HTTP 429 triggers buffering and logs via loguru."""

    # --- Classes ---
    class MockResponse:
        ok = False
        status_code = 429
        reason = "Too Many Requests"

    class ListHandler(logging.Handler):
        def emit(self, record) -> None:
            logs.append(self.format(record))

    # --- Functions ---
    def mock_put(*args, **kwargs) -> MockResponse:
        return MockResponse()

    # --- Variables ---
    monkeypatch.setattr("requests.put", mock_put)

    logs = []
    test_handler = ListHandler()
    logger = logging.getLogger()
    logger.addHandler(test_handler)

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

    logger.removeHandler(test_handler)
    assert any("NTFY rate limit exceeded (HTTP 429)" in log for log in logs), "Expected rate limit warning in logs."

    # Verify that the SQLite buffer has been updated
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, topic FROM buffer WHERE topic = ?", (topic,))
        rows = cursor.fetchall()
        assert len(rows) > 0, "Expected buffered message in SQLite database."
        # Clean up
        conn.execute("DELETE FROM buffer WHERE topic = ?", (topic,))

def test_handler_default_db_path(monkeypatch, tmp_path):
    import os
    from pathlib import Path

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    # Ensure environment is clear
    monkeypatch.delenv("NTFY_LITE_DISABLE_BUFFER", raising=False)

    handler = ntfy.NtfyHandler("test_topic", twice_in_a_row=False)
    assert handler._buffer is not None
    assert handler._buffer.db_path == home_dir / ".ntify" / "ntfy_buffer.sqlite"

def test_handler_disable_db_path_arg(monkeypatch):
    monkeypatch.delenv("NTFY_LITE_DISABLE_BUFFER", raising=False)
    handler = ntfy.NtfyHandler("test_topic", db_path=False)
    assert handler._buffer is None

def test_handler_disable_db_path_env(monkeypatch):
    monkeypatch.setenv("NTFY_LITE_DISABLE_BUFFER", "1")
    handler = ntfy.NtfyHandler("test_topic")
    assert handler._buffer is None
