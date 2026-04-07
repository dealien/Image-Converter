## 2026-04-02 - Information Leakage via Exception Handling
**Vulnerability:** In `parse_metadata_input` in `metadata.py`, raw exception details were passed directly to `console.print()` when JSON loading or parsing failed. This could potentially leak internal stack trace fragments, internal file paths, or other system details to a user.
**Learning:** Even simple file I/O operations (like `json.load`) should catch and mask exceptions before returning error messages to the CLI to prevent sensitive internal data leakage.
**Prevention:** Catch generic `Exception`s without capturing them to a variable (e.g. avoid `except Exception as e:` printing `e`), and instead return or print hardcoded generic error statements (e.g., "Error reading JSON file").

## 2026-04-07 - Overly Broad Exception Handling Swallowing Errors
**Vulnerability:** Found multiple instances of `except Exception: pass` in `processing.py` and `metadata.py`. This anti-pattern silently swallowed any error (like `KeyboardInterrupt`, `MemoryError`, or severe data corruption errors), which could hide security flaws or resource leaks.
**Learning:** Swallowing all exceptions makes the system fail silently, leaving it in an unknown state which attackers could potentially exploit. File operations like `os.remove()` should only catch expected errors like `OSError`.
**Prevention:** Always scope exception handling to specific, expected error types (e.g., `OSError` instead of `Exception`), or log/print a safe warning when catching generic exceptions to ensure visibility into application health.