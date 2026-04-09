## 2024-04-06 - CLI Exception Handler Mocking
**Learning:** Testing CLI arguments like `sys.argv` and file finding with `glob.glob` using `@patch` requires completely isolating standard output using `@patch("image_converter.main.console.print")` to verify error states reliably.
**Action:** Mock file resolution (`glob.glob`) rather than depending on disk contents when covering error paths for empty or invalid paths in the main CLI entry point.

## 2026-03-20 - Edge Cases and Fast Paths in PIL Image Processing
**Learning:** Certain Pillow `ImageEnhance` operations and edge detection methods have specific mathematical and boundary constraints (e.g., Kovalevsky requiring >= 6x6 pixel images to perform 5-pixel comparison window diffs, or alpha channels being preserved via manual fast paths in RGBA modes).
**Action:** When adding test coverage to image processing functions, always include edge cases for extreme input dimensions (small images, zero values) and test multi-channel preservation (RGBA) specifically on optimization fast-paths.

## $(date +%Y-%m-%d) - Edge Cases in Image Processing Pipeline
**Learning:** Testing side effects in complex file processing pipelines (like `process_images_and_save` in `processing.py`) often requires precise mocking of `os` and `shutil` components, especially for error handling paths (e.g. `OSError` during temp file removal). The Rich `Console.print` outputs Table objects, which must be captured or stringified to verify formatted output strings rather than inspecting raw call arguments.
**Action:** When testing Rich console output containing tables, instantiate a test `Console`, use `console.capture()` to render the argument into a string, and assert on the string to verify formatting logic (like byte size conversions). When testing temp file cleanups in `finally` blocks, selectively patch `os.path.exists` and `os.replace` to simulate error states without causing infinite recursions or breaking the test runner.

## 2024-05-20 - Testing missing operation handlers in processing.py
**Learning:** Testing simple mapping handlers (e.g., `handle_vignette` in `processing.py`) is surprisingly effective and simple to implement by mocking `rich.console.Console.print` and the core image filter function (`apply_vignette`). Returning a mock value from the core function and asserting it's returned by the handler ensures the entire workflow logic is verified.
**Action:** When adding or verifying tests for CLI mapping handlers that delegate to core domain logic, structure the test to patch the output console and the target function, execute with sample CLI argument values, and strictly assert the target function was called precisely and the response directly propagated.

## 2026-03-24 - Testing interactive menu prompts with restricted environments
**Learning:** Testing interactive menu functions (e.g., `prompt_for_vignette_options`) that use `_ask_text` can be effectively done by mocking the input helper to return either empty strings (to trigger defaults) or specific values. In environments where `pytest` is missing, `unittest.TestCase` wrappers can be used alongside custom mocked runners (like `run_mocked_tests.py`) to verify logic.
**Action:** When adding test coverage for CLI prompt functions, mock the primary input mechanism (`_ask_text` or `questionary.select`) and verify the resulting operation dictionary. Ensure compatibility with the existing test suite and any available mocked test runners for verification.

## 2024-05-25 - Mocking nested functions and imports in Pytest
**Learning:** Pytest will silently fail or get confused if testing variables/classes like `patch`, `MagicMock` or `pytest` itself are repeatedly imported inside local test functions rather than correctly managed as module-level imports.
**Action:** Place `from unittest.mock import patch, MagicMock` and `import pytest` at the top of test files when using them across multiple test functions.

## 2024-05-25 - Mocking Pillow Image Mode Properties
**Learning:** Pillow's `Image.mode` is a property and cannot be directly patched on a real image instance using `unittest.mock.patch.object()`. Attempting to do so results in an `AttributeError: property 'mode' of 'Image' object has no setter` or `deleter`.
**Action:** To test fallback branches or unexpected image modes, instantiate a mock image (`MagicMock(spec=Image.Image)`), assign the necessary properties (`mock_img.mode = "UNKNOWN"`), and configure the relevant methods (`mock_img.getbands.return_value = ("R", "G", "B")`, `mock_img.convert.return_value = mock_img`) to simulate the required behavior without triggering Pillow's internal type checks.

## $(date +%Y-%m-%d) - Testing Questionary UI Workflows
**Learning:** When writing tests for CLI interfaces that use the `questionary` library to present interactive menus (e.g., `questionary.checkbox`), the actual execution stops to wait for user input unless properly mocked. Furthermore, because these functions often invoke other UI dependencies like `rich` and OS-level operations (e.g., file sizes via `os.path.getsize` or image metadata via Pillow `Image.open`), testing them safely requires extensive patching to isolate the logic.
**Action:** When testing `questionary` UI selections, mock the specific `questionary` method (e.g., `@patch("module.questionary.checkbox")`) and configure its fluent `.ask()` return value via `mock_checkbox.return_value.ask.return_value = [...]` to simulate the user's choice. Ensure all secondary side-effect calls (like printing to the console or reading from disk) are also mocked to avoid blocking or errors in the CI/CD pipeline.

## 2026-04-02 - Trim Bounding Box Edge Case
**Learning:** The image trimming logic in `src/image_converter/remove_background.py` uses `ImageChops.difference` and `getbbox()` to find content. If an image is completely uniform (no borders or transparent areas to trim), `getbbox()` returns `None`. This is an easy branch to miss if only testing images with actual transparent borders.
**Action:** When testing image manipulation functions that rely on `getbbox()` for cropping or boundary detection, always include an edge case test where the entire image is a solid, uniform color (without an alpha channel if that triggers a different path) to ensure the fallback `return original_image` branch is covered.

## 2025-02-28 - Testing Valid JSON That Resolves to Non-Dictionary
**Learning:** In `src/image_converter/metadata.py`, defensive parsing logic checks if inline JSON strings start with `{` before running `json.loads`. Because of this filter, any naturally valid JSON string that passes this check will always return a dictionary. Testing the failure block (`if not isinstance(result, dict)`) requires using `unittest.mock.patch` to artificially force `json.loads` to return a list or integer while still providing a valid-looking string `{"fake": "json"}`.
**Action:** When testing defensive type-validation paths for pre-filtered inputs, explicitly mock the parser to return the invalid type rather than trying to craft a raw string that bypasses the filter.

## 2024-05-18 - Valid JSON Resolving to Non-Dictionaries
**Learning:** When parsing JSON input (e.g., via `json.load()` or `json.loads()`), it is critical to explicitly validate the structure of the resulting data (e.g., `isinstance(result, dict)`) before returning it. Valid JSON can resolve to a list, string, or number, which will cause downstream runtime crashes if callers assume a dictionary and invoke methods like `.items()`.
**Action:** When writing tests for JSON parsing or metadata inputs, always include edge cases where the input is structurally valid JSON but resolves to a list or integer instead of a dictionary, ensuring graceful error handling.
