import sys
import unittest
from unittest.mock import MagicMock

# Try to import Image; if it fails, we're in a restricted environment and should mock it
try:
    from PIL import Image
except ImportError:
    # Mock PIL.Image before importing scale_image
    mock_image = MagicMock()
    mock_image_file = MagicMock()
    sys.modules["PIL"] = MagicMock()
    sys.modules["PIL.Image"] = mock_image
    sys.modules["PIL.ImageFile"] = mock_image_file
    from PIL import Image

from image_converter.scale_image import scale_image  # noqa: E402


class TestScaleImageDoS(unittest.TestCase):
    def test_unbounded_scaling(self):
        # Create a small image (mock or real)
        if hasattr(Image, "new"):
            img = Image.new("RGB", (100, 100))
        else:
            # Fallback for extreme mock cases
            img = MagicMock()
            img.size = (100, 100)

        # Try to scale it to an extremely large size
        # 100 * 100000 = 10,000,000
        # (10^7 * 10^7) = 10^14 pixels.
        with self.assertRaises(ValueError) as cm:
            scale_image(img, scale_factor=1000000.0)

        self.assertIn("exceeds maximum allowed limit", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
