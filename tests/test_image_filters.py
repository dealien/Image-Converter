import unittest
import os
import random
from PIL import Image
from image_filters import invert_colors, grayscale, edge_detection
import numpy as np

class TestImageFilters(unittest.TestCase):
    def setUp(self):
        # Create a gradient image for testing
        self.test_image_path = 'tests/test_images/test_gradient.png'
        self.width, self.height = 256, 100
        self.image = Image.new('RGB', (self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                self.image.putpixel((x, y), (x, x, x))
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
        # Check a few random pixel values to see if they're inverted
        for _ in range(10):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            original_pixel = img.getpixel((x, y))
            inverted_pixel = inverted_img.getpixel((x, y))
            expected_inverted_pixel = tuple(255 - v for v in original_pixel)
            self.assertEqual(inverted_pixel, expected_inverted_pixel)

    def test_grayscale(self):
        # Load the image
        img = Image.open(self.test_image_path)
        # Convert to grayscale
        grayscale_img = grayscale(img)
        # Check the image mode
        self.assertEqual(grayscale_img.mode, 'L')
        # Check a few random pixel values
        for _ in range(10):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            original_pixel = img.getpixel((x, y))
            grayscale_pixel = grayscale_img.getpixel((x, y))
            # For a grayscale image, R=G=B, so the grayscale value is just the value of R.
            expected_grayscale = original_pixel[0]
            self.assertEqual(grayscale_pixel, expected_grayscale)

if __name__ == '__main__':
    unittest.main()


class TestEdgeDetection(unittest.TestCase):
    def setUp(self):
        # Create a simple image with a sharp vertical edge for testing
        self.test_image_path = 'tests/test_images/test_edge.png'
        self.width, self.height = 100, 100
        self.image = Image.new('RGB', (self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                color = (0, 0, 0) if x < self.width // 2 else (255, 255, 255)
                self.image.putpixel((x, y), color)
        self.image.save(self.test_image_path)

    def tearDown(self):
        # Remove the dummy image after tests
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_sobel_edge_detection(self):
        img = Image.open(self.test_image_path)
        edge_img = edge_detection(img, 'sobel')
        self.assertEqual(edge_img.mode, 'L')
        # The edge should be a bright line on a dark background.
        # We expect the brightest pixels to be around the center.
        edge_array = np.array(edge_img)
        # Check that the maximum value is high (edge is detected)
        self.assertGreater(np.max(edge_array), 150)
        # Check that the edge is roughly in the middle
        self.assertGreater(np.mean(edge_array[:, 48:52]), 80)
        # Check that the other areas are dark
        self.assertLess(np.mean(edge_array[:, :45]), 50)
        self.assertLess(np.mean(edge_array[:, 55:]), 50)

    def test_canny_edge_detection(self):
        img = Image.open(self.test_image_path)
        edge_img = edge_detection(img, 'canny')
        self.assertEqual(edge_img.mode, 'L')
        # Canny produces a binary image (0 or 255)
        edge_array = np.array(edge_img)
        self.assertTrue(np.all(np.logical_or(edge_array == 0, edge_array == 255)))
        # Check that there are some edge pixels
        self.assertGreater(np.sum(edge_array == 255), 50)
        # Check that the edge is roughly in the middle
        self.assertGreater(np.mean(edge_array[:, 49:51]), 200)

    def test_kovalevsky_edge_detection(self):
        # Create a very simple image for predictable results
        width, height = 10, 10
        img = Image.new('RGB', (width, height))
        for x in range(width):
            for y in range(height):
                # A sharp red-to-blue edge in the middle
                color = (255, 0, 0) if x < 5 else (0, 0, 255)
                img.putpixel((x, y), color)

        # Use a threshold that will definitely be triggered by this sharp edge
        edge_img = edge_detection(img, 'kovalevsky', threshold=100)
        self.assertEqual(edge_img.mode, 'L')
        edge_array = np.array(edge_img)

        # In the horizontal scan, an edge should be detected between col 4 and 5.
        # The window capturing this starts at x=2. The edge is marked at x+3, so at index 5.
        # Let's check a pixel in the middle row
        self.assertEqual(edge_array[5, 5], 255)
        # The vertical scan should not detect anything, as the color is constant vertically.
        # So we expect the rest of the image to be black.
        self.assertEqual(np.sum(edge_array == 255), height)
