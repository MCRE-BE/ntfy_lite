"""Message formatter in case the message is too large."""

# %%
####################
# Import Statement #
####################
import abc
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
                    msg_bytes[:head_len].decode("utf-8", "ignore")
                    + self.truncation_message
                    + msg_bytes[-tail_len:].decode("utf-8", "ignore")
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


class TemplateFormatter(Formatter):
    """Template-based message formatter for when character limits are exceeded.

    Allows you to define exactly what parts of the message are displayed when
    it is truncated by substituting `{head}`, `{truncation_message}`, and `{tail}`
    in a user-defined template string.
    """

    def __init__(
        self: Self,
        template: str = "{head}{truncation_message}{tail}",
        max_length: int = 4000,
        truncation_message: str = "\n... [truncated] ...\n",
    ) -> None:
        super().__init__(max_length, truncation_message)
        self.template = template

    def process(
        self: Self,
        message: str,
    ) -> FormatterPayload:
        msg_bytes = message.encode("utf-8")
        result = self._default_payload()

        if len(msg_bytes) > self.max_length:
            trunc_msg_bytes = self.truncation_message.encode("utf-8")
            template_overhead = len(
                self.template
                .replace("{head}", "")
                .replace("{tail}", "")
                .replace("{truncation_message}", "")
                .encode("utf-8")
            )
            available_length = self.max_length - len(trunc_msg_bytes) - template_overhead

            if available_length <= 0:
                # If we don't even have space for the truncation message, fallback safely
                result["data"] = self.truncation_message.encode("latin-1", "replace").decode("latin-1")
                return result

            # Divide the available length into head and tail portions based on the template
            has_head = "{head}" in self.template
            has_tail = "{tail}" in self.template

            head_len = 0
            tail_len = 0

            if has_head and has_tail:
                head_len = available_length // 2
                bias = 50 if available_length > 100 else 0
                head_len -= bias
                tail_len = available_length - head_len
            elif has_head:
                head_len = available_length
            elif has_tail:
                tail_len = available_length

            head_str = msg_bytes[:head_len].decode("utf-8", "ignore") if head_len > 0 else ""
            tail_str = msg_bytes[-tail_len:].decode("utf-8", "ignore") if tail_len > 0 else ""

            formatted_str = self.template.format(
                head=head_str, truncation_message=self.truncation_message, tail=tail_str
            )

            result["data"] = formatted_str.encode("latin-1", "replace").decode("latin-1")
        else:
            result["data"] = message.encode("latin-1", "replace").decode("latin-1")

        return result
