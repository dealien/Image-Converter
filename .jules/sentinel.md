## 2026-04-05 - Fix Exception Data Leakage
**Vulnerability:** Raw exception strings (e.g., stack traces, internal paths) were exposed directly to users via CLI output.
**Learning:** This application directly passed the exception instance `e` to `console.print(f"... {e}")` in high-level try/except blocks (e.g., `main.py`, `menu.py`, `file_management.py`), inadvertently creating an information disclosure vulnerability.
**Prevention:** Always use safe, generic error messages when outputting to user-facing interfaces. Log the raw exception details internally using a dedicated logging framework if debugging information is required, but never leak them directly to the end-user.
