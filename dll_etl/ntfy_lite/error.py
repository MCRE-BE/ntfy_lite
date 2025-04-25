"""Define errors."""

from typing import Self


class NtfyError(Exception):
    """Error thrown when the push of a notification fails.

    Attributes
    ----------
      status_code: error code returned by the request
      reason: reason of the failure
    """

    def __init__(self: Self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason

    def __str__(self: Self) -> str:
        """Description of the status code and the reason."""
        return f"{self.status_code} ({self.reason})"
