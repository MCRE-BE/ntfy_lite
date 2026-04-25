"""Tests for utility functions."""

import re

import pytest

from ntfy_lite.utils import validate_url


def test_validate_url_none() -> None:
    """Test validate_url with None value."""
    # Should not raise any error
    assert validate_url("test_attr", None) is None


@pytest.mark.parametrize(
    "valid_url",
    [
        "https://example.com",
        "http://example.com/path",
        "http://localhost:8080/path",
        "https://example.com?query=1#fragment",
    ],
)
def test_validate_url_valid(valid_url: str) -> None:
    """Test validate_url with valid URLs."""
    # Should not raise any error
    assert validate_url("test_attr", valid_url) is None


@pytest.mark.parametrize(
    "invalid_url",
    [
        "example.com",
        "https://",
        "not a url",
        "",
        "http:/example.com",
        "/path/to/resource",
        "ftp://user:pass@host:21/path",
    ],
)
def test_validate_url_invalid(invalid_url: str) -> None:
    """Test validate_url with invalid URLs."""
    with pytest.raises(
        ValueError,
        match=re.escape(f"the value for test_attr ({invalid_url}) is not an url"),
    ):
        validate_url("test_attr", invalid_url)


def test_validate_url_error_message() -> None:
    """Test validate_url error message formatting."""
    attribute = "click_url"
    value = "invalid-url"
    with pytest.raises(
        ValueError,
        match=re.escape("the value for click_url (invalid-url) is not an url"),
    ) as excinfo:
        validate_url(attribute, value)
    assert str(excinfo.value) == r"the value for click_url (invalid-url) is not an url"
