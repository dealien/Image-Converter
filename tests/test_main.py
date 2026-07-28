"""Tests for the main module and command-line entry point."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from automated_testing import (  # noqa: E402
    ValidationError,
    validate_command,
    validate_commands,
)
from PIL import Image, ImageChops

# Import the image filter functions to create an expected image
from image_converter.image_filters import grayscale, invert_colors  # noqa: E402

# Add the project root to the Python path
# Import the main function that we want to test
from image_converter.main import create_parser, main  # noqa: E402


class TestMain(unittest.TestCase):
    """Test suite for the main application entry point and CLI argument parsing."""

    def test_create_parser(self):
        """Test that create_parser returns an ArgumentParser and parses valid arguments."""
        parser = create_parser()
        args = parser.parse_args(
            ["input.png", "--oil-painting", "50", "--cartoonify", "30"]
        )
        self.assertEqual(args.file, "input.png")
        self.assertEqual(len(args.ordered_operations), 2)
        self.assertEqual(
            args.ordered_operations[0], {"dest": "oil_painting", "values": [50]}
        )
        self.assertEqual(
            args.ordered_operations[1], {"dest": "cartoonify", "values": [30]}
        )

    def test_validate_command_valid(self):
        """Test validate_command with valid command argument list."""
        validate_command(["tests/test_images/*", "--oil-painting", "50"])

    def test_validate_command_invalid(self):
        """Test validate_command raises ValidationError for invalid CLI arguments."""
        with self.assertRaises(ValidationError):
            validate_command(["tests/test_images/*", "--unknown-flag"])

    def test_validate_commands_success(self):
        """Test validate_commands succeeds with valid command list."""
        commands = [
            ["tests/test_images/*", "--oil-painting", "50"],
            ["tests/test_images/*", "--cartoonify", "50"],
        ]
        validate_commands(commands)

    def test_validate_commands_failure(self):
        """Test validate_commands aborts with SystemExit on invalid command."""
        commands = [
            ["tests/test_images/*", "--invalid-flag"],
        ]
        with self.assertRaises(SystemExit):
            validate_commands(commands)

    # Patch the function where it is looked up: in the 'processing' module
    @patch("image_converter.processing.remove_background")
    @patch("image_converter.main.move_images_to_subdirectory")
    def test_wildcard_file_argument(self, mock_move, mock_remove_background):
        """Test that wildcard file arguments are handled correctly."""
        mock_remove_background.return_value = Image.new("RGBA", (10, 10))

        # There are 2 images with "Tree" in the name in the test assets
        with patch.object(
            sys, "argv", ["main.py", "-bg", "tests/test_images/Tree*.png"]
        ):
            main()

        # Check that the mocked function was called for each matching file
        self.assertEqual(mock_remove_background.call_count, 2)

    # Patch the function where it is looked up: in the 'processing' module
    @patch("image_converter.processing.remove_background")
    @patch("image_converter.main.move_images_to_subdirectory")
    @patch("glob.glob")
    @patch("os.path.isfile")
    def test_all_files_argument(
        self, mock_isfile, mock_glob, mock_move, mock_remove_background
    ):
        """Test the wildcard '*' to process all files in the directory."""
        mock_remove_background.return_value = Image.new("RGBA", (10, 10))

        # Mock glob.glob to return a list of dummy file paths
        mock_glob.return_value = [
            "Base Images/file1.png",
            "Base Images/file2.png",
            "Base Images/file3.png",
            "Base Images/file4.png",
        ]
        # Mock os.path.isfile to always return True for the dummy paths
        mock_isfile.return_value = True

        with patch(
            "image_converter.processing.Image.open",
            MagicMock(side_effect=lambda *args: Image.new("RGB", (10, 10))),
        ):
            with patch.object(sys, "argv", ["main.py", "-bg", "*"]):
                main()

        # Check that the mocked function was called for each file
        self.assertEqual(mock_remove_background.call_count, 4)

    def test_multiple_operations_in_order(self):
        """Test that multiple operations are applied in the correct order."""
        input_image_path = "tests/test_images/Tree Clear Sky 1.png"
        output_image_path = "Output/Tree Clear Sky 1.png"

        # Ensure the output directory exists
        os.makedirs("Output", exist_ok=True)

        # Create the expected image by applying operations directly
        with Image.open(input_image_path) as img:
            # It's important to apply operations in the same order as the command
            expected_image = grayscale(invert_colors(img.copy()))

        # Run the main function with command line arguments
        # We patch move_images_to_subdirectory to prevent it from moving our test images
        with patch("image_converter.main.move_images_to_subdirectory"):
            with patch.object(
                sys, "argv", ["main.py", input_image_path, "--invert", "--grayscale"]
            ):
                main()

        # Check that the output file was created
        self.assertTrue(os.path.exists(output_image_path))

        # Compare the actual output with the expected image
        with Image.open(output_image_path) as actual_image:
            # Convert both to RGB to ensure comparison is valid
            diff = ImageChops.difference(
                expected_image.convert("RGB"), actual_image.convert("RGB")
            )
            self.assertIsNone(diff.getbbox(), "The output image is not as expected.")

        # Clean up the created file
        if os.path.exists(output_image_path):
            os.remove(output_image_path)

    def test_store_in_order_action(self):
        """Test the StoreInOrder argparse action handles None, scalars, and multiple ops."""
        import argparse

        from image_converter.main import StoreInOrder

        parser = argparse.ArgumentParser()
        parser.add_argument("--scale", action=StoreInOrder, dest="scale")
        parser.add_argument("--invert", action=StoreInOrder, dest="invert")
        parser.add_argument("--blur", action=StoreInOrder, dest="blur")

        namespace = argparse.Namespace()

        # parser._actions[0] is typically the help action
        action_scale = parser._actions[1]
        action_invert = parser._actions[2]
        action_blur = parser._actions[3]

        # Test with None (like a flag without args)
        action_invert(parser, namespace, None)
        self.assertEqual(len(namespace.ordered_operations), 1)
        self.assertEqual(
            namespace.ordered_operations[0], {"dest": "invert", "values": []}
        )

        # Test with scalar value
        action_blur(parser, namespace, 2.5)
        self.assertEqual(len(namespace.ordered_operations), 2)
        self.assertEqual(
            namespace.ordered_operations[1], {"dest": "blur", "values": [2.5]}
        )

        # Test with list (multiple values)
        action_scale(parser, namespace, ["800px", "600px"])
        self.assertEqual(len(namespace.ordered_operations), 3)
        self.assertEqual(
            namespace.ordered_operations[2],
            {"dest": "scale", "values": ["800px", "600px"]},
        )

    @patch("image_converter.menu.interactive_menu")
    def test_menu_flag_triggers_interactive_menu(self, mock_menu):
        """Test that the --menu flag triggers the interactive menu."""
        with patch.object(sys, "argv", ["main.py", "--menu"]):
            main()
        mock_menu.assert_called_once()

    @patch("image_converter.menu.interactive_menu")
    def test_no_args_triggers_interactive_menu(self, mock_menu):
        """Test that running without args triggers the interactive menu."""
        with patch.object(sys, "argv", ["main.py"]):
            main()
        mock_menu.assert_called_once()

    @patch("image_converter.main.console.print")
    def test_no_actions_specified(self, mock_console_print):
        """Test that main exits early and prints a warning when no actions or formats are specified."""
        # Provide a file argument but no operations or format flags
        with patch.object(sys, "argv", ["main.py", "dummy.png"]):
            main()

        mock_console_print.assert_called_with(
            "[yellow]No actions specified. Please provide at least one operation flag (e.g., --invert, --scale 2x) "
            "or an output format (e.g., --format webp).[/]\n"
            "[dim white]To see all available options, run with --help or use the interactive --menu.[/]"
        )

    @patch("image_converter.main.move_images_to_subdirectory")
    @patch("glob.glob")
    @patch("image_converter.main.console.print")
    def test_no_files_found(self, mock_console_print, mock_glob, mock_move):
        """Test that main prints a warning and exits when no files match the pattern."""
        # Mock glob to return empty list (no files found)
        mock_glob.return_value = []

        # Run main with an operation and a custom file pattern
        with patch.object(sys, "argv", ["main.py", "nonexistent*.png", "--invert"]):
            main()

        mock_console_print.assert_any_call(
            "[yellow]No files found matching pattern: 'nonexistent*.png'[/]\n"
            "[dim white]Please verify the file path or ensure images exist in the target directory.[/]"
        )
        mock_console_print.assert_any_call(
            "[dim white]Please check the path or place some images in the specified directory and try again.[/]"
        )

    @patch("image_converter.main.move_images_to_subdirectory")
    @patch("glob.glob")
    @patch("image_converter.main.console.print")
    def test_loading_exception(self, mock_console_print, mock_glob, mock_move):
        """Test that an exception during file loading is caught and printed."""
        # Make glob.glob raise an exception
        mock_glob.side_effect = Exception("Mocked loading error")

        # Run main with valid arguments so it attempts to load files
        with patch.object(sys, "argv", ["main.py", "-bg", "*"]):
            main()

        # Check that the exception message was printed
        mock_console_print.assert_called_with(
            "[red]Error while loading file(s). Please verify the directory and try again.[/]"
        )


if __name__ == "__main__":
    unittest.main()
