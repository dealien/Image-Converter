import argparse
import unittest
from unittest.mock import patch

from PIL import Image

from image_converter import processing


class TestOperationHandlers(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (100, 100))
        self.image_name = "test.png"
        self.args = argparse.Namespace()

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.flip_image")
    def test_handle_flip(self, mock_flip, mock_print):
        mock_flip.return_value = "flipped_image"
        values = ["horizontal"]
        result = processing.handle_flip(self.image, self.image_name, values, self.args)

        mock_print.assert_called_once_with(
            "  [bright_yellow]›[/] [yellow]Flipping horizontal...[/]"
        )
        mock_flip.assert_called_once_with(self.image, "horizontal")
        self.assertEqual(result, "flipped_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.remove_background")
    def test_handle_remove_background(self, mock_remove, mock_print):
        mock_remove.return_value = "no_bg_image"
        values = []
        result = processing.handle_remove_background(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_remove.assert_called_once_with(self.image)
        self.assertEqual(result, "no_bg_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.invert_colors")
    def test_handle_invert(self, mock_invert, mock_print):
        """Verifies that handle_invert logs correctly and calls invert_colors."""
        mock_invert.return_value = "inverted_image"
        values = []
        result = processing.handle_invert(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_invert.assert_called_once_with(self.image)
        self.assertEqual(result, "inverted_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.grayscale")
    def test_handle_grayscale(self, mock_grayscale, mock_print):
        mock_grayscale.return_value = "grayscale_image"
        values = []
        result = processing.handle_grayscale(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_grayscale.assert_called_once_with(self.image)
        self.assertEqual(result, "grayscale_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.grayscale")
    def test_handle_grayscale_delegation(self, mock_grayscale, mock_print):
        """Verifies that handle_grayscale correctly delegates the image and returns the result."""
        mock_grayscale.return_value = "grayscale_image_delegated"
        values = []
        result = processing.handle_grayscale(
            self.image, self.image_name, values, self.args
        )
        mock_print.assert_called_with(
            "  [bright_yellow]›[/] [yellow]Converting to grayscale...[/]"
        )
        mock_grayscale.assert_called_once_with(self.image)
        self.assertEqual(result, "grayscale_image_delegated")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.adjust_brightness")
    def test_handle_brightness(self, mock_adjust, mock_print):
        mock_adjust.return_value = "bright_image"
        values = [50]
        result = processing.handle_brightness(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_adjust.assert_called_once_with(self.image, 50)
        self.assertEqual(result, "bright_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.adjust_contrast")
    def test_handle_contrast(self, mock_adjust, mock_print):
        mock_adjust.return_value = "contrasted_image"
        values = [-20]
        result = processing.handle_contrast(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_adjust.assert_called_once_with(self.image, -20)
        self.assertEqual(result, "contrasted_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.adjust_saturation")
    def test_handle_saturation(self, mock_adjust, mock_print):
        mock_adjust.return_value = "saturated_image"
        values = [10]
        result = processing.handle_saturation(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_adjust.assert_called_once_with(self.image, 10)
        self.assertEqual(result, "saturated_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_blur")
    def test_handle_blur(self, mock_apply, mock_print):
        mock_apply.return_value = "blurred_image"
        values = [2.5]
        result = processing.handle_blur(self.image, self.image_name, values, self.args)

        mock_print.assert_called_once()
        mock_apply.assert_called_once_with(self.image, 2.5)
        self.assertEqual(result, "blurred_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_sharpen")
    def test_handle_sharpen(self, mock_apply, mock_print):
        mock_apply.return_value = "sharpened_image"
        values = [5]
        result = processing.handle_sharpen(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_apply.assert_called_once_with(self.image, 5)
        self.assertEqual(result, "sharpened_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_color_balance")
    def test_handle_color_balance(self, mock_apply, mock_print):
        mock_apply.return_value = "balanced_image"
        values = [1.2, 0.8, 1.0]
        result = processing.handle_color_balance(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_apply.assert_called_once_with(self.image, 1.2, 0.8, 1.0)
        self.assertEqual(result, "balanced_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.rotate_hue")
    def test_handle_hue_rotation(self, mock_rotate, mock_print):
        mock_rotate.return_value = "hue_rotated_image"
        values = [90]
        result = processing.handle_hue_rotation(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_rotate.assert_called_once_with(self.image, 90)
        self.assertEqual(result, "hue_rotated_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_posterize")
    def test_handle_posterize(self, mock_apply, mock_print):
        mock_apply.return_value = "posterized_image"
        values = [4]
        result = processing.handle_posterize(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_apply.assert_called_once_with(self.image, 4)
        self.assertEqual(result, "posterized_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.rotate_image")
    def test_handle_rotate(self, mock_rotate, mock_print):
        mock_rotate.return_value = "rotated_image"
        values = [180]
        result = processing.handle_rotate(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_rotate.assert_called_once_with(self.image, 180)
        self.assertEqual(result, "rotated_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.edge_detection")
    def test_handle_edge_detection_default(self, mock_edge, mock_print):
        mock_edge.return_value = "edge_image"
        values = ["sobel"]
        result = processing.handle_edge_detection(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_edge.assert_called_once_with(self.image, "sobel")
        self.assertEqual(result, "edge_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.edge_detection")
    def test_handle_edge_detection_kovalevsky(self, mock_edge, mock_print):
        mock_edge.return_value = "kovalevsky_image"
        values = ["kovalevsky"]
        self.args.threshold = 42
        result = processing.handle_edge_detection(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_edge.assert_called_once_with(self.image, "kovalevsky", 42)
        self.assertEqual(result, "kovalevsky_image")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_vignette")
    def test_handle_vignette(self, mock_apply, mock_print):
        """Verifies that handle_vignette logs correctly and calls apply_vignette."""
        mock_apply.return_value = "vignette_image"
        values = [50]
        result = processing.handle_vignette(
            self.image, self.image_name, values, self.args
        )

        mock_print.assert_called_once()
        mock_apply.assert_called_once_with(self.image, 50)
        self.assertEqual(result, "vignette_image")


if __name__ == "__main__":
    unittest.main()
