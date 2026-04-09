![unit tests](https://github.com/MPI-IS/ntfy_lite/actions/workflows/tests.yaml/badge.svg)
[![documentation](https://github.com/MPI-IS/ntfy_lite/actions/workflows/mkdocs.yaml/badge.svg)](https://mpi-is.github.io/ntfy_lite/)


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

Original project documentation can be found [here](https://mpi-is.github.io/ntfy_lite/), and the original source is available [here](https://github.com/MPI-IS/ntfy_lite).

## Installation


from source:

```bash
cd ntfy_lite
pip install .
```

from pypi:
```bash
pip install ntfy_lite
```

## Usage

The two following examples cover the full API.
You may also find the code in the demos folder of the sources.

### pushing notifications
https://github.com/MPI-IS/ntfy_lite/blob/da5750eed1ed58eacf4ff1bb1498586b41242f70/demos/ntfy_push.py#L1-L73

### logging handler

https://github.com/MPI-IS/ntfy_lite/blob/52fc7f008fdac3f735d39dd01064a0aa5b751e00/demos/ntfy_logging.py#L1-L146

## Limitation

No check regarding ntfy [limitations](https://ntfy.sh/docs/publish/#limitations) is performed before notifications are sent.

## Copyright

© 2020, Max Planck Society - Max Planck Institute for Intelligent Systems
