import unittest
import os
import random
from PIL import Image
from image_filters import (invert_colors, grayscale, edge_detection,
                           adjust_brightness, adjust_contrast, adjust_saturation,
                           apply_blur, apply_sharpen,
                           apply_color_balance, rotate_hue, apply_posterize)


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


class TestImageAdjustments(unittest.TestCase):
    def setUp(self):
        # Create a simple gradient image for testing
        self.test_image = Image.new('RGB', (100, 100))
        for x in range(100):
            for y in range(100):
                self.test_image.putpixel((x, y), (x, int(y / 2), 128))

    def test_adjust_brightness(self):
        # Test brightening
        brightened_image = adjust_brightness(self.test_image, 50)
        original_pixel = self.test_image.getpixel((50, 50))
        brightened_pixel = brightened_image.getpixel((50, 50))
        self.assertGreater(brightened_pixel[0], original_pixel[0])

        # Test darkening
        darkened_image = adjust_brightness(self.test_image, -50)
        darkened_pixel = darkened_image.getpixel((50, 50))
        self.assertLess(darkened_pixel[0], original_pixel[0])

        # Test no change
        same_image = adjust_brightness(self.test_image, 0)
        same_pixel = same_image.getpixel((50, 50))
        self.assertEqual(same_pixel, original_pixel)

        # Test invalid values
        with self.assertRaises(ValueError):
            adjust_brightness(self.test_image, 101)
        with self.assertRaises(ValueError):
            adjust_brightness(self.test_image, -101)
        with self.assertRaises(TypeError):
            adjust_brightness(self.test_image, "invalid")
        with self.assertRaises(TypeError):
            adjust_brightness(self.test_image, 50.5)
        with self.assertRaises(TypeError):
            adjust_brightness(self.test_image, [50])
        with self.assertRaises(TypeError):
            adjust_brightness(self.test_image, {"value": 50})
        with self.assertRaises(TypeError):
            adjust_brightness(self.test_image, None)

    def test_adjust_contrast(self):
        # Test increasing contrast
        contrasted_image = adjust_contrast(self.test_image, 50)
        original_pixel_1 = self.test_image.getpixel((25, 25))
        original_pixel_2 = self.test_image.getpixel((75, 75))
        contrasted_pixel_1 = contrasted_image.getpixel((25, 25))
        contrasted_pixel_2 = contrasted_image.getpixel((75, 75))
        # With increased contrast, darker pixels get darker and lighter pixels get lighter
        self.assertLess(contrasted_pixel_1[0], original_pixel_1[0])
        self.assertGreater(contrasted_pixel_2[0], original_pixel_2[0])

        # Test decreasing contrast
        decontrasted_image = adjust_contrast(self.test_image, -50)
        decontrasted_pixel_1 = decontrasted_image.getpixel((25, 25))
        decontrasted_pixel_2 = decontrasted_image.getpixel((75, 75))
        # With decreased contrast, the difference between pixels should be smaller
        self.assertGreater(decontrasted_pixel_1[0], original_pixel_1[0])
        self.assertLess(decontrasted_pixel_2[0], original_pixel_2[0])

        # Test no change
        same_image = adjust_contrast(self.test_image, 0)
        self.assertEqual(list(same_image.getdata()), list(self.test_image.getdata()))

        # Test invalid values
        with self.assertRaises(ValueError):
            adjust_contrast(self.test_image, 101)
        with self.assertRaises(ValueError):
            adjust_contrast(self.test_image, -101)
        with self.assertRaises(TypeError):
            adjust_contrast(self.test_image, "invalid")
        with self.assertRaises(TypeError):
            adjust_contrast(self.test_image, 50.5)
        with self.assertRaises(TypeError):
            adjust_contrast(self.test_image, [50])
        with self.assertRaises(TypeError):
            adjust_contrast(self.test_image, {"value": 50})
        with self.assertRaises(TypeError):
            adjust_contrast(self.test_image, None)

    def test_adjust_saturation(self):
        # Test increasing saturation
        saturated_image = adjust_saturation(self.test_image, 50)
        original_pixel = self.test_image.getpixel((50, 50))
        saturated_pixel = saturated_image.getpixel((50, 50))
        # Saturation increases the difference between R, G, B values
        self.assertGreater(abs(saturated_pixel[0] - saturated_pixel[1]), abs(original_pixel[0] - original_pixel[1]))

        # Test decreasing saturation
        desaturated_image = adjust_saturation(self.test_image, -50)
        desaturated_pixel = desaturated_image.getpixel((50, 50))
        # Saturation decreases the difference between R, G, B values
        self.assertLess(abs(desaturated_pixel[0] - desaturated_pixel[1]), abs(original_pixel[0] - original_pixel[1]))

        # Test no change
        same_image = adjust_saturation(self.test_image, 0)
        self.assertEqual(list(same_image.getdata()), list(self.test_image.getdata()))

        # Test invalid values
        with self.assertRaises(ValueError):
            adjust_saturation(self.test_image, 101)
        with self.assertRaises(ValueError):
            adjust_saturation(self.test_image, -101)
        with self.assertRaises(TypeError):
            adjust_saturation(self.test_image, "invalid")
        with self.assertRaises(TypeError):
            adjust_saturation(self.test_image, 50.5)
        with self.assertRaises(TypeError):
            adjust_saturation(self.test_image, [50])
        with self.assertRaises(TypeError):
            adjust_saturation(self.test_image, {"value": 50})
        with self.assertRaises(TypeError):
            adjust_saturation(self.test_image, None)

    def test_adjust_saturation_rgba(self):
        # Create an RGBA image for testing
        rgba_image = self.test_image.copy().convert("RGBA")
        # Set a semi-transparent alpha channel
        alpha = Image.new('L', rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        # Adjust saturation
        saturated_image = adjust_saturation(rgba_image, 50)

        # Check that the image is still RGBA
        self.assertEqual(saturated_image.mode, 'RGBA')

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = saturated_image.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))


