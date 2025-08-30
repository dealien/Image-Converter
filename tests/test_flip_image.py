import unittest
from PIL import Image
import sys
import os

# Add the parent directory to the path so we can import the flip_image module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flip_image import flip_image

class TestFlipImage(unittest.TestCase):

    def setUp(self):
        """Set up a dummy image for testing."""
        self.original_image = Image.new('RGB', (2, 2))
        self.pixels = {
            (0, 0): (255, 0, 0),    # Red
            (1, 0): (0, 255, 0),    # Green
            (0, 1): (0, 0, 255),    # Blue
            (1, 1): (255, 255, 255) # White
        }
        self.original_image.putdata([self.pixels[(x, y)] for y in range(2) for x in range(2)])

    def test_flip_horizontal(self):
        """Test flipping the image horizontally."""
        flipped_image = flip_image(self.original_image, 'horizontal')
        self.assertEqual(flipped_image.getpixel((0, 0)), self.pixels[(1, 0)]) # Green
        self.assertEqual(flipped_image.getpixel((1, 0)), self.pixels[(0, 0)]) # Red
        self.assertEqual(flipped_image.getpixel((0, 1)), self.pixels[(1, 1)]) # White
        self.assertEqual(flipped_image.getpixel((1, 1)), self.pixels[(0, 1)]) # Blue

    def test_flip_vertical(self):
        """Test flipping the image vertically."""
        flipped_image = flip_image(self.original_image, 'vertical')
        self.assertEqual(flipped_image.getpixel((0, 0)), self.pixels[(0, 1)]) # Blue
        self.assertEqual(flipped_image.getpixel((1, 0)), self.pixels[(1, 1)]) # White
        self.assertEqual(flipped_image.getpixel((0, 1)), self.pixels[(0, 0)]) # Red
        self.assertEqual(flipped_image.getpixel((1, 1)), self.pixels[(1, 0)]) # Green

    def test_flip_both(self):
        """Test flipping the image both horizontally and vertically."""
        flipped_image = flip_image(self.original_image, 'both')
        self.assertEqual(flipped_image.getpixel((0, 0)), self.pixels[(1, 1)]) # White
        self.assertEqual(flipped_image.getpixel((1, 0)), self.pixels[(0, 1)]) # Blue
        self.assertEqual(flipped_image.getpixel((0, 1)), self.pixels[(1, 0)]) # Green
        self.assertEqual(flipped_image.getpixel((1, 1)), self.pixels[(0, 0)]) # Red

    def test_invalid_direction(self):
        """Test that a ValueError is raised for an invalid flip direction."""
        with self.assertRaises(ValueError):
            flip_image(self.original_image, 'invalid_direction')

if __name__ == '__main__':
    unittest.main()
