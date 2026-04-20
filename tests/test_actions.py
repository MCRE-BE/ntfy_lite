"""Tests."""

####################
# IMPORT STATEMENT #
####################
import typing
from unittest.mock import patch

import pytest

from ntfy_lite.actions import Action, HttpAction, HttpMethod, ViewAction


####################
# INDIVIDUAL TESTS #
####################
@pytest.fixture(autouse=True)
def mock_validators() -> typing.Any:
    """Mock the urllib.parse module used in ntfy_lite.utils."""
    with patch("ntfy_lite.utils.urllib.parse") as mock:
        mock.urlparse.return_value.scheme = "https"
        mock.urlparse.return_value.netloc = "example.com"
        yield mock


class MockAction(Action):
    """Mock Action for testing base class functionality."""

    def __str__(self: typing.Any) -> str:
        """Format the action as a string."""
        return self._str(("label", "url"))


def test_action_init(mock_validators: typing.Any) -> None:
    """Test Action base class initialization."""
    # Test with clear=False (default)
    action = MockAction("test_action", "Test Label", "https://example.com")
    assert action.action == "test_action"
    assert action.label == "Test Label"
    assert action.url == "https://example.com"
    assert action.clear == "false"

    # Test with clear=True
    action_clear = MockAction("test_action", "Test Label", "https://example.com", clear=True)
    assert action_clear.clear == "true"

    # Test URL validation call
    mock_validators.urlparse.assert_called_with("https://example.com")


def test_action_str_helper() -> None:
    """Test Action._str helper method."""
    action = MockAction("test_action", "Test Label", "https://example.com", clear=False)
    attrs = ("label", "url", "clear")
    result = action._str(attrs)
    assert result == "test_action, label=Test Label, url=https://example.com, clear=false"

    # Test with some None values (should be skipped)
    setattr(action, "test_attr", None)  # noqa: B010
    result_with_none = action._str(("label", "test_attr"))
    assert result_with_none == "test_action, label=Test Label"


def test_view_action_init() -> None:
    """Test ViewAction initialization."""
    action = ViewAction("View Website", "https://is.mpg.de", clear=True)
    assert action.action == "view"
    assert action.label == "View Website"
    assert action.url == "https://is.mpg.de"
    assert action.clear == "true"


def test_view_action_str() -> None:
    """Test ViewAction __str__ method."""
    action = ViewAction("View Website", "https://is.mpg.de")
    assert str(action) == "view, label=View Website, url=https://is.mpg.de, clear=false"


def test_http_action_init() -> None:
    """Test HttpAction initialization."""
    headers = {"Authorization": "Bearer token"}
    body = '{"key": "value"}'
    action = HttpAction(
        "Post Data",
        "https://api.example.com",
        method=HttpMethod.POST,
        headers=headers,
        body=body,
    )
    assert action.action == "http"
    assert action.label == "Post Data"
    assert action.url == "https://api.example.com"
    assert action.method == HttpMethod.POST.value
    assert action.headers == headers
    assert action.body == body


def test_http_action_str() -> None:
    """Test HttpAction __str__ method."""
    # Test without headers
    action_no_headers = HttpAction("Get Data", "https://api.example.com", method=HttpMethod.GET)
    expected_no_headers = "http, label=Get Data, url=https://api.example.com, clear=false, method=1"
    assert str(action_no_headers) == expected_no_headers

    # Test with headers
    headers = {"X-Custom": "Value", "Content-Type": "application/json"}
    action_with_headers = HttpAction(
        "Post Data",
        "https://api.example.com",
        method=HttpMethod.POST,
        headers=headers,
    )
    res = str(action_with_headers)
    assert "http, label=Post Data, url=https://api.example.com, clear=false, method=2" in res
    assert "headers.X-Custom=Value" in res
    assert "headers.Content-Type=application/json" in res
