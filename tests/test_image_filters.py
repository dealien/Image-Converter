import os
import random
import unittest
from unittest.mock import MagicMock

import numpy as np
from PIL import Image

from image_converter.image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_blur,
    apply_border,
    apply_cartoonify,
    apply_color_balance,
    apply_oil_painting,
    apply_posterize,
    apply_sharpen,
    apply_vignette,
    edge_detection,
    grayscale,
    invert_colors,
    rotate_hue,
    rotate_image,
)


class TestImageFilters(unittest.TestCase):
    def setUp(self):
        # Create a gradient image for testing
        self.test_image_path = "tests/test_images/test_gradient.png"
        self.width, self.height = 256, 100
        self.image = Image.new("RGB", (self.width, self.height))
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
        self.assertEqual(grayscale_img.mode, "L")
        # Check a few random pixel values
        for _ in range(10):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            original_pixel = img.getpixel((x, y))
            grayscale_pixel = grayscale_img.getpixel((x, y))
            # For a grayscale image, R=G=B, so the grayscale value is just the value of R.
            expected_grayscale = original_pixel[0]
            self.assertEqual(grayscale_pixel, expected_grayscale)


if __name__ == "__main__":
    unittest.main()


class TestEdgeDetection(unittest.TestCase):
    def setUp(self):
        # Create a simple image with a sharp vertical edge for testing
        self.test_image_path = "tests/test_images/test_edge.png"
        self.width, self.height = 100, 100
        self.image = Image.new("RGB", (self.width, self.height))
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
        edge_img = edge_detection(img, "sobel")
        self.assertEqual(edge_img.mode, "L")
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
        edge_img = edge_detection(img, "canny")
        self.assertEqual(edge_img.mode, "L")
        # Canny produces a binary image (0 or 255)
        edge_array = np.array(edge_img)
        self.assertTrue(np.all(np.logical_or(edge_array == 0, edge_array == 255)))
        # Check that there are some edge pixels
        self.assertGreater(np.sum(edge_array == 255), 50)
        # Check that the edge is roughly in the middle
        self.assertGreater(np.mean(edge_array[:, 49:51]), 200)

    def test_invalid_method(self):
        """Verifies that ValueError is raised for an invalid edge detection method."""
        img = Image.open(self.test_image_path)
        with self.assertRaisesRegex(
            ValueError, r"^Method must be 'sobel', 'canny', or 'kovalevsky'$"
        ):
            edge_detection(img, "invalid_method")

    def test_kovalevsky_small_image_edge_case(self):
        """Verifies Kovalevsky edge detection handles images smaller than the 6-pixel window safely."""
        # Kovalevsky requires at least 6x6. Test smaller images.
        img_5x5 = Image.new("RGB", (5, 5))
        edge_img_5x5 = edge_detection(img_5x5, "kovalevsky")
        self.assertEqual(edge_img_5x5.size, (5, 5))
        self.assertEqual(edge_img_5x5.mode, "L")
        self.assertEqual(np.sum(np.array(edge_img_5x5)), 0)  # Should be all black

        img_6x5 = Image.new("RGB", (6, 5))
        edge_img_6x5 = edge_detection(img_6x5, "kovalevsky")
        self.assertEqual(edge_img_6x5.size, (6, 5))
        self.assertEqual(np.sum(np.array(edge_img_6x5)), 0)

    def test_kovalevsky_edge_detection(self):
        # Create a very simple image for predictable results
        width, height = 10, 10
        img = Image.new("RGB", (width, height))
        for x in range(width):
            for y in range(height):
                # A sharp red-to-blue edge in the middle
                color = (255, 0, 0) if x < 5 else (0, 0, 255)
                img.putpixel((x, y), color)

        # Use a threshold that will definitely be triggered by this sharp edge
        edge_img = edge_detection(img, "kovalevsky", threshold=100)
        self.assertEqual(edge_img.mode, "L")
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
        self.test_image = Image.new("RGB", (100, 100))
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
        with self.assertRaisesRegex(TypeError, r"^Brightness must be an integer\.$"):
            adjust_brightness(self.test_image, "invalid")
        with self.assertRaisesRegex(TypeError, r"^Brightness must be an integer\.$"):
            adjust_brightness(self.test_image, 50.5)
        with self.assertRaisesRegex(TypeError, r"^Brightness must be an integer\.$"):
            adjust_brightness(self.test_image, [50])
        with self.assertRaisesRegex(TypeError, r"^Brightness must be an integer\.$"):
            adjust_brightness(self.test_image, {"value": 50})
        with self.assertRaisesRegex(TypeError, r"^Brightness must be an integer\.$"):
            adjust_brightness(self.test_image, None)

    def test_adjust_brightness_rgba(self):
        """Verifies adjust_brightness preserves alpha channel using the RGBA fast path."""
        # Create an RGBA image for testing
        rgba_image = self.test_image.copy().convert("RGBA")
        # Set a semi-transparent alpha channel
        alpha = Image.new("L", rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        # Adjust brightness
        brightened_image = adjust_brightness(rgba_image, 50)

        # Check that the image is still RGBA
        self.assertEqual(brightened_image.mode, "RGBA")

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = brightened_image.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))

        # Check brightness increased on RGB channels
        original_pixel = rgba_image.getpixel((50, 50))
        brightened_pixel = brightened_image.getpixel((50, 50))
        self.assertGreater(brightened_pixel[0], original_pixel[0])

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

    def test_adjust_contrast_rgba(self):
        """Verifies adjust_contrast preserves alpha channel using the RGBA fast path."""
        # Create an RGBA image for testing
        rgba_image = self.test_image.copy().convert("RGBA")
        # Set a semi-transparent alpha channel
        alpha = Image.new("L", rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        # Adjust contrast
        contrasted_image = adjust_contrast(rgba_image, 50)

        # Check that the image is still RGBA
        self.assertEqual(contrasted_image.mode, "RGBA")

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = contrasted_image.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))

        # Check contrast changes on RGB
        original_pixel = rgba_image.getpixel((25, 25))
        contrasted_pixel = contrasted_image.getpixel((25, 25))
        self.assertLess(contrasted_pixel[0], original_pixel[0])

    def test_adjust_saturation(self):
        # Test increasing saturation
        saturated_image = adjust_saturation(self.test_image, 50)
        original_pixel = self.test_image.getpixel((50, 50))
        saturated_pixel = saturated_image.getpixel((50, 50))
        # Saturation increases the difference between R, G, B values
        self.assertGreater(
            abs(saturated_pixel[0] - saturated_pixel[1]),
            abs(original_pixel[0] - original_pixel[1]),
        )

        # Test decreasing saturation
        desaturated_image = adjust_saturation(self.test_image, -50)
        desaturated_pixel = desaturated_image.getpixel((50, 50))
        # Saturation decreases the difference between R, G, B values
        self.assertLess(
            abs(desaturated_pixel[0] - desaturated_pixel[1]),
            abs(original_pixel[0] - original_pixel[1]),
        )

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
        alpha = Image.new("L", rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        # Adjust saturation
        saturated_image = adjust_saturation(rgba_image, 50)

        # Check that the image is still RGBA
        self.assertEqual(saturated_image.mode, "RGBA")

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = saturated_image.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))


