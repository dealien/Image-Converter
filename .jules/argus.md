## 2024-04-06 - CLI Exception Handler Mocking
**Learning:** Testing CLI arguments like `sys.argv` and file finding with `glob.glob` using `@patch` requires completely isolating standard output using `@patch("image_converter.main.console.print")` to verify error states reliably.
**Action:** Mock file resolution (`glob.glob`) rather than depending on disk contents when covering error paths for empty or invalid paths in the main CLI entry point.
