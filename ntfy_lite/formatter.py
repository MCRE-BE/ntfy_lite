# ruff: noqa: SIM115
"""Message formatter in case the message is too large."""

# %%
####################
# Import Statement #
####################
import abc
import sys
import tempfile
import typing

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


###########
# CLASSES #
###########
class Formatter(abc.ABC):
    """Base class for handling how messages are formatted and processed for ntfy."""

    @abc.abstractmethod
    def process(
        self: Self,
        message: str,
    ) -> dict[str, typing.Any]:
        """Process the message string and return a dictionary of propertiesto be applied to the DataPayload.

        Must return a dict that can include:
        - data: typing.Union[typing.IO, str] (The HTTP body)
        - message_header: str | None (The Message HTTP header)
        - filename_header: str | None (The Filename HTTP header)
        - file_to_close: typing.IO | None (File handle to close after send)
        - temp_file_path: str | None (Temporary file to delete after send)
        """


class AttachmentFormatter(Formatter):
    """Formatter of the attachment text.

    If the text exceeds 4000 bytes, ntfy converts the whole thing to an attachment.
    We bypass this by intentionally truncating the text and generating our own attachment.
    """

    def process(
        self: Self,
        message: str,
    ) -> dict[str, typing.Any]:
        msg_bytes = message.encode("utf-8")
        result: dict[str, typing.Any] = {
            "message_header": None,
            "filename_header": None,
            "file_to_close": None,
            "temp_file_path": None,
            "data": "",
        }

        if len(msg_bytes) > 4000:
            # 1. Truncate the text message to keep the most relevant parts (the start and end).
            truncated_str = (
                msg_bytes[:1000].decode("utf-8", "ignore")
                + "\n... [truncated] ...\n"
                + msg_bytes[-2900:].decode("utf-8", "ignore")
            )
            result["message_header"] = truncated_str

            # 2. Write the complete, un-truncated string to a temporary file.
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", prefix="traceback_")
            tf.write(msg_bytes)
            tf.flush()
            tf.seek(0)

            # 3. Queue the temporary file to be uploaded in the HTTP body.
            result["file_to_close"] = tf
            result["temp_file_path"] = tf.name
            result["data"] = tf
            result["filename_header"] = "traceback.txt"
        else:
            # The message fits within limits, we can send it directly as the HTTP body.
            result["data"] = message.encode(encoding="latin-1", errors="replace").decode(encoding="latin-1")

        return result


class TruncationFormatter(Formatter):
    """Character limit handler.

    Handles character limits by intelligently cutting the middle of the text out
    and leaving a 'truncated' note, avoiding ntfy's attachment mechanism entirely.
    """

    def process(
        self: Self,
        message: str,
    ) -> dict[str, typing.Any]:
        msg_bytes = message.encode("utf-8")
        result: dict[str, typing.Any] = {
            "message_header": None,
            "filename_header": None,
            "file_to_close": None,
            "temp_file_path": None,
            "data": "",
        }

        if len(msg_bytes) > 4000:
            # Truncate the text message to keep the most relevant parts (the start and end)
            # keeping it safely under 4000 bytes.
            truncated_str = (
                msg_bytes[:1800].decode("utf-8", "ignore")
                + "\n... [truncated] ...\n"
                + msg_bytes[-2100:].decode("utf-8", "ignore")
            )
            # Send the safely truncated string directly as the HTTP body
            result["data"] = truncated_str.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")
        else:
            # The message fits within limits, we can send it directly as the HTTP body.
            result["data"] = message.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")

        return result