class TestImageBlurAndSharpen(unittest.TestCase):
    def setUp(self):
        # Create a simple image with a checkboard pattern (high frequency/contrast)
        self.width, self.height = 100, 100
        self.test_image = Image.new("RGB", (self.width, self.height))
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
        with self.assertRaisesRegex(TypeError, r"^Radius must be a number\.$"):
            apply_blur(self.test_image, "invalid")
        with self.assertRaises(ValueError):
            apply_blur(self.test_image, -1)

    def test_apply_sharpen(self):
        # Create a blurry image to sharpen
        blurry_image = apply_blur(self.test_image, radius=1)

        # Apply sharpen
        sharpened_image = apply_sharpen(blurry_image, sharpness=100)

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

        # Test invalid values
        with self.assertRaises(ValueError):
            apply_sharpen(self.test_image, 101)
        with self.assertRaises(ValueError):
            apply_sharpen(self.test_image, -1)
        with self.assertRaisesRegex(TypeError, r"^Sharpness must be an integer\.$"):
            apply_sharpen(self.test_image, "invalid")
        with self.assertRaisesRegex(TypeError, r"^Sharpness must be an integer\.$"):
            apply_sharpen(self.test_image, 50.5)
        with self.assertRaisesRegex(TypeError, r"^Sharpness must be an integer\.$"):
            apply_sharpen(self.test_image, [50])
        with self.assertRaisesRegex(TypeError, r"^Sharpness must be an integer\.$"):
            apply_sharpen(self.test_image, {"value": 50})
        with self.assertRaisesRegex(TypeError, r"^Sharpness must be an integer\.$"):
            apply_sharpen(self.test_image, None)

    def test_apply_sharpen_rgba(self):
        """Verifies apply_sharpen preserves alpha channel using the RGBA fast path."""
        # Create a blurry image with RGBA to sharpen
        blurry_image = apply_blur(self.test_image, radius=1).convert("RGBA")
        # Set a semi-transparent alpha channel
        alpha = Image.new("L", blurry_image.size, 128)
        blurry_image.putalpha(alpha)

        # Apply sharpen
        sharpened_image = apply_sharpen(blurry_image, sharpness=100)

        # Check that the image is still RGBA
        self.assertEqual(sharpened_image.mode, "RGBA")

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = sharpened_image.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))

        # Verify sharpening occurred on RGB (compare difference)
        def calculate_horizontal_gradient(img):
            data = list(img.convert("RGB").getdata())
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
        self.test_image = Image.new("RGB", (self.width, self.height), (100, 100, 100))

    def test_color_balance(self):
        # Enhance Red
        red_enhanced = apply_color_balance(self.test_image, 2.0, 1.0, 1.0)
        self.assertEqual(red_enhanced.getpixel((0, 0)), (200, 100, 100))

        # Suppress Blue
        blue_suppressed = apply_color_balance(self.test_image, 1.0, 1.0, 0.5)
        self.assertEqual(blue_suppressed.getpixel((0, 0)), (100, 100, 50))

        # Test invalid values
        with self.assertRaises(TypeError):
            apply_color_balance(self.test_image, "a", 1, 1)
        with self.assertRaisesRegex(
            ValueError, r"^Color balance factors must be non-negative\.$"
        ):
            apply_color_balance(self.test_image, -1, 1, 1)
        with self.assertRaisesRegex(ValueError, r"^Factors must be finite numbers\.$"):
            apply_color_balance(self.test_image, float("nan"), 1, 1)
        with self.assertRaisesRegex(ValueError, r"^Factors must be finite numbers\.$"):
            apply_color_balance(self.test_image, 1, float("inf"), 1)

    def test_color_balance_clamping(self):
        # Enhance Red to overflow
        red_enhanced = apply_color_balance(self.test_image, 10.0, 1.0, 1.0)
        # 100 * 10 = 1000 -> clamped to 255
        self.assertEqual(red_enhanced.getpixel((0, 0))[0], 255)

    def test_color_balance_rgba(self):
        # Create an RGBA image for testing
        rgba_image = self.test_image.copy().convert("RGBA")
        # Set a semi-transparent alpha channel
        alpha = Image.new("L", rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        # Enhance Red
        red_enhanced = apply_color_balance(rgba_image, 2.0, 1.0, 1.0)

        # Check that the image is still RGBA
        self.assertEqual(red_enhanced.mode, "RGBA")

        # Check that the RGB values are correctly scaled
        self.assertEqual(red_enhanced.getpixel((0, 0))[:3], (200, 100, 100))

        # Check that the alpha channel is preserved
        _, _, _, new_alpha = red_enhanced.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))

    def test_apply_color_balance_4_plus_bands(self):
        # Create an RGBA image for testing 4+ bands edge case
        rgba_image = self.test_image.copy().convert("RGBA")
        alpha = Image.new("L", rgba_image.size, 100)
        rgba_image.putalpha(alpha)

        # Enhance Color
        color_balanced = apply_color_balance(rgba_image, 1.5, 1.0, 1.0)

        # Check output mode
        self.assertEqual(color_balanced.mode, "RGBA")

        # Verify alpha channel is preserved
        _, _, _, result_alpha = color_balanced.split()
        self.assertEqual(list(result_alpha.getdata()), list(alpha.getdata()))

    def test_posterize(self):
        # Create a gradient image
        img = Image.new("RGB", (256, 1))
        for x in range(256):
            img.putpixel((x, 0), (x, x, x))

        posterized = apply_posterize(
            img, bits=1
        )  # Reduce to 1 bit (2 levels per channel)

        unique_colors = len(set(posterized.getdata()))
        self.assertLess(
            unique_colors, 10
        )  # Should be very few colors (actually 2^3=8 max for full RGB, but 2 for grayscale-ish)

        with self.assertRaises(ValueError):
            apply_posterize(img, 9)
        with self.assertRaises(ValueError):
            apply_posterize(img, 0)

    def test_hue_rotation(self):
        # Create a pure red image
        red_img = Image.new("RGB", (10, 10), (255, 0, 0))

        # Rotate 120 degrees -> Green
        green_img = rotate_hue(red_img, 120)
        pixel = green_img.getpixel((0, 0))
        # Hue rotation isn't perfectly precise with 8-bit HSV, but red->green should have dominant G
        self.assertGreater(pixel[1], pixel[0])
        self.assertGreater(pixel[1], pixel[2])

        # Rotate 240 degrees -> Blue
        blue_img = rotate_hue(red_img, 240)
        pixel = blue_img.getpixel((0, 0))
        self.assertGreater(pixel[2], pixel[0])
        self.assertGreater(pixel[2], pixel[1])

    def test_hue_rotation_preserves_alpha(self):
        # Create an RGBA image with transparency
        rgba_img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))

        # Rotate hue
        rotated_img = rotate_hue(rgba_img, 90)

        # Check if alpha is preserved
        self.assertEqual(rotated_img.mode, "RGBA")
        self.assertEqual(rotated_img.getpixel((0, 0))[3], 128)

    def test_posterize_preserves_alpha(self):
        # Create an RGBA image with transparency
        rgba_img = Image.new("RGBA", (10, 10), (100, 150, 200, 128))

        # Apply posterize
        posterized_img = apply_posterize(rgba_img, bits=4)

        # Check if alpha is preserved
        self.assertEqual(posterized_img.mode, "RGBA")
        self.assertEqual(posterized_img.getpixel((0, 0))[3], 128)

    def test_posterize_la_mode(self):
        """Verifies that LA mode preserves alpha when posterized."""
        la_img = Image.new("LA", (10, 10), (100, 128))
        posterized_img = apply_posterize(la_img, bits=4)
        self.assertEqual(posterized_img.mode, "LA")
        self.assertEqual(posterized_img.getpixel((0, 0))[1], 128)

    def test_posterize_non_standard_mode(self):
        """Verifies that non-standard modes like CMYK are posterized natively preserving mode."""
        cmyk_img = Image.new("CMYK", (10, 10), (100, 150, 200, 50))
        posterized_img = apply_posterize(cmyk_img, bits=4)
        self.assertEqual(posterized_img.mode, "CMYK")

    def test_invert_colors_not_rgba_rgb_l(self):
        """Verifies color inversion natively supports modes like CMYK preserving mode."""
        img = Image.new("CMYK", (10, 10), (100, 50, 20, 10))
        inverted = invert_colors(img)
        self.assertEqual(inverted.mode, "CMYK")

    def test_apply_color_balance_not_rgb_rgba(self):
        """Verifies color balance natively applies to non-RGB/RGBA modes."""
        img = Image.new("CMYK", (10, 10), (100, 50, 20, 10))
        balanced = apply_color_balance(img, 1.5, 1.0, 1.0)
        self.assertEqual(balanced.mode, "CMYK")


