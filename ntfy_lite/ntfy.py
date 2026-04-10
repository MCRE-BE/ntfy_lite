"""Module defining the push method, which send a message or the content of a file to an NTFY channel."""

####################
# IMPORT STATEMENT #
####################
import base64
import logging
import tempfile
import traceback
import typing
from enum import Enum, auto
from pathlib import Path

import requests

from .actions import Action

try:
    from .buffer import NtfyBuffer
except ImportError:
    NtfyBuffer = typing.Any
from .error import NtfyError
from .ntfy2logging import Priority
from .utils import validate_url

logger = logging.getLogger("ntfy_lite")


###########
# CLASSES #
###########
# Use a shared Session object to enable urllib3 connection pooling.
# This significantly reduces latency (by skipping repeated TLS handshakes)
# when pushing multiple notifications to the same ntfy server host.
_session = requests.Session()


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
    data: typing.Union[typing.IO, str],
    headers: typing.Dict[str, str],
    buffer: NtfyBuffer | None,
) -> bool:
    """Helper to handle HTTP 429 buffering logic."""
    if buffer is None:
        return False

    logger.warning(
        f"NTFY rate limit exceeded (HTTP 429) for '{topic}'. Buffering message."
    )
    data_str = (
        data
        if isinstance(data, str)
        else "Original file attachment was not buffered due to HTTP 429."
    )
    buffer.add(topic, str(url), data_str, headers)
    return True


def push(
    topic: str,
    title: str,
    message: str | None = None,
    priority: Priority = Priority.DEFAULT,
    tags: typing.Union[str, typing.Iterable[str]] = [],
    click: str | None = None,
    email: str | None = None,
    filepath: Path | None = None,
    attach: str | None = None,
    icon: str | None = None,
    actions: typing.Union[Action, typing.Sequence[Action]] = (),
    at: str | None = None,
    url: str | None = "https://ntfy.sh",
    dry_run: DryRun = DryRun.off,
    buffer: NtfyBuffer | None = None,
) -> None:
    """
    Pushes a notification.

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
    """

    # checking the user is at least pushing a message
    # or a file attachment
    if not any((message, filepath)):
        raise ValueError(
            "must push either a message or a filepath (no message nor filepath argument specified)"
        )

    # checking that arguments that are expected to be urls are urls
    urls = {"click": click, "attach": attach, "icon": icon}
    for attr, value in urls.items():
        validate_url(attr, value)

    headers: typing.Dict[str, str] = {}
    direct_mapping: typing.Dict[str, typing.Any] = {
        "Title": title,
        "At": at,
        "Click": click,
        "Email": email,
        "Icon": icon,
    }
    headers = {key: value for key, value in direct_mapping.items() if value}

    headers["Priority"] = priority.value

    if tags:
        if isinstance(tags, str):
            tags = (tags,)
        headers["Tags"] = ",".join([str(t) for t in tags])

    if actions:
        if isinstance(actions, Action):
            actions = [actions]
        headers["Actions"] = "; ".join([str(action) for action in actions])

    # Convert non-string messages to string (e.g. exception traces)
    if message is not None and not isinstance(message, str):
        message = "".join(traceback.TracebackException.from_exception(message).format())

    data: typing.Union[typing.IO, bytes] = b""
    tmp_file = None

    if filepath is None and message is not None:
        message_bytes = message.encode("utf-8")
        if len(message_bytes) > 2000:
            # Message is too long. Truncate it and attach the full message as a file.
            truncated_msg = (
                message_bytes[:2000].decode("utf-8", errors="ignore")
                + "\n\n[...Truncated. See attachment for full message...]"
            )
            data = truncated_msg.encode("utf-8")

            # Create a temporary file to hold the full message
            tmp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", prefix="ntfy_long_message_"
            )
            tmp_file.write(message_bytes)
            tmp_file.close()

            filepath = Path(tmp_file.name)
        else:
            data = message_bytes

    if filepath is not None:
        if not filepath.is_file():
            raise FileNotFoundError(f"failed to find file to attach ({filepath})")
        data = open(filepath, "rb")
        if message is not None:
            # If we are attaching a user file, but also have a message,
            # put the message in the header. Must be base64 encoded.
            if tmp_file is not None:
                b64_msg = base64.b64encode(truncated_msg.encode("utf-8")).decode(
                    "ascii"
                )
            else:
                b64_msg = base64.b64encode(message.encode("utf-8")).decode("ascii")
            headers["Message"] = f"=?utf-8?B?{b64_msg}?="
            headers["Filename"] = filepath.name

    try:
        if dry_run == DryRun.off:
            response = _session.put(
                f"{url}/{topic}",
                data=data,
                headers=headers,
                timeout=10,
            )
            if not response.ok:
                if int(response.status_code) == 429:
                    if _buffer_429(topic, url, data, headers, buffer):
                        return
                    raise NtfyError(response.status_code, response.reason)
                raise NtfyError(response.status_code, response.reason)
        elif dry_run == DryRun.error:
            if getattr(requests, "_SIMULATE_429", False):
                if _buffer_429(topic, url, data, headers, buffer):
                    return
            raise NtfyError(-1, "DryRun.error passed as argument")
    finally:
        if not isinstance(data, bytes):
            data.close()
        if tmp_file is not None:
            try:
                Path(tmp_file.name).unlink()
            except Exception:
                pass
