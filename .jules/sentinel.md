## 2025-07-01 - Replace broad exception blocks in metadata handler
**Vulnerability:** The application was catching broad `Exception` in metadata parsing operations (e.g., `piexif.load`, `piexif.dump`, byte decoding), which could mask logic errors and bugs like `NameError`, preventing them from surfacing for debugging, and thus breaking fail-secure principles.
**Learning:** Broad exception handling is often used initially for robustness but it hides underlying issues. In a local CLI application, hiding error details with generic catch-alls hinders maintainability.
**Prevention:** Use targeted exception handling (e.g., catching `ValueError`, `struct.error`, `OSError`, `UnicodeDecodeError`) so that expected failures are handled gracefully and unexpected bugs bubble up appropriately.
