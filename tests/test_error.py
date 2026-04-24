"""Tests for NtfyError."""

from ntfy_lite.error import NtfyError

def test_ntfy_error_init():
    """Test NtfyError initialization."""
    error = NtfyError(404, "Not Found")
    assert error.status_code == 404
    assert error.reason == "Not Found"

def test_ntfy_error_str():
    """Test NtfyError string representation."""
    error = NtfyError(500, "Internal Server Error")
    assert str(error) == "500 (Internal Server Error)"
