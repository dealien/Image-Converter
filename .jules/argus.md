## 2024-11-20 - Unreachable code in orthogonal image rotation
**Learning:** `rotate_image` has a dead code path `return image.rotate(clamped_angle, expand=True)` because `clamped_angle = int(round(angle / 90.0)) * 90 % 360` enforces values of 0, 90, 180, and 270 exclusively, and these exact values are handled efficiently by transposing.

**Action:** Note that 100% line coverage here is impossible without altering the code or removing the dead branch. No further action to cover it via testing, but future contributors could be aware.
