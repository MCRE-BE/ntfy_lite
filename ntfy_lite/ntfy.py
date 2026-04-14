"""Module defining the push method, which send a message or the content of a file to an NTFY channel."""

####################
# IMPORT STATEMENT #
####################
"""Module defining the push method, which send a message or the content of a file to an NTFY channel."""

####################
# IMPORT STATEMENT #
####################
import base64
import collections.abc
import contextlib
import logging
import os
import sys
import traceback
import typing
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import requests

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

try:
    from .buffer import NtfyBuffer
except ImportError:
    NtfyBuffer: typing.TypeAlias = typing.Any

from .actions import Action
from .config import Priority
from .error import NtfyError
from .formatter import AttachmentFormatter, Formatter
from .utils import validate_url

logger = logging.getLogger("ntfy_lite")


###########
# CLASSES #
###########
# Use a shared Session object to enable urllib3 connection pooling.
# This significantly reduces latency (by skipping repeated TLS handshakes)
# when pushing multiple notifications to the same ntfy server host.
_session = requests.Session()


@dataclass
class _DataPayload:
    """Holds the resulting payload and headers for pushing to ntfy."""

    data: typing.IO[typing.Any] | str
    message_header: str | None = None
    filename_header: str | None = None


class _DataManager:
    """The data manager.

    The payload pushed to ntfy can be a message, a file, or both simultaneously.
    When pushing both, ntfy receives the file in the HTTP body and the text in the `Message` HTTP header.

    If the text message is very long (e.g., a traceback), ntfy will normally reject it or
    auto-convert it to an attachment without a text preview. To prevent this, this manager
    uses a Formatter to process the message and handle truncation or attachment logic.
    """

    def __init__(
        self: Self,
        message: typing.Any | None,
        filepath: Path | None,
        formatter: Formatter | None = None,
    ) -> None:
        if message is None and filepath is None:
            raise ValueError("must push either a message or a filepath (no message nor filepath argument specified)")

        if filepath is not None and not filepath.is_file():
            raise FileNotFoundError(f"failed to find file to attach ({filepath})")

        self._file_to_close: typing.IO[typing.Any] | None = None
        self._temp_file_path: str | None = None
        self._payload = _DataPayload(data="")

        # Format any non-string objects (like Exceptions) into a readable traceback string
        if message is not None and not isinstance(message, str):
            message = "".join(traceback.TracebackException.from_exception(message).format())

        if filepath is not None:
            # If a file is explicitly provided by the user, we upload it as the HTTP body.
            self._file_to_close = open(filepath, "rb")  # noqa: SIM115
            self._payload.data = self._file_to_close
            if message is not None:
                # The text message must be placed in the HTTP header since the body is occupied.
                self._payload.message_header = message
        elif message is not None:
            if formatter is None:
                formatter = AttachmentFormatter()

            fmt_result = formatter.process(message)
            self._payload.data = fmt_result.get("data", "")
            self._payload.message_header = fmt_result.get("message_header")
            self._payload.filename_header = fmt_result.get("filename_header")
            self._file_to_close = fmt_result.get("file_to_close")
            self._temp_file_path = fmt_result.get("temp_file_path")

    def __enter__(self: Self) -> _DataPayload:
        return self._payload

    def __exit__(
        self: Self,
        _,
        __,
        ___,
    ) -> None:
        # Cleanup any opened file handles or temporary files after the request has been sent.
        if self._file_to_close is not None:
            self._file_to_close.close()
        if self._temp_file_path is not None:
            with contextlib.suppress(OSError):
                os.remove(self._temp_file_path)


class DryRun(Enum):
    """
    An optional value of DryRun may be passed as an argument to the [ntfy_lite.ntfy.push][] function.

    - If 'off' is passed (default), then the [ntfy_lite.ntfy.push][] function will publish to ntfy.

    - If 'on' is passed, then the [ntfy_lite.ntfy.push][] function will *not* publish to ntfy.

    - If 'error' is passed, then the [ntfy_lite.ntfy.push][] function will raise an [ntfy_lite.error.NtfyError][].

    This is meant for testing.
    """

    on = auto()
    off = auto()
    error = auto()


def _buffer_429(
    topic: str,
    url: str | None,
    data: typing.IO[typing.Any] | str,
    headers: dict[str, str],
    buffer: typing.Any | None,
) -> bool:
    """Helper to handle HTTP 429 buffering logic."""
    if buffer is None:
        return False

    logger.warning(f"NTFY rate limit exceeded (HTTP 429) for '{topic}'. Buffering message.")
    data_str = data if isinstance(data, str) else "Original file attachment was not buffered due to HTTP 429."
    buffer.add(topic, str(url), data_str, headers)
    return True


