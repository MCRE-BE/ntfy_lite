"""Define errors."""

# %%
####################
# Import Statement #
####################
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


###########
# CLASSES #
###########
class NtfyError(Exception):
    """Error thrown when the push of a notification fails.

    Attributes
    ----------
    status_code : int
        Error code returned by the request.
    reason : str
        Reason of the failure.

    Parameters
    ----------
    status_code : int
        Error code returned by the request.
    reason : str
        Reason of the failure.
    """

    def __init__(self: Self, status_code: int, reason: str):
        self.status_code = status_code
        self.reason = reason

    def __str__(self: Self) -> str:
        """Description of the status code and the reason."""
        return f"{self.status_code} ({self.reason})"
