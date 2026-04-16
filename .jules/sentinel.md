## 2026-04-02 - Information Leakage via Exception Handling
**Vulnerability:** In `parse_metadata_input` in `metadata.py`, raw exception details were passed directly to `console.print()` when JSON loading or parsing failed. This could potentially leak internal stack trace fragments, internal file paths, or other system details to a user.
**Learning:** Even simple file I/O operations (like `json.load`) should catch and mask exceptions before returning error messages to the CLI to prevent sensitive internal data leakage.
**Prevention:** Catch generic `Exception`s without capturing them to a variable (e.g. avoid `except Exception as e:` printing `e`), and instead return or print hardcoded generic error statements (e.g., "Error reading JSON file").

## 2026-04-07 - Overly Broad Exception Handling Swallowing Errors
**Vulnerability:** Found multiple instances of `except Exception: pass` in `processing.py` and `metadata.py`. This anti-pattern silently swallowed any error (like `KeyboardInterrupt`, `MemoryError`, or severe data corruption errors), which could hide security flaws or resource leaks.
**Learning:** Swallowing all exceptions makes the system fail silently, leaving it in an unknown state which attackers could potentially exploit. File operations like `os.remove()` should only catch expected errors like `OSError`.
**Prevention:** Always scope exception handling to specific, expected error types (e.g., `OSError` instead of `Exception`), or log/print a safe warning when catching generic exceptions to ensure visibility into application health.

## 2026-04-05 - Fix Exception Data Leakage
**Vulnerability:** Raw exception strings (e.g., stack traces, internal paths) were exposed directly to users via CLI output.
**Learning:** This application directly passed the exception instance `e` to `console.print(f"... {e}")` in high-level try/except blocks (e.g., `main.py`, `menu.py`, `file_management.py`), inadvertently creating an information disclosure vulnerability.
**Prevention:** Always use safe, generic error messages when outputting to user-facing interfaces. Log the raw exception details internally using a dedicated logging framework if debugging information is required, but never leak them directly to the end-user.

## 2025-02-27 - Decompression Bomb Vulnerability in Pillow
**Vulnerability:** The application was globally overriding `Image.MAX_IMAGE_PIXELS = 100_000_000` to "prevent decompression bomb attacks". However, Pillow's default is actually stricter (~89.4 million pixels). By explicitly setting it higher, the code inadvertently weakened security against DoS attacks. Additionally, modifying module-level state locally inside functions (`rich_menu.py`) is a dangerous practice that can cause unexpected side effects across the application.
**Learning:** Do not manually override security limits unless explicitly required, and understand the default protections of established libraries before attempting to "enhance" them.
**Prevention:** Rely on Pillow's default decompression bomb protection. Never set global state variables within local function scope.
