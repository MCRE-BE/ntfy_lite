"""Security tests for Action classes."""

import typing
from unittest.mock import patch

import pytest

from ntfy_lite.actions import HttpAction, HttpMethod, ViewAction


@pytest.fixture(autouse=True)
def mock_validators() -> typing.Any:
    """Mock the urllib.parse module used in ntfy_lite.utils."""
    with patch("ntfy_lite.utils.urllib.parse") as mock:
        mock.urlparse.return_value.scheme = "https"
        mock.urlparse.return_value.netloc = "example.com"
        yield mock


def test_view_action_injection_label():
    """Test that ViewAction label with commas is properly escaped/quoted."""
    action = ViewAction("Label with, comma", "https://example.com")
    res = str(action)
    # This will fail before the fix
    assert 'label="Label with, comma"' in res


def test_http_action_injection_headers():
    """Test that HttpAction headers with special characters are properly escaped/quoted."""
    headers = {"X-Custom": "Value, body=injected"}
    action = HttpAction(
        "Post Data",
        "https://api.example.com",
        method=HttpMethod.POST,
        headers=headers,
    )
    res = str(action)
    # This will fail before the fix
    assert 'headers.X-Custom="Value, body=injected"' in res


def test_http_action_injection_body():
    """Test that HttpAction body with special characters is properly escaped/quoted."""
    action = HttpAction("Label", "https://api.example.com", body="Body with; semicolon")
    res = str(action)
    # This will fail before the fix
    assert 'body="Body with; semicolon"' in res


def test_action_quoting_double_quotes():
    """Test that double quotes are escaped."""
    action = ViewAction('Label with "quotes"', "https://example.com")
    res = str(action)
    # This will fail before the fix
    assert 'label="Label with \\"quotes\\""' in res
