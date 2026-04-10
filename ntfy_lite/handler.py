"""
Module defining the NtfyHandler class.

The NtfyHandler is a logging handler, i.e. an handler suitable for the
[python logging package](https://docs.python.org/3/library/logging.html)

``` python
# Basic usage

import logging
import ntfy_lite as ntfy

ntfy_handler = ntfy.NtfyHandler("my_topic")

logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s | %(name)s |  %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
        handlers=(ntfy_handler,),
)
```

"""

####################
# Import Statement #
####################
import logging
import os
import typing
import warnings
from pathlib import Path

try:
    from .buffer import NtfyBuffer

    _HAS_BUFFER = True
except ImportError:
    _HAS_BUFFER = False

from .defaults import level2tags
from .ntfy import DryRun, push
from .ntfy2logging import LoggingLevel, Priority, level2priority


###########
# CLASSES #
###########
class NtfyHandler(logging.Handler):
    """Subclass of [logging.Handler](https://docs.python.org/3/library/logging.html#handler-objects) that pushes ntfy notifications.

    The notification title will be the record name, and the
    notification message will be either the record message or a
    file attachment (depending on the level2filepath argument).
    """

    def __init__(
        self,
        topic: str,
        url: str = "https://ntfy.sh",
        twice_in_a_row: bool = True,
        error_callback: typing.Callable[[Exception], typing.Any] | None = None,
        level2tags: dict[LoggingLevel, tuple[str, ...]] = level2tags,
        level2priority: dict[LoggingLevel, Priority] = level2priority,
        level2filepath: dict[LoggingLevel, Path] | None = None,
        level2email: dict[LoggingLevel, str] | None = None,
        dry_run: DryRun = DryRun.off,
        db_path: Path | str | bool | None = None,
    ):
        """Start.

        Args:
          topic: Topic on which the notifications will be pushed.
          url: https://ntfy.sh by default.
          twice_in_a_row: If False, if several similar records (similar: same name
            and same message) are emitted, only the first one will result in notification
            being pushed (to avoid the channel to reach the accepted limits of notifications).
          error_callback: It will be called if a NtfyError is raised when pushing a notification.
          level2tags: mapping between logging level and tags to be associated with the notification
          level2priority: mapping between the logging level and the notification priority.
          level2filepath: If for the logging level of the record a corresponding filepath is set,
            the notification will contain no message but a correspondinf file attachment
            (be aware of the size limits, see https://ntfy.sh/docs/publish/#attach-local-file).
          level2email: If an email address is specified for the logging level of the record,
            the ntfy notification will also request a mail to be sent.
          dry_run: For testing. If 'on', no notification will be sent. If 'error', no notification will be sent,
            instead a NtfyError are raised.
        """

        # ... checks ...
        level2filepath = {} if level2filepath is None else level2filepath
        level2email = {} if level2email is None else level2email

        # ... Init ...
        super().__init__()
        self._url = url
        self._topic = topic
        self._last_messages: dict[str, str] | None
        self._last_messages = None if twice_in_a_row else {}
        self._level2tags = level2tags
        self._level2priority = level2priority
        self._level2filepath = level2filepath
        self._level2email = level2email
        self._error_callback = error_callback
        self._dry_run = dry_run
        self._twice_in_a_row = twice_in_a_row

        self._buffer = None

        disable_buffer_env = os.environ.get(
            "NTFY_LITE_DISABLE_BUFFER", "0"
        ).lower() in ("1", "true")

        if db_path is not False and not disable_buffer_env:
            if db_path is None or db_path is True:
                db_path = Path.home() / ".ntify" / "ntfy_buffer.sqlite"
            elif isinstance(db_path, str):
                db_path = Path(db_path)

            if _HAS_BUFFER:
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                self._buffer = NtfyBuffer(db_path)
            else:
                msg = (
                    "Buffering requested (db_path provided or default) but 'pysqlite3' or 'sqlite3' is not available. "
                    "Run 'pip install ntfy_lite[buffer]' to enable this feature. "
                    "Buffering will be disabled."
                )
                warnings.warn(msg, UserWarning)
                logging.info(msg)

        for logging_level in level2priority:
            if logging_level not in self._level2priority:
                raise ValueError(
                    f"NtfyHandler, level2priority argument: missing mapping from "
                    f"logging level {logging_level} to ntfy priority level",
                )

    def _is_new_record(self, record: logging.LogRecord) -> bool:
        if self._last_messages is None:
            return True
        try:
            previous_message = self._last_messages[record.name]
        except KeyError:
            self._last_messages[record.name] = record.msg
            return True
        if record.msg == previous_message:
            return False
        self._last_messages[record.name] = record.msg
        return True

    def emit(self, record: logging.LogRecord) -> None:
        """Push the record as an ntfy message."""

        if self._last_messages and not self._is_new_record(record):
            return
        try:
            filepath = self._level2filepath[record.levelno]
            message = None
        except KeyError:
            filepath = None
            message = record.msg
        try:
            email = self._level2email[record.levelno]
        except KeyError:
            email = None
        try:
            tags = self._level2tags[record.levelno]
        except KeyError:
            tags = ()
        try:
            title = (
                record.extra.get("logger_name")
                if hasattr(record, "extra") is not None
                else record.name
            )
            push(
                topic=self._topic,
                title=title,
                message=message,
                priority=self._level2priority[record.levelno],
                tags=tags,
                email=email,
                filepath=filepath,
                url=self._url,
                dry_run=self._dry_run,
                buffer=self._buffer,
            )
        except Exception as e:
            logging.exception("NTFY Log Handler failed")
            if self._error_callback is not None:
                self._error_callback(e)
            self.handleError(record)
