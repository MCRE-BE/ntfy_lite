"""Module defining the Action class as well as it subclasses.

- ViewAction
- HttpAction
"""

# %%
####################
# Import Statement #
####################
import abc
import sys
import typing

if sys.version_info >= (3, 11):
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self
from enum import Enum, auto

from .utils import validate_url


###########
# CLASSES #
###########
class Action(abc.ABC):
    """Superclass for action buttons.

    See Also
    --------
    [ntfy button action documentation](https://ntfy.sh/docs/publish/#action-buttons)

    Parameters
    ----------
    action : str
        Name of the action (e.g. 'view', 'http').
    label : str
        Description of the action.
    url : str
        Where the action redirects.
    clear : bool, optional
        If true, the notification is deleted upon click. Defaults to False.
    """

    def __init__(
        self: Self,
        action: str,
        label: str,
        url: str,
        *,
        clear: bool = False,
    ) -> None:
        validate_url("Action.url", url)

        self.action = action
        self.label = label
        self.url = url
        if clear:
            self.clear = "true"
        else:
            self.clear = "false"

    @abc.abstractmethod
    def __str__(self: Self) -> str:
        """Format the action as a string."""

    @staticmethod
    def _quote(value: str) -> str:
        """Quote a string if it contains special characters.

        Parameters
        ----------
        value : str
            the string to quote.

        Returns
        -------
        str
            the quoted string.
        """
        # 1. Handle newlines and carriage returns (replace with space to keep header safe)
        value = value.replace("\n", " ").replace("\r", "")

        # 2. Check if we need quoting or escaping
        if any(c in value for c in (",", ";", '"', "\\", "=")):
            # 3. Escape backslashes first, then quotes
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value

    def _str(
        self: Self,
        attrs: tuple[str, ...],
    ) -> str:
        return ", ".join((
            self.action,
            *(f"{attr}={self._quote(str(val))}" for attr in attrs if (val := getattr(self, attr)) is not None),
        ))


class ViewAction(Action):
    """Class encapsulating the information of a view action.

    See Also
    --------
    See: [ntfy view action](https://ntfy.sh/docs/publish/#open-websiteapp)

    Parameters
    ----------
    label : str
        Description of the action.
    url : str
        Where the action redirects.
    clear : bool, optional
        If true, the notification is deleted upon click. Defaults to False.
    """

    def __init__(
        self: Self,
        label: str,
        url: str,
        *,
        clear: bool = False,
    ) -> None:
        super().__init__("view", label, url, clear=clear)

    def __str__(self: Self) -> str:
        _attrs = ("label", "url", "clear")
        return self._str(_attrs)


class HttpMethod(Enum):
    """List of methods supported by instances of HttpAction."""

    GET = auto()
    """ GET http method """

    POST = auto()
    """ POST http method """

    PUT = auto()
    """ PUT http method """


class HttpAction(Action):
    """Class encapsulating the information of an HTTP action.

    See Also
    --------
    See: [ntfy http action](https://ntfy.sh/docs/publish/#send-http-request)

    Parameters
    ----------
    label : str
        Arbitrary string description.
    url : str
        URL to which the request should be sent.
    clear : bool, optional
        If the ntfy notification should be cleared after the request succeeds. Defaults to False.
    method : HttpMethod, optional
        HTTP method to use (GET, POST or PUT). Defaults to HttpMethod.GET.
    headers : Mapping[str, str], optional
        HTTP headers to be passed in the request. Defaults to None.
    body : str, optional
        HTTP body content. Defaults to None.
    """

    def __init__(
        self: Self,
        label: str,
        url: str,
        *,
        clear: bool = False,
        method: HttpMethod = HttpMethod.GET,
        headers: typing.Mapping[str, str] | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__("http", label, url, clear=clear)
        self.method = method.value
        self.headers = headers
        self.body = body

    def __str__(self: Self) -> str:
        _attrs = ("label", "url", "clear", "method", "body")
        main = self._str(_attrs)
        if not self.headers:
            return main
        headers_str = ", ".join(
            f"headers.{self._quote(key)}={self._quote(value)}" for key, value in self.headers.items()
        )
        return f"{main}, {headers_str}"
