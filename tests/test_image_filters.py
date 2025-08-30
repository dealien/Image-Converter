import unittest
import os
from PIL import Image
from image_filters import invert_colors, grayscale

class TestImageFilters(unittest.TestCase):
    def setUp(self):
        # Create a dummy image for testing
        self.test_image_path = 'tests/test_images/test_image.png'
        self.image = Image.new('RGB', (100, 100), color = 'red')
        self.image.save(self.test_image_path)

    def tearDown(self):
        # Remove the dummy image after tests
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_invert_colors(self):
        # Load the image
        img = Image.open(self.test_image_path)
        # Invert the colors
        inverted_img = invert_colors(img)
        # Check a pixel value to see if it's inverted
        # Red (255, 0, 0) should become Cyan (0, 255, 255)
        inverted_pixel = inverted_img.getpixel((50, 50))
        self.assertEqual(inverted_pixel, (0, 255, 255))

    def test_grayscale(self):
        # Load the image
        img = Image.open(self.test_image_path)
        # Convert to grayscale
        grayscale_img = grayscale(img)
        # Check the image mode
        self.assertEqual(grayscale_img.mode, 'L')
        # Check a pixel value to see if it's grayscale
        # Red (255, 0, 0) should become a shade of gray
        # Using the standard formula: 0.299*R + 0.587*G + 0.114*B
        # 0.299*255 + 0.587*0 + 0.114*0 = 76.245, which rounds to 76
        grayscale_pixel = grayscale_img.getpixel((50, 50))
        self.assertEqual(grayscale_pixel, 76)

if __name__ == '__main__':
    unittest.main()
