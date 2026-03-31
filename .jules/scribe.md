## 2025-05-15 - Pillow Type Hints for Generic Images
**Learning:** Using `ImageFile` as a generic type hint in Pillow causes confusion for tools expecting general image processing types, as `ImageFile` is actually a specific subclass used for lazy-loading image files, not the generic image object.
**Action:** When adding type hints to functions accepting Pillow images (like filters, resizing, background removal), always use `PIL.Image.Image` as the standard type hint for an image object unless specifically relying on the lazy-loading properties of `ImageFile`.

## 2025-05-18 - Type Hints on Inner Functions
**Learning:** When adding type hints to inner callback functions (like `validate` in `prompt_toolkit`), using string literals (e.g., `"prompt_toolkit.document.Document"`) for types that are not explicitly imported at the module level prevents `NameError` or `ImportError` runtime crashes while still providing valuable type information for documentation.
**Action:** Always use string literal type hints for complex objects or external library types that aren't already imported in the current module's scope, especially when documenting nested or inner functions.
