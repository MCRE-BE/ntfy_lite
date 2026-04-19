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
        """Process the message string and return properties for the DataPayload.

        Parameters
        ----------
        message : str
            The message string to be formatted and processed.

        Returns
        -------
        dict[str, typing.Any]
            A dictionary that can include:
            - data: typing.IO | str (The HTTP body)
            - message_header: str | None (The Message HTTP header)
            - filename_header: str | None (The Filename HTTP header)
            - file_to_close: typing.IO | None (File handle to close after send)
            - temp_file_path: str | None (Temporary file to delete after send)
        """


class AttachmentFormatter(Formatter):
    """Formatter of the attachment text.

    If the text exceeds a maximum length, ntfy converts the whole thing to an attachment.
    We bypass this by intentionally truncating the text and generating our own attachment.
    """

    def __init__(
        self: Self,
        max_length: int = 4000,
        truncation_message: str = "\n... [truncated] ...\n",
    ) -> None:
        self.max_length = max_length
        self.truncation_message = truncation_message

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

        if len(msg_bytes) > self.max_length:
            # 1. Truncate the text message to keep the most relevant parts (the start and end).
            # Reserve 1000 for start (if enough space) or 1/4 of total.
            start_len = min(1000, max(0, self.max_length // 4))
            # Reserve space for the truncation message, the rest for the end.
            trunc_len = len(self.truncation_message.encode("utf-8"))
            end_len = max(0, self.max_length - start_len - trunc_len)

            truncated_str = (
                (
                    msg_bytes[:start_len].decode("utf-8", "ignore")
                    + self.truncation_message
                    + msg_bytes[-end_len:].decode("utf-8", "ignore")
                )
                if start_len + trunc_len < self.max_length
                else self.truncation_message
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

    def __init__(
        self: Self,
        max_length: int = 4000,
        truncation_message: str = "\n... [truncated] ...\n",
    ) -> None:
        self.max_length = max_length
        self.truncation_message = truncation_message

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

        if len(msg_bytes) > self.max_length:
            # Truncate the text message to keep the most relevant parts (the start and end)
            # keeping it safely under max_length bytes.
            start_len = max(0, (self.max_length - len(self.truncation_message.encode("utf-8"))) // 2)
            end_len = max(0, self.max_length - len(self.truncation_message.encode("utf-8")) - start_len)

            truncated_str = (
                (
                    msg_bytes[:start_len].decode("utf-8", "ignore")
                    + self.truncation_message
                    + msg_bytes[-end_len:].decode("utf-8", "ignore")
                )
                if start_len > 0
                else self.truncation_message
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