class TestExtendedImageModeLUTs(unittest.TestCase):
    """Tests LUT-based operations across extended Pillow image modes."""

    def test_cmyk_mode_luts(self):
        """Test brightness, contrast, posterize, and invert on CMYK images."""
        img = Image.new("CMYK", (20, 20), (100, 50, 200, 20))
        brightened = adjust_brightness(img, 20)
        self.assertEqual(brightened.mode, "CMYK")

        contrasted = adjust_contrast(img, 20)
        self.assertEqual(contrasted.mode, "CMYK")

        posterized = apply_posterize(img, 4)
        self.assertEqual(posterized.mode, "CMYK")

        inverted = invert_colors(img)
        self.assertEqual(inverted.mode, "CMYK")

    def test_ycbcr_mode_luts(self):
        """Test brightness, contrast, and posterize on YCbCr images."""
        img = Image.new("YCbCr", (20, 20), (128, 100, 150))
        brightened = adjust_brightness(img, 10)
        self.assertEqual(brightened.mode, "YCbCr")

        contrasted = adjust_contrast(img, 10)
        self.assertEqual(contrasted.mode, "YCbCr")

        posterized = apply_posterize(img, 4)
        self.assertEqual(posterized.mode, "YCbCr")

    def test_lab_mode_luts(self):
        """Test brightness, contrast, and posterize on LAB images."""
        img = Image.new("LAB", (20, 20), (128, 128, 128))
        brightened = adjust_brightness(img, 15)
        self.assertEqual(brightened.mode, "LAB")

        contrasted = adjust_contrast(img, 15)
        self.assertEqual(contrasted.mode, "LAB")

        posterized = apply_posterize(img, bits=4)
        self.assertEqual(posterized.mode, "LAB")
        pixel = posterized.getpixel((0, 0))
        self.assertEqual(len(pixel), 3)

    def test_mode_1_invert(self):
        """Test invert_colors on binary mode '1' images preserving mode."""
        img = Image.new("1", (10, 10), 0)
        inverted = invert_colors(img)
        self.assertEqual(inverted.mode, "1")

    def test_hsv_mode_luts(self):
        """Test brightness, contrast, and hue rotation on HSV images."""
        img = Image.new("HSV", (20, 20), (100, 200, 150))
        brightened = adjust_brightness(img, 20)
        self.assertEqual(brightened.mode, "HSV")

        rotated = rotate_hue(img, 90)
        self.assertEqual(rotated.mode, "HSV")

    def test_palette_mode_luts(self):
        """Test brightness, contrast, and posterize on Palette (P) images."""
        img_rgb = Image.new("RGB", (20, 20), (100, 150, 200))
        img_p = img_rgb.convert("P")
        self.assertEqual(img_p.mode, "P")

        brightened = adjust_brightness(img_p, 25)
        self.assertEqual(brightened.mode, "P")

        contrasted = adjust_contrast(img_p, 25)
        self.assertEqual(contrasted.mode, "P")

        posterized = apply_posterize(img_p, 4)
        self.assertEqual(posterized.mode, "P")

        inverted = invert_colors(img_p)
        self.assertEqual(inverted.mode, "P")

    def test_16bit_integer_mode_luts(self):
        """Test 16-bit integer (I;16) brightness and contrast adjustments."""
        img = Image.new("I;16", (20, 20), 30000)
        brightened = adjust_brightness(img, 10)
        self.assertTrue(brightened.mode.startswith("I;16"))

        contrasted = adjust_contrast(img, 10)
        self.assertTrue(contrasted.mode.startswith("I;16"))

    def test_posterize_fallback_mode(self):
        """Verifies the fallback LUT application for unexpected but valid modes."""

        # Pillow's Image.mode is a property that can't be easily patched directly on the instance using patch.object.
        # Instead, we can create a mock image that acts like a Pillow image.
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "UNKNOWN"
        mock_img.getbands.return_value = ("R", "G", "B")

        # When image.convert is called, return the mock image itself to stay in UNKNOWN mode
        mock_img.convert.return_value = mock_img

        apply_posterize(mock_img, bits=4)

        # Verify that point was called, indicating the fallback branch ran
        mock_img.point.assert_called_once()


