## 2026-03-20 - Edge Cases and Fast Paths in PIL Image Processing
**Learning:** Certain Pillow `ImageEnhance` operations and edge detection methods have specific mathematical and boundary constraints (e.g., Kovalevsky requiring >= 6x6 pixel images to perform 5-pixel comparison window diffs, or alpha channels being preserved via manual fast paths in RGBA modes).
**Action:** When adding test coverage to image processing functions, always include edge cases for extreme input dimensions (small images, zero values) and test multi-channel preservation (RGBA) specifically on optimization fast-paths.
