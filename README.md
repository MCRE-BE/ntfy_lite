![unit tests](https://github.com/MPI-IS/ntfy_lite/actions/workflows/tests.yaml/badge.svg)
[![documentation](https://github.com/MPI-IS/ntfy_lite/actions/workflows/mkdocs.yaml/badge.svg)](https://mpi-is.github.io/ntfy_lite/)

# NTFY LITE

**ntfy_lite** is a minimalistic python API for sending [ntfy](https://ntfy.sh) notifications.

It provides a simple and programmatic way to integrate notifications into your Python scripts and applications. Out of the box, it supports advanced `ntfy` features such as actions, attachments, tags, and priorities. Additionally, it comes with a dedicated **Handler** for the built-in Python [logging package](https://docs.python.org/3/library/logging.html), allowing you to easily route warnings, errors, and critical logs to your phone or desktop.

## Fork Improvements

Compared to the original `ntfy_lite`, this version introduces significant enhancements to better handle high-volume notification traffic and modern Python environments:

- **Asynchronous Buffering**: Integrated SQLite-based persistence (`NtfyBuffer`). When the NTFY server returns an HTTP 429 "Too Many Requests" error, the message is automatically buffered locally and retried in the background using a dedicated daemon thread.
- **Improved Logging Handler**: The `NtfyHandler` now supports non-blocking delivery when configured with a `buffer_path`.
- **Modernized Codebase**: Support for Python 3.13+, improved typing using modern PEP standards, and a modernized build system (Hatch).
- **Code Quality**: Integrated `ruff` for consistent style and linting.

Original project documentation can be found [here](https://mpi-is.github.io/ntfy_lite/), and the original source is available [here](https://github.com/MPI-IS/ntfy_lite).

## Installation

As this is a fork, it is recommended to install directly from source rather than PyPI.

**Standard Installation:**
```bash
git clone https://github.com/MPI-IS/ntfy_lite.git
cd ntfy_lite
pip install .
```

**With Buffering Support:**
To enable SQLite-based background buffering to prevent 429 rate limit freezes, install the `buffer` extra:
```bash
git clone https://github.com/MPI-IS/ntfy_lite.git
cd ntfy_lite
pip install ".[buffer]"
```

## Structure & Options

The repository exposes two main ways of interacting with `ntfy`:

1. **Direct Notification Pushing (`ntfy.push`)**: A straightforward function to trigger a single notification.
2. **Logging Integration (`ntfy.NtfyHandler`)**: A drop-in handler for `logging.Logger` to route application logs natively.

### Key Options

- `topic`: The target ntfy.sh topic (e.g., `mytopic`).
- `priority`: Defines the urgency. Values: `MAX`, `HIGH`, `DEFAULT`, `LOW`, `MIN` (via `ntfy.Priority`).
- `tags`: A string or list of strings to append emojis or tags.
- `actions`: Add interactive buttons using `ViewAction` (opens a URL) or `HttpAction` (sends a background HTTP request).
- `filepath`: Send a local file as an attachment.
- `dry_run`: Prevent actual network calls during testing using `ntfy.DryRun.on` or `ntfy.DryRun.error`.

---

## Examples

### Pushing a Simple Notification

```python
import ntfy_lite as ntfy

ntfy.push(
    topic="my_alerts",
    title="Backup Complete",
    message="The daily database backup finished successfully.",
    priority=ntfy.Priority.DEFAULT,
    tags=["white_check_mark", "floppy_disk"]
)
```

### Pushing with Interactive Actions

```python
import ntfy_lite as ntfy

view_btn = ntfy.ViewAction(label="Open Dashboard", url="https://dashboard.local", clear=True)

ntfy.push(
    topic="my_alerts",
    title="New User Registered",
    message="A new user signed up for the platform.",
    tags="tada",
    actions=[view_btn]
)
```

### Setting up the Logging Handler

```python
import logging
import ntfy_lite as ntfy

# Set up the custom NtfyHandler
ntfy_handler = ntfy.NtfyHandler(
    topic="app_error_logs",
    # (Optional) Enable asynchronous buffering to avoid HTTP 429 blockages
    # db_path=Path("/tmp/ntfy_buffer.sqlite")
)

# Configure the root logger
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), ntfy_handler],
)

logger = logging.getLogger("MyApp")
logger.error("Database connection failed! Retrying in 5s...")
```

---

## File Directory Description & Audit

Below is an overview of the internal structure and files in this package, along with their roles and recommendations for the future:

### Core Files (Essential Functionality)
- **`ntfy_lite/__init__.py`**: Exposes the public API (e.g., `push`, `NtfyHandler`, `Action`).
- **`ntfy_lite/ntfy.py`**: Contains the core `push` function, parameter validation, and actual HTTP request logic towards the ntfy server.
- **`ntfy_lite/handler.py`**: Defines `NtfyHandler`, integrating the push functionality smoothly into Python's standard `logging` library.
- **`ntfy_lite/actions.py`**: Defines the `Action` superclass alongside `ViewAction` and `HttpAction` to enable interactive notification buttons.
- **`ntfy_lite/buffer.py`**: Manages the SQLite database and the background daemon thread responsible for asynchronously retrying rate-limited (HTTP 429) requests.
- **`ntfy_lite/ntfy2logging.py`**: Maps standard Python logging levels to `ntfy` priorities (e.g., `CRITICAL` -> `MAX`).
- **`ntfy_lite/defaults.py`**: Provides default tags (emojis) for standard logging levels.
- **`ntfy_lite/error.py`**: Defines `NtfyError`, a custom exception triggered upon failed API requests.
- **`ntfy_lite/utils.py`**: Contains helper routines, like URL validation using the `validators` library.
- **`ntfy_lite/py.typed`**: A marker file indicating that the package includes inline type annotations (PEP 561 compliance).
- **`ntfy_lite/version.py`**: Dynamically reads the package version utilizing `importlib.metadata`.

### Candidates for Deletion / Movement
- **`ntfy_lite/demo_logging.py`**: Contains a demo script for logging. **Flag:** Candidate for deletion/movement. Demonstration scripts should ideally be placed in an `examples/` directory at the repository root, rather than inside the distributable Python package.
- **`ntfy_lite/demo_push.py`**: Contains a demo script for push notifications. **Flag:** Candidate for deletion/movement. Same reason as above.

### Project Configuration & Maintenance Files
- **`pyproject.toml`**: The modern build system configuration (Hatch) listing dependencies, metadata, and tools (e.g., Ruff, Pyright).
- **`README.md`**: This documentation file.
- **`LICENSE`**: The open-source MIT License terms.
- **`tests/test_ntfy_lite.py`**: Unit tests ensuring functions run effectively without regressions.
- **`.github/`**: Houses GitHub Actions workflows for continuous integration, dependabot configurations, and issue templates.
- **`docs/`**: Documentation source files for MkDocs/Zensical rendering.

## Limitation

No check regarding ntfy [limitations](https://ntfy.sh/docs/publish/#limitations) is performed *before* notifications are sent, but `ntfy_lite` (when using the buffer) respects 429 headers and attempts to stagger retries to resolve them natively.

## Copyright

© 2020, Max Planck Society - Max Planck Institute for Intelligent Systems
