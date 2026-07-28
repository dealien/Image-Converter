# Python Codebase Learnings

## 2026-07-27 - Virtual Environment Dependency Syncing
**Learning:** Returning to this project or pulling new dependencies in `pyproject.toml` requires re-running `.\.venv\Scripts\python.exe -m pip install -e .[dev,docs]` inside `.venv` to ensure optional dependencies (e.g. `piexif`) are synced into the environment.
**Action:** When encountering missing `ModuleNotFoundError` for packages declared in `pyproject.toml`, run `.\.venv\Scripts\python.exe -m pip install -e .[dev,docs]` to sync dependencies into `.venv`.