class TestImageBlurAndSharpen(unittest.TestCase):
    def setUp(self):
        # Create a simple image with a checkboard pattern (high frequency/contrast)
        self.width, self.height = 100, 100
        self.test_image = Image.new('RGB', (self.width, self.height))
        for x in range(self.width):
            for y in range(self.height):
                if (x // 10 + y // 10) % 2 == 0:
                    self.test_image.putpixel((x, y), (0, 0, 0))
                else:
                    self.test_image.putpixel((x, y), (255, 255, 255))

    def test_apply_blur(self):
        # Apply blur
        blurred_image = apply_blur(self.test_image, radius=2)
        
        # Check that sharp edges are softened
        # In the original image, pixel (9, 0) is black (0,0,0) and (10, 0) is white (255,255,255)
        # After blur, they should be closer in value.
        p1 = blurred_image.getpixel((9, 0))[0]
        p2 = blurred_image.getpixel((10, 0))[0]
        diff = abs(p1 - p2)
        # Original difference is 255. Blurred diff should be significantly less.
        self.assertLess(diff, 200)

        # Test invalid values
        with self.assertRaises(TypeError):
            apply_blur(self.test_image, "invalid")
        with self.assertRaises(ValueError):
            apply_blur(self.test_image, -1)

    def test_apply_sharpen(self):
        # Create a blurry image to sharpen
        blurry_image = apply_blur(self.test_image, radius=1)

        
        # Apply sharpen
        sharpened_image = apply_sharpen(blurry_image, sharpness=100)
        
        # Measure local contrast at an edge
        # We expect the contrast to increase after sharpening
        p1_blur = blurry_image.getpixel((9, 0))[0]
        p2_blur = blurry_image.getpixel((10, 0))[0]
        
        # Calculate total horizontal gradient (sum of absolute differences)
        def calculate_horizontal_gradient(img):
            data = list(img.getdata())
            width, height = img.size
            total_gradient = 0
            for y in range(height):
                row_start = y * width
                for x in range(width - 1):
                    p1 = data[row_start + x][0]
                    p2 = data[row_start + x + 1][0]
                    total_gradient += abs(p1 - p2)
            return total_gradient

        blur_gradient = calculate_horizontal_gradient(blurry_image)
        sharp_gradient = calculate_horizontal_gradient(sharpened_image)
        
        self.assertGreater(sharp_gradient, blur_gradient)


class TestImageColorOps(unittest.TestCase):
    def setUp(self):
         self.width, self.height = 100, 100
         self.test_image = Image.new('RGB', (self.width, self.height), (100, 100, 100))
         
    def test_color_balance(self):
        # Enhance Red
        red_enhanced = apply_color_balance(self.test_image, 2.0, 1.0, 1.0)
        self.assertEqual(red_enhanced.getpixel((0,0)), (200, 100, 100))
        
        # Suppress Blue
        blue_suppressed = apply_color_balance(self.test_image, 1.0, 1.0, 0.5)
        self.assertEqual(blue_suppressed.getpixel((0,0)), (100, 100, 50))
        
        # Test invalid values
        with self.assertRaises(TypeError):
            apply_color_balance(self.test_image, "a", 1, 1)
        with self.assertRaises(ValueError):
             apply_color_balance(self.test_image, -1, 1, 1)

    def test_posterize(self):
        # Create a gradient image
        img = Image.new('RGB', (256, 1))
        for x in range(256):
            img.putpixel((x, 0), (x, x, x))
            
        posterized = apply_posterize(img, bits=1) # Reduce to 1 bit (2 levels per channel)
        
        unique_colors = len(set(posterized.getdata()))
        self.assertLess(unique_colors, 10) # Should be very few colors (actually 2^3=8 max for full RGB, but 2 for grayscale-ish)

        with self.assertRaises(ValueError):
             apply_posterize(img, 9)
        with self.assertRaises(ValueError):
             apply_posterize(img, 0)

    def test_hue_rotation(self):
        # Create a pure red image
        red_img = Image.new('RGB', (10, 10), (255, 0, 0))
        
        # Rotate 120 degrees -> Green
        green_img = rotate_hue(red_img, 120)
        pixel = green_img.getpixel((0,0))
        # Hue rotation isn't perfectly precise with 8-bit HSV, but red->green should have dominant G
        self.assertGreater(pixel[1], pixel[0]) 
        self.assertGreater(pixel[1], pixel[2])

        # Rotate 240 degrees -> Blue
        blue_img = rotate_hue(red_img, 240)
        pixel = blue_img.getpixel((0,0))
        self.assertGreater(pixel[2], pixel[0])
        self.assertGreater(pixel[2], pixel[1])

    def test_hue_rotation_preserves_alpha(self):
        # Create an RGBA image with transparency
        rgba_img = Image.new('RGBA', (10, 10), (255, 0, 0, 128))
        
        # Rotate hue
        rotated_img = rotate_hue(rgba_img, 90)
        
        # Check if alpha is preserved
        self.assertEqual(rotated_img.mode, 'RGBA')
        self.assertEqual(rotated_img.getpixel((0,0))[3], 128)







        # Test invalid values
        with self.assertRaises(TypeError):
            apply_sharpen(self.test_image, "invalid")
        with self.assertRaises(ValueError):
            apply_sharpen(self.test_image, -1)
        with self.assertRaises(ValueError):
            apply_sharpen(self.test_image, 101)

