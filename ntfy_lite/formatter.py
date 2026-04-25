"""Message formatter in case the message is too large."""

# %%
####################
# Import Statement #
####################
import abc
import io
import sys
import typing
from dataclasses import dataclass

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


###########
# CLASSES #
###########
@dataclass
class FormatterPayload:
    """Holds the resulting payload, headers, and files to cleanup for pushing to ntfy.

    Attributes
    ----------
    - data: typing.IO | str (The HTTP body)
    - message_header: str | None (The Message HTTP header)
    - filename_header: str | None (The Filename HTTP header)
    - file_to_close: typing.IO | None (File handle to close after send)
    - temp_file_path: str | None (Temporary file to delete after send)
    """

    data: typing.IO[typing.Any] | str
    message_header: str | None = None
    filename_header: str | None = None
    file_to_close: typing.IO[typing.Any] | None = None
    temp_file_path: str | None = None

    def get(
        self: Self,
        key: typing.Any,
        default: typing.Any = None,
    ) -> typing.Any:
        """Retrieve one of the defined fields from the dictionnary."""
        return getattr(self, key, default)

    def __getitem__(
        self: Self,
        key: typing.Any,
    ) -> typing.Any:
        """Enable dataclass to be subscriptable."""
        return getattr(self, key, None)

    def __setitem__(
        self: Self,
        key: typing.Any,
        value: typing.Any = None,
    ) -> None:
        """Enable dataclass to be subscriptable."""
        setattr(self, key, value)


class Formatter(abc.ABC):
    """Base class for handling how messages are formatted and processed for ntfy."""

    def __init__(
        self: Self,
        max_length: int = 4000,
        truncation_message: str = "\n... [truncated] ...\n",
    ) -> None:
        self.max_length = max_length
        self.truncation_message = truncation_message

    def _default_payload(self: Self) -> FormatterPayload:
        return FormatterPayload(data="")

    @abc.abstractmethod
    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        """Process the message string and return properties for the DataPayload.

        Parameters
        ----------
        message : str
            The message string to be formatted and processed.

        Returns
        -------
        FormatterPayload
            A dataclass containing the formatted payload and associated files.
        """


class TemplateFormatter(Formatter):
    """Template-based format handler.

    Handles character limits by intelligently cutting the middle of the text out
    and substituting the result into a user-defined template string.
    """

    def __init__(
        self: Self,
        max_length: int = 4000,
        truncation_message: str = "\n... [truncated] ...\n",
        template: str = "{head}{truncation_message}{tail}",
    ) -> None:
        r"""Initialize TemplateFormatter.

        Parameters
        ----------
        max_length : int, optional
            The maximum allowed length of the message body, by default 4000.
        truncation_message : str, optional
            The note added to indicate truncation, by default "\n... [truncated] ...\n".
        template : str, optional
            The format string determining how the final message is constructed.
            Must contain `{head}`, `{truncation_message}`, and `{tail}` placeholders,
            by default "{head}{truncation_message}{tail}".
        """
        super().__init__(max_length, truncation_message)
        self.template = template

    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        msg_bytes = message.encode("utf-8")
        result = self._default_payload()

        if len(msg_bytes) > self.max_length:
            # Estimate how much space the template adds (excluding the placeholders)
            template_static_len = len(
                self.template.format(head="", truncation_message=self.truncation_message, tail="")
            )

            available_length = self.max_length - template_static_len

            if available_length <= 0:
                truncated_str = self.template.format(head="", truncation_message=self.truncation_message, tail="")
            else:
                head_len = available_length // 2
                bias = 50 if available_length > 100 else 0
                head_len -= bias
                tail_len = available_length - head_len

                head = msg_bytes[:head_len].decode("utf-8", "ignore")
                tail = msg_bytes[-tail_len:].decode("utf-8", "ignore")

                truncated_str = self.template.format(
                    head=head,
                    truncation_message=self.truncation_message,
                    tail=tail,
                )

            # In case the resulting string with replaced characters exceeds max_length slightly,
            # we ensure it gets sent directly as an HTTP body by relying on the latin-1 encoding
            result["data"] = truncated_str.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")
        else:
            result["data"] = message.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")

        return result


class AttachmentFormatter(Formatter):
    """Formatter of the attachment text.

    If the text exceeds a given limit, ntfy converts the whole thing to an attachment.
    We bypass this by intentionally truncating the text and generating our own attachment.
    """

    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        msg_bytes = message.encode("utf-8")
        result = self._default_payload()

        if len(msg_bytes) > self.max_length:
            trunc_msg_bytes = self.truncation_message.encode("utf-8")
            available_length = self.max_length - len(trunc_msg_bytes)

            if available_length <= 0:
                truncated_str = self.truncation_message
            else:
                head_len = available_length // 4
                tail_len = available_length - head_len
                # 1. Truncate the text message to keep the most relevant parts (the start and end).
                truncated_str = (
                    f"{msg_bytes[:head_len].decode('utf-8', 'ignore')}"
                    f"{self.truncation_message}"
                    f"{msg_bytes[-tail_len:].decode('utf-8', 'ignore')}"
                )
            result["message_header"] = truncated_str

            # 2. Provide the complete, un-truncated string in a file-like object.
            tf = io.BytesIO(msg_bytes)

            # 3. Queue the file-like object to be uploaded in the HTTP body.
            result["file_to_close"] = tf
            result["temp_file_path"] = None
            result["data"] = tf
            result["filename_header"] = "traceback.txt"
        else:
            # The message fits within limits, we can send it directly as the HTTP body.
            result["data"] = message.encode(encoding="latin-1", errors="replace").decode(encoding="latin-1")

        return result


class EmptyFormatter(Formatter):
    """Empty format handler.

    Drops the message body entirely if it exceeds the limit and only returns
    the truncation note, safely avoiding ntfy's attachment mechanism.
    """

    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        msg_bytes = message.encode("utf-8")
        result = self._default_payload()

        if len(msg_bytes) > self.max_length:
            result["data"] = self.truncation_message.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")
        else:
            result["data"] = message.encode(
                encoding="latin-1",
                errors="replace",
            ).decode(encoding="latin-1")

        return result


class TruncationFormatter(Formatter):
    """Character limit handler.

    Handles character limits by intelligently cutting the middle of the text out
    and leaving a 'truncated' note, avoiding ntfy's attachment mechanism entirely.
    """

    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        msg_bytes = message.encode("utf-8")
        result = self._default_payload()

        if len(msg_bytes) > self.max_length:
            trunc_msg_bytes = self.truncation_message.encode("utf-8")
            available_length = self.max_length - len(trunc_msg_bytes)

            if available_length <= 0:
                truncated_str = self.truncation_message
            else:
                # Truncate the text message to keep the most relevant parts (the start and end)
                # keeping it safely under max_length bytes.
                head_len = available_length // 2
                # Ensure head_len doesn't go negative if we applied the -50 bias, so adjust bias conditionally
                bias = 50 if available_length > 100 else 0
                head_len -= bias
                tail_len = available_length - head_len

                truncated_str = (
                    f"{msg_bytes[:head_len].decode('utf-8', 'ignore')}"
                    f"{self.truncation_message}"
                    f"{msg_bytes[-tail_len:].decode('utf-8', 'ignore')}"
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
