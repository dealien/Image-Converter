import unittest
from PIL import Image
import sys
import os

# Add the parent directory to the path so we can import the scale_image module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scale_image import scale_image, RESAMPLE_FILTERS


class TestScaleImage(unittest.TestCase):

    def setUp(self):
        """Set up a dummy image for testing."""
        self.original_image = Image.new('RGB', (200, 100))

    def test_scale_by_factor(self):
        """Test scaling the image by a given factor."""
        scaled_image = scale_image(self.original_image, scale_factor=1.5)
        self.assertEqual(scaled_image.size, (300, 150))

    def test_scale_to_fit_bounding_box(self):
        """Test scaling the image to fit within a bounding box, preserving aspect ratio."""
        # Bounding box where width is the limiting dimension
        scaled_image_1 = scale_image(self.original_image, new_size=(80, 60))
        self.assertEqual(scaled_image_1.size, (80, 40))

        # Bounding box where height is the limiting dimension
        scaled_image_2 = scale_image(self.original_image, new_size=(150, 50))
        self.assertEqual(scaled_image_2.size, (100, 50))

    def test_no_scaling_params(self):
        """Test that the image size does not change if no scaling parameters are provided."""
        scaled_image = scale_image(self.original_image)
        self.assertEqual(scaled_image.size, self.original_image.size)

    def test_invalid_resample_filter(self):
        """Test that a ValueError is raised for an invalid resample filter."""
        with self.assertRaises(ValueError):
            scale_image(self.original_image, scale_factor=0.5, resample_filter="invalid_filter")

    def test_all_resample_filters(self):
        """Test that all supported resample filters work without error."""
        for filter_name in RESAMPLE_FILTERS.keys():
            with self.subTest(filter=filter_name):
                try:
                    scale_image(self.original_image, scale_factor=0.5, resample_filter=filter_name)
                except Exception as e:
                    self.fail(f"scale_image failed with filter '{filter_name}': {e}")


if __name__ == '__main__':
    unittest.main()
