# Agent Instructions

## Dev  tips
- **Branching**: Never commit directly to `master` or `main`. Use feature branches and merge-based workflows.
- We don't work with a develop branch, but with a **version release branch**. When making suggestions, always look at the latest
  version branch as your base (usually `vX.X.X_release_branch`) and not main.
- Limit your changes to a **single improvement** or change and change as little files as possible

## Tech Stack & Tooling
- **Language**: Python 3.10+ (unless specified otherwise).
- **Environment**: Use `uv` for all dependency management and execution.
- **Pre-commit**: Use `prek` to run pre-commit hooks.
- **Linting & Formatting**:
  - **Ruff**: Always run `uv run ruff check --fix` and `uv run ruff format` after editing and before commiting.
  - **Ty**: Always run `uv run ty check .` after editing and before commiting.
  - **pytest**: Always run `uv run pytest tests/` after editing and before commiting.

## Testing instructions
- Find the CI plan in the .github/workflows folder.
- Fix any test or type errors until the whole suite is green.
- Add or update tests for the code you change, even if nobody asked.

## PR instructions
- Use **Conventional Commits** in commits and PR's. This means to format them as <type>[optional scope]: <description>
- Always run `prek run --all-files` and `uv run pytest tests/` before committing. 

## Engineering Standards
- **Python Style**:
  - **Documentation**: Use **NumPy docstring** convention for all public classes and functions.
  - **Formatting**: Use **trailing commas** for multi-line lists/parameters to force clean diffs.
  - **Safety**: Prefer **named arguments** over positional ones for clarity.
  - **Types**: Use strict type annotations for all new code. Favor `typing.Self` and standard collections (`list`, `dict`).
  - **Paths**: Use `pathlib.Path` exclusively.
