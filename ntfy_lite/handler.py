"""Module defining the NtfyHandler class.

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
import contextlib
import logging
import os
import sys
import typing
import warnings
from pathlib import Path

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
try:
    from .buffer import NtfyBuffer

    _HAS_BUFFER = True
except ImportError:
    _HAS_BUFFER = False

from .config import Priority, level2priority, level2tags
from .formatter import Formatter
from .ntfy import push


###########
# CLASSES #
###########
class NtfyHandler(logging.Handler):
    """Subclass of [logging.Handler](https://docs.python.org/3/library/logging.html#handler-objects) that pushes ntfy notifications.

    The notification title will be the record name, and the
    notification message will be the formatted log record message.
    """

    def __init__(
        self: Self,
        topic: str,
        url: str = "https://ntfy.sh",
        twice_in_a_row: bool = True,
        error_callback: typing.Callable[[Exception], typing.Any] | None = None,
        level2tags: dict[int, tuple[str, ...]] = level2tags,
        level2priority: dict[int, Priority] = level2priority,
        db_path: Path | str | bool | None = None,
        formatter: Formatter | None = None,
    ):
        """Start.

        Parameters
        ----------
        topic : str
            Topic on which the notifications will be pushed.
        url : str, optional
            https://ntfy.sh by default.
        twice_in_a_row : bool, optional
            If False, if several similar records (similar: same name and same message) are emitted, only the first one will result in notification being pushed (to avoid the channel to reach the accepted limits of notifications).
        error_callback : Callable[[Exception], Any] | None, optional
            It will be called if a NtfyError is raised when pushing a notification.
        level2tags : dict[int, tuple[str, ...]], optional
            mapping between logging level and tags to be associated with the notification
        level2priority : dict[int, Priority], optional
            mapping between the logging level and the notification priority.
        db_path : Path | str | bool | None, optional
            Database path for the buffer.
        formatter : Formatter | None, optional
            Formatter for payloads.
        """

        # ... Init ...
        super().__init__()
        self._url: str = url
        self._topic: str = topic
        self._last_messages: dict[str, str] | None
        self._last_messages = None if twice_in_a_row else {}
        self._level2tags: dict[int, tuple[str, ...]] = level2tags
        self._level2priority: dict[int, Priority] = level2priority
        self._error_callback: typing.Callable[[Exception], typing.Any] | None = error_callback
        self._formatter: Formatter | None = formatter

        self._buffer: typing.Any | None = None

        # ...Activate or deactive NTFY Buffering
        disable_buffer_env = os.environ.get("NTFY_LITE_DISABLE_BUFFER", "0").lower()
        disable_buffer_env = disable_buffer_env in ("1", "true")

        if db_path is not False and not disable_buffer_env:
            if db_path is None or db_path is True:
                db_path = Path.home() / ".ntify" / "ntfy_buffer.sqlite"
            elif isinstance(db_path, str):
                db_path = Path(db_path)

            if _HAS_BUFFER:
                with contextlib.suppress(Exception):
                    db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                self._buffer = NtfyBuffer(db_path)
            else:
                msg = (
                    "Buffering requested (db_path provided or default) but 'pysqlite3' or 'sqlite3' is not available. "
                    "Run 'pip install ntfy_lite[buffer]' to enable this feature. "
                    "Buffering will be disabled."
                )
                warnings.warn(msg, UserWarning, stacklevel=2)
                logging.info(msg)

        # ... Check logging level's
        for logging_level in level2priority:
            if logging_level not in self._level2priority:
                raise ValueError(
                    f"NtfyHandler, level2priority argument: missing mapping from "
                    f"logging level {logging_level} to ntfy priority level",
                )

    def _is_new_record(self, record: logging.LogRecord) -> bool:
        if self._last_messages is None:
            return True
        previous_message = self._last_messages.get(record.name)
        if previous_message is None:
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

        message = self.format(record)
        tags = self._level2tags.get(record.levelno, ())

        try:
            title = record.name
            if hasattr(record, "extra") and isinstance(record.extra, dict) and "logger_name" in record.extra:
                title = str(
                    typing.cast(
                        "dict[str, typing.Any]",
                        record.extra,
                    )["logger_name"]
                )
            push(
                topic=self._topic,
                title=title,
                message=message,
                priority=self._level2priority[record.levelno],
                tags=tags,
                url=self._url,
                buffer=self._buffer,
                formatter=self._formatter,
            )
        except Exception as e:
            logging.exception("NTFY Log Handler failed")
            if self._error_callback is not None:
                self._error_callback(e)
            self.handleError(record)
