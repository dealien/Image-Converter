import unittest
import importlib


class TestSecurityLimits(unittest.TestCase):
    def test_max_image_pixels_setting(self):
        """Test that PIL.Image.MAX_IMAGE_PIXELS is set to a safe limit."""
        import PIL.Image

        PIL.Image.MAX_IMAGE_PIXELS = 0  # reset

        # Importing will set it
        import image_converter.rich_menu

        importlib.reload(image_converter.rich_menu)

        self.assertEqual(PIL.Image.MAX_IMAGE_PIXELS, 100000000)

        PIL.Image.MAX_IMAGE_PIXELS = 0
        import image_converter.processing

        importlib.reload(image_converter.processing)
        self.assertEqual(PIL.Image.MAX_IMAGE_PIXELS, 100000000)


if __name__ == "__main__":
    unittest.main()
