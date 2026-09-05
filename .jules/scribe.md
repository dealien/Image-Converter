## 2025-05-15 - Pillow Type Hints for Generic Images
**Learning:** Using `ImageFile` as a generic type hint in Pillow causes confusion for tools expecting general image processing types, as `ImageFile` is actually a specific subclass used for lazy-loading image files, not the generic image object.
**Action:** When adding type hints to functions accepting Pillow images (like filters, resizing, background removal), always use `PIL.Image.Image` as the standard type hint for an image object unless specifically relying on the lazy-loading properties of `ImageFile`.

## 2025-05-18 - Type Hints on Inner Functions
**Learning:** When adding type hints to inner callback functions (like `validate` in `prompt_toolkit`), using string literals (e.g., `"prompt_toolkit.document.Document"`) for types that are not explicitly imported at the module level prevents `NameError` or `ImportError` runtime crashes while still providing valuable type information for documentation.
**Action:** Always use string literal type hints for complex objects or external library types that aren't already imported in the current module's scope, especially when documenting nested or inner functions.

## 2025-05-19 - Synchronizing README and Dedicated Docs
**Learning:** Projects with both a comprehensive `README.md` and a dedicated `docs/` folder (like MkDocs) often suffer from synchronization drift. Features or CLI options added to the main README are frequently forgotten in the corresponding files in the `docs/` directory.
**Action:** When documenting a project with multiple doc sources, always cross-reference the main `README.md` against files in `docs/` (like `index.md` or `cli_usage.md`) to ensure feature lists and usage options are fully synchronized.
## 2025-05-19 - Using string literals for type hinting missing parameters
**Learning:** When adding type hints to undocumented functions without module-level imports, use string literals (e.g., `"numpy.ndarray"`) to avoid runtime `NameError` exceptions while satisfying the documentation builder (`mkdocs`). This was observed when adding hints to `_kovalevsky_scan` which caused `mkdocs build --strict` to fail until string literal hints were applied.
**Action:** When acting as Scribe to add type hints to undocumented inner or private functions, evaluate if the type module is imported globally. If not, use string-based forward references (`"type"`) to add the hint safely.

## 2025-05-19 - MkDocs Pygments Incompatibility
**Learning:** Building MkDocs documentation with the `mkdocstrings-python` plugin can fail with an obfuscated `AttributeError: 'NoneType' object has no attribute 'replace'` within Python's built-in `html.escape` function. This crash is triggered by an upstream regression in Pygments version 2.20.0 when formatting syntax-highlighted code blocks with missing optional file names.
**Action:** When adding or verifying MkDocs documentation for Python API modules, downgrade the `pygments` package to version `2.18.0` if build errors occur, and ensure all required type hints use string literals to avoid import crashes during documentation generation.

## 2025-05-19 - Documenting CLI Handler Functions
**Learning:** When documenting handler functions for CLI operations (like those in `src/image_converter/processing.py`), they often accept a generic `args` parameter representing parsed command-line arguments. Attempting to type hint this directly in the function signature (e.g., `args: argparse.Namespace`) can cause runtime errors if `argparse` is not explicitly imported in that module.
**Action:** When adding docstrings and type hints to handler functions, add the type hint for `args` (as `argparse.Namespace`) within the Google-style docstring itself, but omit it from the function signature unless the module already imports the required type, preventing unnecessary import overhead or runtime crashes.