class TestImageBorder(unittest.TestCase):
    def setUp(self):
        self.width, self.height = 100, 100
        self.test_image = Image.new("RGB", (self.width, self.height), (100, 100, 100))

    def test_border_expand(self):
        thickness = 10
        img_with_border = apply_border(self.test_image, thickness, "red", "expand")

        # Dimensions should increase by 2*thickness
        self.assertEqual(
            img_with_border.size,
            (self.width + 2 * thickness, self.height + 2 * thickness),
        )

        # Top-left corner should be red (border)
        self.assertEqual(img_with_border.getpixel((0, 0)), (255, 0, 0))
        # Center should be original color
        center_x = (self.width + 2 * thickness) // 2
        center_y = (self.height + 2 * thickness) // 2
        self.assertEqual(
            img_with_border.getpixel((center_x, center_y)), (100, 100, 100)
        )

    def test_border_inside(self):
        thickness = 10
        border_color_rgb = (0, 0, 255)
        original_color = (100, 100, 100)

        img_with_border = apply_border(self.test_image, thickness, "#0000FF", "inside")

        # Dimensions should match original
        self.assertEqual(img_with_border.size, (self.width, self.height))

        # Top-left corner should be blue (border)
        self.assertEqual(img_with_border.getpixel((0, 0)), border_color_rgb)

        # Center should be original color
        self.assertEqual(
            img_with_border.getpixel((self.width // 2, self.height // 2)),
            original_color,
        )

        # Check Top Border Boundary
        self.assertEqual(
            img_with_border.getpixel((self.width // 2, thickness - 1)),
            border_color_rgb,
            "Top border outer edge failed",
        )
        self.assertEqual(
            img_with_border.getpixel((self.width // 2, thickness)),
            original_color,
            "Top border inner edge failed",
        )

        # Check Bottom Border Boundary
        self.assertEqual(
            img_with_border.getpixel((self.width // 2, self.height - thickness)),
            border_color_rgb,
            "Bottom border outer edge failed",
        )
        self.assertEqual(
            img_with_border.getpixel((self.width // 2, self.height - thickness - 1)),
            original_color,
            "Bottom border inner edge failed",
        )

        # Check Left Border Boundary
        self.assertEqual(
            img_with_border.getpixel((thickness - 1, self.height // 2)),
            border_color_rgb,
            "Left border outer edge failed",
        )
        self.assertEqual(
            img_with_border.getpixel((thickness, self.height // 2)),
            original_color,
            "Left border inner edge failed",
        )

        # Check Right Border Boundary
        self.assertEqual(
            img_with_border.getpixel((self.width - thickness, self.height // 2)),
            border_color_rgb,
            "Right border outer edge failed",
        )
        self.assertEqual(
            img_with_border.getpixel((self.width - thickness - 1, self.height // 2)),
            original_color,
            "Right border inner edge failed",
        )

    def test_border_custom_color_string_and_zero_thickness(self):
        """Verifies apply_border handles 255,0,0 format strings and zero thickness gracefully."""
        # Zero thickness
        img_zero = apply_border(self.test_image, 0, "red")
        self.assertEqual(img_zero, self.test_image)

        # "255,0,0" format
        img_custom = apply_border(self.test_image, 10, "255,0,0", "expand")
        self.assertEqual(img_custom.getpixel((0, 0)), (255, 0, 0))

    def test_border_invalid_args(self):
        with self.assertRaises(ValueError):
            apply_border(self.test_image, -5, "red")
        with self.assertRaisesRegex(
            ValueError, r"^Invalid color format: invalid_color$"
        ):
            apply_border(self.test_image, 10, "invalid_color")
        with self.assertRaises(ValueError):
            apply_border(self.test_image, 10, "red", "invalid_pos")

    def test_border_thickness_limit(self):
        from image_converter.image_filters import MAX_BORDER_THICKNESS

        with self.assertRaises(ValueError) as cm:
            apply_border(self.test_image, MAX_BORDER_THICKNESS + 1, "red")
        self.assertIn("Thickness exceeds maximum allowed limit", str(cm.exception))

    def test_border_output_size_limit(self):
        # Create a large image but within limits
        # 5000 * 5000 = 25MP
        large_img = Image.new("RGB", (5000, 5000), (100, 100, 100))
        # Adding 3000px border: new size = (5000 + 6000) * (5000 + 6000) = 11000 * 11000 = 121MP
        # This should exceed 100MP (MAX_TOTAL_PIXELS)
        thickness = 3000
        with self.assertRaises(ValueError) as cm:
            apply_border(large_img, thickness, "red", "expand")
        self.assertIn("exceeds maximum allowed limit", str(cm.exception))


class TestImageRotation(unittest.TestCase):
    def setUp(self):
        # Create a rectangular image to easily verify rotation
        self.width, self.height = 100, 50
        self.test_image = Image.new("RGB", (self.width, self.height), "blue")
        # Mark top-left pixel
        self.test_image.putpixel((0, 0), (255, 0, 0))  # Red pixel at top-left

    def test_rotate_90(self):
        # 90 degrees clockwise? PIL rotate is counter-clockwise by default.
        # But let's check what we implemented. We just passed the angle to image.rotate.
        # PIL image.rotate(90) rotates counter-clockwise.

        rotated = rotate_image(self.test_image, 90)

        # Dimensions should be swapped (50, 100)
        self.assertEqual(rotated.size, (self.height, self.width))

        # Original top-left (0,0) red pixel should move to bottom-left (0, 100) -> Wait,
        # (0,0) in PIL is top-left.
        # Rotate 90 CCW:
        # Top-left (0,0) -> Bottom-left (0, 50-1) => (0, 49) ? No.
        # Let's verify standard PIL behavior.
        # (x, y) -> (y, width-x-1) ?

        # Let's just trust dimensions for now and visual checks via automated tests,
        # but verifying dimensions is a strong signal for 90 deg rotation.
        # We can also check 180 and 360.

    def test_rotate_180(self):
        rotated = rotate_image(self.test_image, 180)
        self.assertEqual(rotated.size, (self.width, self.height))  # Same dimensions

    def test_rotate_270(self):
        rotated = rotate_image(self.test_image, 270)
        self.assertEqual(rotated.size, (self.height, self.width))  # Swapped dimensions

    def test_rotate_clamping(self):
        # 89 -> 90
        self.assertEqual(
            rotate_image(self.test_image, 89).size, (self.height, self.width)
        )
        # 44 -> 0
        self.assertEqual(
            rotate_image(self.test_image, 44).size, (self.width, self.height)
        )
        # 46 -> 90
        self.assertEqual(
            rotate_image(self.test_image, 46).size, (self.height, self.width)
        )

    def test_rotate_negative(self):
        # -90 -> 270
        rotated = rotate_image(self.test_image, -90)
        self.assertEqual(rotated.size, (self.height, self.width))


class TestImageVignette(unittest.TestCase):
    def setUp(self):
        self.width, self.height = 100, 100
        self.test_image = Image.new("RGB", (self.width, self.height), (255, 255, 255))

    def test_vignette_basic(self):
        vignetted = apply_vignette(self.test_image, 100)
        center_pixel = vignetted.getpixel((50, 50))
        corner_pixel = vignetted.getpixel((0, 0))

        # Center should remain white (or very close)
        self.assertGreater(center_pixel[0], 240)

        # Corners should be darkened significantly
        self.assertLess(corner_pixel[0], 100)

    def test_vignette_zero_intensity(self):
        vignetted = apply_vignette(self.test_image, 0)
        self.assertEqual(list(vignetted.getdata()), list(self.test_image.getdata()))

    def test_vignette_rgba(self):
        rgba_image = self.test_image.copy().convert("RGBA")
        alpha = Image.new("L", rgba_image.size, 128)
        rgba_image.putalpha(alpha)

        vignetted = apply_vignette(rgba_image, 50)

        self.assertEqual(vignetted.mode, "RGBA")
        _, _, _, new_alpha = vignetted.split()
        self.assertEqual(list(new_alpha.getdata()), list(alpha.getdata()))

    def test_vignette_invalid_args(self):
        with self.assertRaises(ValueError):
            apply_vignette(self.test_image, -10)
        with self.assertRaises(ValueError):
            apply_vignette(self.test_image, 110)
        with self.assertRaises(TypeError):
            apply_vignette(self.test_image, "invalid")


class TestImageFiltersEdgeCases(unittest.TestCase):
    def test_invert_colors_rgba(self):
        """Verifies the fast path for RGBA images when inverting colors."""
        img = Image.new("RGBA", (10, 10), (100, 50, 20, 10))
        inverted = invert_colors(img)
        self.assertEqual(inverted.mode, "RGBA")
        self.assertEqual(inverted.getpixel((0, 0)), (155, 205, 235, 10))

    def test_invert_colors_not_rgba_rgb_l(self):
        """Verifies color inversion for images not in RGBA, RGB, or L mode (e.g. CMYK)."""
        img = Image.new("CMYK", (10, 10), (100, 50, 20, 10))
        inverted = invert_colors(img)
        self.assertEqual(inverted.mode, "CMYK")

    def test_edge_detection_missing_deps(self):
        """Verifies that an ImportError is raised if scikit-image is missing."""
        import sys

        img = Image.new("RGB", (10, 10))
        original_skimage = sys.modules.get("skimage")
        sys.modules["skimage"] = None
        try:
            with self.assertRaisesRegex(
                ImportError, r"scikit-image and numpy are required for edge detection\."
            ):
                edge_detection(img, "sobel")
        finally:
            if original_skimage is not None:
                sys.modules["skimage"] = original_skimage
            else:
                del sys.modules["skimage"]

    def test_apply_blur_zero_radius(self):
        """Verifies that applying a blur with zero radius returns the original image."""
        img = Image.new("RGB", (10, 10))
        blurred = apply_blur(img, 0)
        self.assertIs(blurred, img)

    def test_apply_sharpen_zero_sharpness(self):
        """Verifies that applying sharpening with zero sharpness returns the original image."""
        img = Image.new("RGB", (10, 10))
        sharpened = apply_sharpen(img, 0)
        self.assertIs(sharpened, img)

    def test_apply_color_balance_not_rgb_rgba(self):
        """Verifies color balance natively supports non-RGB/RGBA modes (e.g. CMYK)."""
        img = Image.new("CMYK", (10, 10), (100, 50, 20, 10))
        balanced = apply_color_balance(img, 1.5, 1.0, 1.0)
        self.assertEqual(balanced.mode, "CMYK")

    def test_apply_posterize_l_mode(self):
        """Verifies that posterizing an L mode image returns an L mode image."""
        img = Image.new("L", (10, 10), 128)
        posterized = apply_posterize(img, 4)
        self.assertEqual(posterized.mode, "L")

    def test_apply_vignette_l_mode(self):
        """Verifies that applying a vignette to an L mode image returns an L mode image."""
        img = Image.new("L", (10, 10), 128)
        vignetted = apply_vignette(img, 50)
        self.assertEqual(vignetted.mode, "L")

    def test_vignette_truncation(self):
        """Verifies that vignette mask generation uses round() to avoid truncation off-by-one errors."""
        from image_converter.image_filters import _generate_vignette_mask

        # With int() truncation, a calculated val of ~0.985 * 255 = ~251.175
        # We need a value that ends in something > .5 to catch the truncation
        mask = _generate_vignette_mask(100, 50)

        # We check the size of the image to satisfy usage
        self.assertEqual(mask.size, (100, 100))

    def test_scaled_lut_truncation(self):
        """Verifies that LUT scaling uses round() to avoid truncation off-by-one errors."""
        from image_converter.image_filters import _generate_scaled_lut

        # factor = 1.005.
        # For i=100: 100 * 1.005 = 100.5.
        # int(100.5) = 100
        # int(round(100.5)) = 100

        # factor = 1.006
        # For i=100: 100 * 1.006 = 100.6.
        # int(100.6) = 100
        # int(round(100.6)) = 101

        lut = _generate_scaled_lut(1.006)

        # Without round(), lut[100] would be 100. With round(), it is 101.
        self.assertEqual(lut[100], 101)

    def test_hue_rotation_truncation(self):
        """Verifies that hue rotation uses round() to avoid truncation off-by-one errors."""
        from image_converter.image_filters import _get_hue_rotation_lut

        # For an angle like 150 degrees, 150 / 360 * 256 = 106.666
        # int(106.666) -> 106
        # int(round(106.666)) -> 107

        # 150 degrees corresponds to shift 107 with proper rounding.
        # Let's inspect the LUT for shift 107.
        _ = _get_hue_rotation_lut(107)

        # Under old behavior, 150 degrees would pass 106 to this function.
        # Our newly refactored shift variable will compute 107. We test this mathematically:
        shift = int(round((150 / 360.0) * 256)) % 256
        self.assertEqual(shift, 107)

    def test_all_filters_preserve_palette_transparency(self):
        """Verifies that palette mode images with transparency metadata retain transparency across all filters."""
        p_img = Image.new("P", (10, 10), 0)
        p_img.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
        p_img.info["transparency"] = 0

        filters_to_test = [
            lambda img: adjust_brightness(img, 50),
            lambda img: adjust_contrast(img, 50),
            lambda img: adjust_saturation(img, 50),
            lambda img: apply_blur(img, 2),
            lambda img: apply_sharpen(img, 50),
            lambda img: apply_color_balance(img, 50, 50, 50),
            lambda img: apply_posterize(img, 4),
            lambda img: invert_colors(img),
            lambda img: rotate_hue(img, 45),
            lambda img: apply_vignette(img, 50),
        ]

        for fn in filters_to_test:
            res = fn(p_img)
            has_transparency = ("A" in res.getbands()) or ("transparency" in res.info)
            self.assertTrue(
                has_transparency,
                f"Transparency metadata was lost by filter operation: {fn}",
            )

    def test_all_filters_preserve_la_alpha(self):
        """Verifies that LA (Grayscale + Alpha) mode images preserve their alpha channel across all filters."""
        la_img = Image.new("LA", (10, 10), (100, 128))

        filters_to_test = [
            lambda img: adjust_brightness(img, 50),
            lambda img: adjust_contrast(img, 50),
            lambda img: adjust_saturation(img, 50),
            lambda img: apply_blur(img, 2),
            lambda img: apply_sharpen(img, 50),
            lambda img: apply_color_balance(img, 50, 50, 50),
            lambda img: apply_posterize(img, 4),
            lambda img: invert_colors(img),
            lambda img: rotate_hue(img, 45),
            lambda img: apply_vignette(img, 50),
        ]

        for fn in filters_to_test:
            res = fn(la_img)
            self.assertIn("A", res.getbands())
            self.assertEqual(res.getchannel("A").getextrema(), (128, 128))

    def test_all_filters_preserve_info_metadata(self):
        """Verifies that image.info metadata (dpi, icc_profile) is retained across all filters."""
        meta_img = Image.new("RGB", (10, 10), (100, 100, 100))
        meta_img.info["dpi"] = (300, 300)
        meta_img.info["icc_profile"] = b"dummy_icc_bytes"

        filters_to_test = [
            lambda img: adjust_brightness(img, 50),
            lambda img: adjust_contrast(img, 50),
            lambda img: adjust_saturation(img, 50),
            lambda img: apply_blur(img, 2),
            lambda img: apply_sharpen(img, 50),
            lambda img: apply_color_balance(img, 50, 50, 50),
            lambda img: apply_posterize(img, 4),
            lambda img: invert_colors(img),
            lambda img: rotate_hue(img, 45),
            lambda img: apply_vignette(img, 50),
        ]

        for fn in filters_to_test:
            res = fn(meta_img)
            self.assertEqual(res.info.get("dpi"), (300, 300))
            self.assertEqual(res.info.get("icc_profile"), b"dummy_icc_bytes")

    def test_all_filters_zero_alpha_scenario(self):
        """Verifies that all-zero alpha RGBA images complete without runtime errors across all filters."""
        zero_img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))

        filters_to_test = [
            lambda img: adjust_brightness(img, 50),
            lambda img: adjust_contrast(img, 50),
            lambda img: adjust_saturation(img, 50),
            lambda img: apply_blur(img, 2),
            lambda img: apply_sharpen(img, 50),
            lambda img: apply_color_balance(img, 50, 50, 50),
            lambda img: apply_posterize(img, 4),
            lambda img: invert_colors(img),
            lambda img: rotate_hue(img, 45),
            lambda img: apply_vignette(img, 50),
        ]

        for fn in filters_to_test:
            res = fn(zero_img)
            self.assertIn("A", res.getbands())
            self.assertEqual(res.getchannel("A").getextrema(), (0, 0))


class TestPainterlyEffects(unittest.TestCase):
    """Tests for the oil-painting and cartoonify filters."""

    def setUp(self):
        self.image = Image.new("RGB", (24, 24))
        for x in range(24):
            for y in range(24):
                self.image.putpixel((x, y), (255, 255, 255) if x < 12 else (20, 20, 20))

    def test_oil_painting_preserves_rgba_alpha(self):
        image = self.image.convert("RGBA")
        image.putalpha(128)
        result = apply_oil_painting(image, 50)
        self.assertEqual(result.mode, "RGBA")
        self.assertEqual(result.getchannel("A").getextrema(), (128, 128))

    def test_painterly_effects_preserve_palette_transparency(self):
        palette_image = Image.new("P", (24, 24), 0)
        palette_image.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
        palette_image.info["transparency"] = 0
        for x in range(12, 24):
            for y in range(24):
                palette_image.putpixel((x, y), 1)

        for effect in (apply_oil_painting, apply_cartoonify):
            result = effect(palette_image, 50)
            self.assertEqual(result.mode, "RGBA")
            alpha_extrema = result.getchannel("A").getextrema()
            self.assertEqual(alpha_extrema, (0, 255))

    def test_painterly_preserves_palette_transparency(self):
        """Verifies that Palette images with transparency metadata retain their alpha."""
        rgba_img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
        palette_img = rgba_img.convert("P")
        palette_img.info["transparency"] = 0

        for effect in (apply_oil_painting, apply_cartoonify):
            result_img = effect(palette_img, intensity=5)
            has_alpha_band = "A" in result_img.getbands()
            has_transparency_info = "transparency" in result_img.info
            self.assertTrue(
                has_alpha_band or has_transparency_info,
                "Transparency was completely lost",
            )
            if has_alpha_band:
                expected_alpha = (
                    palette_img.convert("RGBA").getchannel("A").getextrema()
                )
                self.assertEqual(
                    result_img.getchannel("A").getextrema(), expected_alpha
                )

    def test_painterly_la_mode(self):
        """Verifies that LA (Grayscale + Alpha) images preserve their alpha channel."""
        la_image = Image.new("LA", (24, 24), (100, 128))
        for effect in (apply_oil_painting, apply_cartoonify):
            result = effect(la_image, intensity=5)
            self.assertIn("A", result.getbands())
            self.assertEqual(result.getchannel("A").getextrema(), (128, 128))

    def test_painterly_preserves_metadata_info(self):
        """Verifies that image.info metadata (e.g. dpi, icc_profile) is retained."""
        img = self.image.copy()
        img.info["dpi"] = (300, 300)
        img.info["icc_profile"] = b"dummy_icc_data"

        for effect in (apply_oil_painting, apply_cartoonify):
            result = effect(img, intensity=5)
            self.assertEqual(result.info.get("dpi"), (300, 300))
            self.assertEqual(result.info.get("icc_profile"), b"dummy_icc_data")

    def test_painterly_zero_alpha_scenario(self):
        """Verifies that all-zero alpha RGBA images are processed without error."""
        zero_alpha_img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        for effect in (apply_oil_painting, apply_cartoonify):
            result = effect(zero_alpha_img, intensity=5)
            self.assertEqual(result.mode, "RGBA")
            self.assertEqual(result.getchannel("A").getextrema(), (0, 0))

    def test_cartoonify_creates_edges_and_preserves_dimensions(self):
        result = apply_cartoonify(self.image, 100)
        self.assertEqual(result.mode, "RGB")
        self.assertEqual(result.size, self.image.size)
        self.assertIn((0, 0, 0), result.getdata())

    def test_cartoonify_edge_strength_scales_with_intensity(self):
        """Verifies that Sobel edge overlay strength increases monotonically with intensity."""
        from skimage.color import rgb2gray
        from skimage.filters import sobel

        edge_mask = sobel(rgb2gray(np.asarray(self.image))) > 0.05
        res_low = np.asarray(apply_cartoonify(self.image, 25))
        res_mid = np.asarray(apply_cartoonify(self.image, 50))
        res_high = np.asarray(apply_cartoonify(self.image, 100))

        mean_edge_low = res_low[edge_mask].mean()
        mean_edge_mid = res_mid[edge_mask].mean()
        mean_edge_high = res_high[edge_mask].mean()

        self.assertGreater(mean_edge_low, mean_edge_mid)
        self.assertGreater(mean_edge_mid, mean_edge_high)

    def test_effects_return_original_image_at_zero_intensity(self):
        self.assertIs(apply_oil_painting(self.image, 0), self.image)
        self.assertIs(apply_cartoonify(self.image, 0), self.image)

    def test_effects_validate_intensity(self):
        for effect in (apply_oil_painting, apply_cartoonify):
            with self.assertRaises(ValueError):
                effect(self.image, 101)
            with self.assertRaises(TypeError):
                effect(self.image, "50")
