# NTFY LITE

**ntfy_lite** is a minimalistic python API for sending [ntfy](https://ntfy.sh) notifications.

It comes with a **Handler** for the [logging package](https://docs.python.org/3/library/logging.html).

This fork contains significant enhancements to better handle high-volume notification traffic and modern Python environments.

## Fork Improvements

Compared to the original `ntfy_lite`, this version introduces:

- **Asynchronous Buffering**: Integrated SQLite-based persistence (`NtfyBuffer`). When the NTFY server returns an HTTP 429 "Too Many Requests" error, the message is automatically buffered locally and retried in the background using a dedicated daemon thread.
- **Improved Logging Handler**: The `NtfyHandler` now supports non-blocking delivery when configured with a `buffer_path`.
- **Modernized Codebase**: Support for Python 3.13+, improved typing using modern PEP standards, and a modernized build system (Hatch).
- **Code Quality**: Integrated `ruff` for consistent style and linting.

This is a fork of the original project, which can be found [here](https://github.com/MPI-IS/ntfy_lite).
Current documentation for this fork is available [here](https://mcre-be.github.io/ntfy_lite/).

## Installation


using `uv` (recommended):

```bash
uv add git+https://github.com/MCRE-BE/ntfy_lite.git
```

from source:

```bash
git clone https://github.com/MCRE-BE/ntfy_lite.git
cd ntfy_lite
uv pip install .
```

```bash
pip install git+https://github.com/MCRE-BE/ntfy_lite.git
```

```bash
uv pip install git+https://github.com/MCRE-BE/ntfy_lite.git
```

## Usage

The two following examples cover the full API.
You may also find the code in the demos folder of the sources.

### pushing notifications
[ntfy_push.py](https://github.com/MCRE-BE/ntfy_lite/blob/master/demos/ntfy_push.py)

### logging handler

[ntfy_logging.py](https://github.com/MCRE-BE/ntfy_lite/blob/master/demos/ntfy_logging.py)

## Limitation

No check regarding ntfy [limitations](https://ntfy.sh/docs/publish/#limitations) is performed before notifications are sent.

## Copyright

© 2020, Max Planck Society - Max Planck Institute for Intelligent Systems
