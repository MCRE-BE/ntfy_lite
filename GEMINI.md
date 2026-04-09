# Project: ntfy_lite
**Location:** `C:\Users\PBE00A26\Python_Code\ntfy_lite`

## Project Context
- **Product:** ntfy_lite (Fork).
- **Domain:** Minimalistic Python API for sending [ntfy](https://ntfy.sh) notifications.
- **Source:** This is a high-performance fork of `MPI-IS/ntfy_lite`, modernized for Python 3.13 and enhanced with asynchronous buffering.

## Tech Stack & Tooling
- **Language:** Python 3.13+ (strict requirement).
- **Environment Management:** Use `uv` for local development and dependency resolution.
- **Build System:** `hatch` (configured in `pyproject.toml`).
- **Persistence:** `sqlite3` (used for the `NtfyBuffer`).
- **Linting & Formatting:**
  - **Python:** `ruff`. Always run `uv run ruff check --fix` and `uv run ruff format` after editing.

## Engineering Standards
- **Python Style:** Adhere to `numpy` docstring convention.
- **Type Safety:** Use type annotations for all new Python functions. Favor modern `typing.Self` and `list`/`dict` (Python 3.10+ style).
- **Naming:** `snake_case` for variables/functions, `PascalCase` for classes (e.g., `NtfyBuffer`).
- **Path Handling:** Use `pathlib.Path` for all file and directory navigation.
- **Branching Workflow:** **NEVER** commit directly to the `master` branch. All changes must be implemented in feature branches and merged via Pull Requests on GitHub.

## Key Features & Logic
- **Asynchronous Buffering**: When hit with an HTTP 429 (Rate Limit) error, the `NtfyHandler` (if configured with a `db_path`) will offload the message to a SQLite `NtfyBuffer`. A background daemon thread handles retries every 60 seconds.
- **Non-blocking Handler**: The `NtfyHandler` is designed to be "fire-and-forget" when buffering is enabled, ensuring the main application thread never stalls on network or rate-limit issues.

## Workflow Specifics
- **Verification:** Before considering a task complete, verify the buffering logic. You can use/re-create a verification script that uses `DryRun.error` and `_SIMULATE_429 = True` to force buffering.
- **Testing:** run `uv run pytest tests/` to verify core notification logic.

## Safety Guards
- **SQLite Persistence**: Ensure the `db_path` passed to the handler is in a persistent directory if notifications must survive application restarts.
- **Rate Limits**: The background flusher respects a 60-second linear wait to stay within standard ntfy.sh public instance limits.
