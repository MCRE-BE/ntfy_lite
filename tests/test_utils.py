import pytest

from ntfy_lite.utils import validate_url


def test_validate_url_valid():
    validate_url("test", "http://example.com")
    validate_url("test", "https://example.com/path?query=1")


def test_validate_url_none():
    validate_url("test", None)


def test_validate_url_invalid_scheme():
    with pytest.raises(ValueError, match="has an invalid scheme: ftp"):
        validate_url("test", "ftp://example.com")


def test_validate_url_missing_scheme_or_netloc():
    with pytest.raises(ValueError, match="is not an url"):
        validate_url("test", "file:///etc/passwd")
    with pytest.raises(ValueError, match="is not an url"):
        validate_url("test", "example.com")
    with pytest.raises(ValueError, match="is not an url"):
        validate_url("test", "http://")