def push(  # noqa: C901, PLR0912
    topic: str,
    title: str,
    message: typing.Any | None = None,
    priority: Priority = Priority.DEFAULT,
    tags: str | collections.abc.Iterable[str] | None = None,
    click: str | None = None,
    email: str | None = None,
    filepath: Path | None = None,
    attach: str | None = None,
    icon: str | None = None,
    actions: Action | collections.abc.Sequence[Action] = (),
    at: str | None = None,
    url: str | None = "https://ntfy.sh",
    dry_run: DryRun = DryRun.off,
    buffer: typing.Any | None = None,
    formatter: Formatter | None = None,
) -> None:
    """Pushes a notification.

    ```python
    # basic usage
    import ntfy_lite as ntfy

    ntfy.push(
        "my topic", priority=ntfy.Priority.DEFAULT, message="my message"
    )
    ```

    For more documentation of all arguments, visit:
    [https://ntfy.sh/docs/publish/](https://ntfy.sh/docs/publish/)

    Args:
    topic: the ntfy topic on which to publish
    title: the title of the notification
    message: the message. It is optional and if None, then a filepath argument must be provided instead.
    priority: the priority of the notification
    tags (i.e. emojis): either a string (a single tag) or a list of string (several tags). see [supported emojis](https://docs.ntfy.sh)
    click: URL link to be included in the notification
    email: address to which the notification should also be sent
    filepath: path to the file to be sent as attachement.
        It is optional and if None, then a message argument must be provided instead.
    icon: URL to an icon to include in the notification
    actions: An action is either a [ntfy_lite.actions.ViewAction][]
        (i.e. a link to a website) or a [ntfy_lite.actions.HttpAction][]
        (i.e. sending of a HTTP GET, POST or PUT request to a website)
    at: to be used for delayed notification, see [scheduled delivery](https://ntfy.sh/docs/publish/#scheduled-delivery)
    url: ntfy server
    dry_run: for testing purposes, see [ntfy_lite.ntfy.DryRun][]
    formatter: define how large payloads are formatted (e.g. TruncationFormatter or AttachmentFormatter)
    """

    # the message manager handles files and long messages,
    # ensuring files are closed after sending.
    with _DataManager(message, filepath, formatter) as payload:
        # checking that arguments that are expected to be
        # urls are urls
        urls = {"click": click, "attach": attach, "icon": icon}
        for attr, value in urls.items():
            # throw value error if not None
            # and not a url
            validate_url(attr, value)

        # some argument can be directly set in the
        # headers dict
        direct_mapping: dict[str, typing.Any] = {
            "Title": title,
            "At": at,
            "Click": click,
            "Email": email,
            "Icon": icon,
        }
        headers = {key: value for key, value in direct_mapping.items() if value}

        if payload.message_header is not None:
            # use RFC 2047 base64 encoding to support newlines and utf-8 securely
            b64 = base64.b64encode(payload.message_header.encode("utf-8")).decode("ascii")
            headers["Message"] = f"=?UTF-8?B?{b64}?="

        if payload.filename_header is not None:
            headers["Filename"] = payload.filename_header

        # adding priority
        headers["Priority"] = priority.value

        # adding tags
        if tags:
            if isinstance(tags, str):
                tags = (tags,)
            headers["Tags"] = ",".join([str(t) for t in tags])

        # adding actions
        if actions:
            if isinstance(actions, Action):
                actions = [actions]
            headers["Actions"] = "; ".join([str(action) for action in actions])

        # sending
        if dry_run == DryRun.off:
            response = _session.put(
                f"{url}/{topic}",
                data=payload.data,
                headers=headers,
                timeout=10,
            )
            if not response.ok:
                # If HTTP 429, don't block the thread; buffer it asynchronously
                if int(response.status_code) == 429:
                    if _buffer_429(topic, url, payload.data, headers, buffer):
                        return
                    raise NtfyError(response.status_code, response.reason)

                # Normal error, raise
                raise NtfyError(response.status_code, response.reason)
        elif dry_run == DryRun.error:
            if getattr(
                requests,
                "_SIMULATE_429",
                False,
            ) and _buffer_429(
                topic,
                url,
                payload.data,
                headers,
                buffer,
            ):
                return
            raise NtfyError(-1, "DryRun.error passed as argument")
