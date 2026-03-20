
## 2025-05-15 - Pillow Type Hints for Generic Images
**Learning:** Using `ImageFile` as a generic type hint in Pillow causes confusion for tools expecting general image processing types, as `ImageFile` is actually a specific subclass used for lazy-loading image files, not the generic image object.
**Action:** When adding type hints to functions accepting Pillow images (like filters, resizing, background removal), always use `PIL.Image.Image` as the standard type hint for an image object unless specifically relying on the lazy-loading properties of `ImageFile`.
