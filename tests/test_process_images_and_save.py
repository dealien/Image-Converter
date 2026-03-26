import unittest
from unittest.mock import patch
import argparse
import os
import shutil
from PIL import Image, ImageChops

from image_converter import processing


class TestProcessImagesAndSave(unittest.TestCase):
    def setUp(self):
        self.output_dir = "Output"
        self.test_image_dir = "tests/test_images"
        self.test_image_name = "Tree Clear Sky 1.png"
        self.test_image_path = os.path.join(self.test_image_dir, self.test_image_name)

        # Ensure output directory doesn't exist before each test
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        # Clean up output directory after each test
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch("image_converter.processing.console.print")
    def test_empty_images_data(self, mock_print):
        # Empty images_data -> early return with "No images to process."
        processing.process_images_and_save([], [], argparse.Namespace())
        mock_print.assert_called_once_with("[yellow]No images to process.[/]")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.Image.open")
    def test_exception_during_image_load(self, mock_open, mock_print):
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
        images_data = [(self.test_image_name, self.test_image_path)]
        # Chain: Invert -> Grayscale
        ordered_operations = [
            {"dest": "invert", "values": []},
            {"dest": "grayscale", "values": []},
        ]
        args = argparse.Namespace()

        processing.process_images_and_save(images_data, ordered_operations, args)

        # Expected output from manual application
        from image_converter.image_filters import invert_colors, grayscale

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


if __name__ == "__main__":
    unittest.main()
