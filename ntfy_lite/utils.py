"""Module defining the function 'validate_url'."""

import urllib.parse


def validate_url(attribute: str, value: str | None) -> None:
    """Validate URL.

    Return None if value is a valid URL or is None,
    raises a ValueError otherwise.

    Parameters
    ----------
    attribute : str
        an arbitrary string, used in the message of the raised ValueError.
    value : str | None
        the string to check.
    """
    if value is None:
        return
    parsed = urllib.parse.urlparse(value)
    if not parsed.scheme or not parsed.netloc or parsed.scheme not in ("http", "https"):
        raise ValueError(f"the value for {attribute} ({value}) is not an url")
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"the value for {attribute} ({value}) has an invalid scheme: {parsed.scheme}")
