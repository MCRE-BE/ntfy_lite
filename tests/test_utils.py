"""Tests for utility functions."""

import re

import pytest

from ntfy_lite.utils import validate_url


def test_validate_url_none() -> None:
    """Test validate_url with None value."""
    # Should not raise any error
    assert validate_url("test_attr", None) is None


def test_validate_url_valid() -> None:
    """Test validate_url with valid URLs."""
    # Should not raise any error
    assert validate_url("test_attr", "https://example.com") is None
    assert validate_url("test_attr", "http://localhost:8080/path") is None
    assert validate_url("test_attr", "https://example.com?query=1#fragment") is None


def test_validate_url_invalid_missing_scheme() -> None:
    """Test validate_url with URL missing scheme."""
    with pytest.raises(
        ValueError,
        match=re.escape("the value for test_attr (example.com) is not an url"),
    ):
        validate_url("test_attr", "example.com")


def test_validate_url_invalid_missing_netloc() -> None:
    """Test validate_url with URL missing netloc."""
    with pytest.raises(
        ValueError,
        match=re.escape("the value for test_attr (https://) is not an url"),
    ):
        validate_url("test_attr", "https://")


def test_validate_url_invalid_path_only() -> None:
    """Test validate_url with path only."""
    with pytest.raises(
        ValueError,
        match=re.escape("the value for test_attr (/path/to/resource) is not an url"),
    ):
        validate_url("test_attr", "/path/to/resource")


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
