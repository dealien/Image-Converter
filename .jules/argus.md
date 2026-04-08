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
## 2024-04-08 - Unreachable `image.rotate()` after exact 90-degree fast-paths
**Learning:** In `src/image_converter/image_filters.py`, the fallback `image.rotate(clamped_angle, expand=True)` on line 802 is strictly unreachable. The `clamped_angle` computation rounds to nearest 90 (0, 90, 180, 270). The preceding `if/elif` block explicitly handles all four possible values (0 returns early, the other three use `transpose`). Thus, attempting to cover line 802 is impossible without modifying the math, exposing a case where code was written for a broader domain than what the input sanitization actually permits.
**Action:** When adding fast-paths for a discrete set of input possibilities that comprehensively covers all sanitized inputs, remove the fallback generalized logic instead of leaving it as dead, un-coverable code.
