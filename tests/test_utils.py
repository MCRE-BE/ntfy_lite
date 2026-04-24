import pytest

from ntfy_lite.utils import validate_url


def test_validate_url_none():
    assert validate_url("test_attr", None) is None


@pytest.mark.parametrize(
    "valid_url",
    [
        "https://example.com",
        "http://example.com/path",
        "ftp://user:pass@host:21/path",
    ],
)
def test_validate_url_valid(valid_url):
    assert validate_url("test_attr", valid_url) is None


@pytest.mark.parametrize(
    "invalid_url",
    [
        "example.com",
        "https://",
        "not a url",
        "",
        "http:/example.com",
    ],
)
def test_validate_url_invalid(invalid_url):
    with pytest.raises(ValueError, match=rf"the value for test_attr \({invalid_url}\) is not an url"):
        validate_url("test_attr", invalid_url)
