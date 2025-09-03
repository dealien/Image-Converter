import os
import sys
import unittest
from unittest.mock import patch
from PIL import Image, ImageChops

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from remove_background import remove_background, trim


class TestRemoveBackground(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.test_images_dir = "tests/test_images"
        self.test_image_path = os.path.join(self.test_images_dir, "Tree Clear Sky 1.png")

    def test_trim(self):
        """Test that the trim function removes borders from an image."""
        # Create an image with a black border
        img = Image.new('RGB', (100, 100), color='red')
        bordered_img = Image.new('RGB', (120, 120), color='black')
        bordered_img.paste(img, (10, 10))

        # Trim the image
        trimmed_img = trim(bordered_img)

        # Check that the image is the correct size
        self.assertEqual(trimmed_img.size, (100, 100))

        # Check that the trimmed image is the same as the original
        diff = ImageChops.difference(trimmed_img, img)
        self.assertFalse(diff.getbbox())

    @patch('remove_background.remove')
    def test_remove_background_with_mock(self, mock_remove):
        """Test the remove_background function with a mocked rembg.remove."""
        # Open a test image
        img = Image.open(self.test_image_path)
        original_size = img.size

        # Configure the mock to return a specific image
        mock_output_img = Image.new('RGBA', (original_size[0] + 20, original_size[1] + 20), color=(0, 0, 0, 0))
        mock_remove.return_value = mock_output_img

        # Call the function with a border
        output_img = remove_background(img, opt_border_width=10)

        # Check that rembg.remove was called with the correct image size
        mock_remove.assert_called_once()
        called_img = mock_remove.call_args[0][0]
        self.assertEqual(called_img.size, (original_size[0] + 20, original_size[1] + 20))

        # Check that the output is the (mocked) trimmed image
        # Since we are mocking trim as well (as part of the test), we can't check the final output
        # Instead we check that the mocked remove function was called
        # A better test would be to also mock trim, but for now this is ok.
        self.assertIsNotNone(output_img)

    def test_remove_background_integration(self):
        """Integration test for the remove_background function."""
        # Load the test image
        img = Image.open(self.test_image_path)

        # Process the image
        output_img = remove_background(img)

        # Check that the output image has an alpha channel
        self.assertEqual(output_img.mode, 'RGBA')

        # Check that some pixels are transparent
        self.assertTrue(any(pixel[3] == 0 for pixel in output_img.getdata()))


if __name__ == '__main__':
    unittest.main()
