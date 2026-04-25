"""Tests for the CLI module."""

from pathlib import Path
from unittest import mock

import pytest

from ntfy_lite.cli import main
from ntfy_lite.config import Priority


def test_cli_push_defaults(monkeypatch):
    """Test CLI push with default optional arguments."""
    test_args = ["ntfy-lite", "mytopic", "mytitle"]
    monkeypatch.setattr("sys.argv", test_args)

    with mock.patch("ntfy_lite.cli.push") as mock_push:
        main()
        mock_push.assert_called_once_with(
            topic="mytopic",
            title="mytitle",
            message=None,
            priority=Priority.DEFAULT,
            tags=None,
            click=None,
            email=None,
            filepath=None,
            attach=None,
            icon=None,
            at=None,
            url="https://ntfy.sh",
        )


def test_cli_push_all_args(monkeypatch):
    """Test CLI push with all optional arguments provided."""
    test_args = [
        "ntfy-lite",
        "mytopic",
        "mytitle",
        "-m",
        "hello world",
        "-p",
        "high",
        "-t",
        "warning,skull",
        "-c",
        "https://example.com",
        "-e",
        "test@example.com",
        "-f",
        "/path/to/file.txt",
        "-a",
        "https://example.com/file.txt",
        "-i",
        "https://example.com/icon.png",
        "--at",
        "tomorrow, 10am",
        "-u",
        "https://custom.ntfy.sh",
    ]
    monkeypatch.setattr("sys.argv", test_args)

    with mock.patch("ntfy_lite.cli.push") as mock_push:
        main()
        mock_push.assert_called_once_with(
            topic="mytopic",
            title="mytitle",
            message="hello world",
            priority=Priority.HIGH,
            tags=["warning", "skull"],
            click="https://example.com",
            email="test@example.com",
            filepath=Path("/path/to/file.txt"),
            attach="https://example.com/file.txt",
            icon="https://example.com/icon.png",
            at="tomorrow, 10am",
            url="https://custom.ntfy.sh",
        )


def test_cli_push_error(monkeypatch):
    """Test CLI handles push errors gracefully."""
    test_args = ["ntfy-lite", "mytopic", "mytitle"]
    monkeypatch.setattr("sys.argv", test_args)

    with mock.patch("ntfy_lite.cli.push", side_effect=Exception("API Error")):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
