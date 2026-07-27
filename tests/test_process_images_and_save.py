"""Unit tests for the main image processing pipeline in processing.py."""

import argparse
import os
import shutil
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops

from image_converter import processing


class TestProcessImagesAndSave(unittest.TestCase):
    """Test suite for the `process_images_and_save` core function."""

    def setUp(self):
        """Set up the test environment."""
        self.output_dir = "Output"
        self.test_image_dir = "tests/test_images"
        self.test_image_name = "Tree Clear Sky 1.png"
        self.test_image_path = os.path.join(self.test_image_dir, self.test_image_name)

        # Ensure output directory doesn't exist before each test
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        """Tear down the test environment."""
        # Clean up output directory after each test
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch("image_converter.processing.console.print")
    def test_empty_images_data(self, mock_print):
        """Test processing with empty images data array."""
        # Empty images_data -> early return with "No images to process."
        processing.process_images_and_save([], [], argparse.Namespace())
        mock_print.assert_any_call("[yellow]No images to process.[/]")
        mock_print.assert_any_call(
            "[dim white]Please specify valid image files or ensure images exist in your input directory.[/]"
        )
        self.assertEqual(mock_print.call_count, 2)

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.Image.open")
    def test_exception_during_image_load(self, mock_open, mock_print):
        """Test exception handling during image load."""
        # Mock opening to fail
        mock_open.side_effect = Exception("Mocked load error")
        images_data = [("test_image.png", "fake_path.png")]

        processing.process_images_and_save(images_data, [], argparse.Namespace())

        # Verify that output directory isn't suddenly filled with garbage or anything
        self.assertFalse(
            os.path.exists(os.path.join(self.output_dir, "test_image.png"))
        )
        # Check that it did not raise an unhandled exception

    def test_successful_path_output_dir_and_cli_string(self):
        """Test successful image processing output and generated CLI string matching."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = [
            {"dest": "scale", "values": ["0.5x"]},
            {"dest": "edge_detection", "values": ["kovalevsky"]},
        ]
        args = argparse.Namespace()
        args.resample = "bicubic"
        args.threshold = 120

        # We'll patch `console.print` to capture the CLI string
        with patch("image_converter.processing.console.print") as mock_print:
            processing.process_images_and_save(images_data, ordered_operations, args)

        # Output dir should be created
        self.assertTrue(os.path.exists(self.output_dir))
        # The file should be saved
        self.assertTrue(
            os.path.exists(os.path.join(self.output_dir, self.test_image_name))
        )

        # Check CLI string generation
        cli_printed = False
        for call_args, _ in mock_print.call_args_list:
            output = str(call_args)
            if "Equivalent CLI Command" in output:
                pass  # The label is printed
            if "> image-converter" in output:
                # The actual command should include the file path
                if (
                    " ".join(
                        [
                            "--scale 0.5x",
                            "--resample bicubic",
                            "--edge-detection kovalevsky",
                            "--threshold 120",
                        ]
                    )
                    in output
                ):
                    cli_printed = True

        self.assertTrue(
            cli_printed,
            "The equivalent CLI command with special args wasn't printed correctly.",
        )

    def test_chained_operations_integration(self):
        """Test chaining multiple image operations sequentially."""
        images_data = [(self.test_image_name, self.test_image_path)]
        # Chain: Invert -> Grayscale
        ordered_operations = [
            {"dest": "invert", "values": []},
            {"dest": "grayscale", "values": []},
        ]
        args = argparse.Namespace()

        processing.process_images_and_save(images_data, ordered_operations, args)

        # Expected output from manual application
        from image_converter.image_filters import grayscale, invert_colors

        with Image.open(self.test_image_path) as img:
            expected_image = grayscale(invert_colors(img.copy()))

        output_image_path = os.path.join(self.output_dir, self.test_image_name)
        self.assertTrue(os.path.exists(output_image_path))

        with Image.open(output_image_path) as actual_image:
            diff = ImageChops.difference(
                expected_image.convert("RGB"), actual_image.convert("RGB")
            )
            self.assertIsNone(
                diff.getbbox(), "Chained operations did not produce the expected image."
            )

    @patch("image_converter.processing.console.print")
    def test_flatten_alpha_channel(self, mock_print):
        """Test flattening the alpha channel onto a solid background."""
        # Create a test RGBA image with transparency
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        img.paste((0, 255, 0, 255), (25, 25, 75, 75))  # Green square in middle

        test_file = os.path.join(self.test_image_dir, "test_alpha.png")
        img.save(test_file)

        images_data = [("test_alpha.png", test_file)]
        ordered_operations = []

        args = argparse.Namespace()
        args.format = ["webp"]
        args.quality = [90]
        args.flatten = "red"

        try:
            processing.process_images_and_save(images_data, ordered_operations, args)

            output_image_path = os.path.join(self.output_dir, "test_alpha.webp")
            self.assertTrue(os.path.exists(output_image_path))

            with Image.open(output_image_path) as actual_image:
                actual = actual_image.convert("RGB")
                # Calculate expected result: red background with green square
                expected_bg = Image.new("RGB", (100, 100), "red")
                expected_bg.paste(
                    img.convert("RGBA"), mask=img.convert("RGBA").split()[3]
                )

                diff = ImageChops.difference(expected_bg, actual)
                # Since WEBP is lossy by default, check if the maximum difference is within a reasonable threshold
                extrema = diff.getextrema()

                for min_val, max_val in extrema:
                    self.assertLessEqual(
                        max_val,
                        210,
                        "Flattened image differs significantly from the expected solid background composite.",
                    )
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == "__main__":
    unittest.main()
