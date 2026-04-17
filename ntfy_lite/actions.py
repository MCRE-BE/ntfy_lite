"""Module defining the Action class as well as it subclasses.

- ViewAction
- HttpAction
"""

# %%
####################
# Import Statement #
####################
import sys
import typing

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self
from enum import Enum, auto

from .utils import validate_url


###########
# CLASSES #
###########
class Action:
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
        clear: bool = False,
    ):
        validate_url("Action.url", url)

        self.action = action
        self.label = label
        self.url = url
        if clear:
            self.clear = "true"
        else:
            self.clear = "false"

    def _str(
        self: Self,
        attrs: tuple[str, ...],
    ) -> str:
        values = {attr: getattr(self, attr) for attr in attrs}
        return ", ".join([self.action] + [f"{attr}={value}" for attr, value in values.items() if value is not None])


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
        clear: bool = False,
    ) -> None:
        super().__init__("view", label, url, clear)

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
        clear: bool = False,
        method: HttpMethod = HttpMethod.GET,
        headers: typing.Mapping[str, str] | None = None,
        body: str | None = None,
    ):
        super().__init__("http", label, url, clear)
        self.method = method.value
        self.headers = headers
        self.body = body

    def __str__(self: Self) -> str:
        _attrs = ("label", "url", "clear", "method", "body")
        main = self._str(_attrs)
        if not self.headers:
            return main
        headers_str = ", ".join(f"headers.{key}={value}" for key, value in self.headers.items())
        return main + ", " + headers_str
