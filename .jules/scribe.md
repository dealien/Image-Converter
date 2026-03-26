
## 2025-05-15 - Pillow Type Hints for Generic Images
**Learning:** Using `ImageFile` as a generic type hint in Pillow causes confusion for tools expecting general image processing types, as `ImageFile` is actually a specific subclass used for lazy-loading image files, not the generic image object.
**Action:** When adding type hints to functions accepting Pillow images (like filters, resizing, background removal), always use `PIL.Image.Image` as the standard type hint for an image object unless specifically relying on the lazy-loading properties of `ImageFile`.

## 2025-05-15 - Docstring Formatting & Line Limits
**Learning:** While automatically fixing PEP 257 (D401) imperative mood violations across the entire codebase is useful for linting, it easily exceeds the strict 50-line limit for Scribe tasks and is considered too "mechanical" compared to Scribe's goal of illuminating complex or undocumented logic ("Dark Matter").
**Action:** In the future, prioritize documenting single, complex, and undocumented functions, classes, or adding meaningful module-level docstrings, rather than bulk grammatical fixes across multiple files to stay within the 50-line limit and provide higher-value documentation.
