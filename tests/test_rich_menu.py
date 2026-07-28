import os
import unittest
from unittest.mock import patch

from image_converter import rich_menu


class TestRichMenu(unittest.TestCase):
    def test_get_image_metadata_nonexistent_path(self):
        """Test metadata extraction with a path that does not exist."""
        dims, size_str, fmt = rich_menu._get_image_metadata("nonexistent_fake_path.png")
        self.assertEqual(dims, "—")
        self.assertEqual(size_str, "—")
        self.assertEqual(fmt, "UNKNOWN")

    @patch("image_converter.rich_menu.os.path.getsize")
    def test_get_image_metadata_non_image_file(self, mock_getsize):
        """Test metadata extraction with a non-image file that exists."""
        # Assume it has size but is not a valid image
        mock_getsize.return_value = 1024

        # Create a dummy text file
        test_file = "test_dummy.txt"
        with open(test_file, "w") as f:
            f.write("This is not an image.")

        dims, size_str, fmt = rich_menu._get_image_metadata(test_file)

        self.assertEqual(dims, "—")
        self.assertEqual(size_str, "1.0 KB")
        self.assertEqual(fmt, "UNKNOWN")

        os.remove(test_file)

    @patch("image_converter.rich_menu.console.print")
    @patch("image_converter.rich_menu.console.clear")
    def test_render_combined_menu_empty_operations(self, mock_clear, mock_print):
        """Test rendering the menu with no operations."""
        images_data = [
            {"name": "test.png", "dims": "100x100", "size": "10KB", "fmt": "PNG"}
        ]
        operations = []
        extra_args = {}

        rich_menu.render_combined_menu(images_data, operations, extra_args)

        # Verify it didn't crash
        mock_clear.assert_called_once()
        self.assertTrue(mock_print.called)

    @patch("image_converter.rich_menu.console.print")
    @patch("image_converter.rich_menu.console.clear")
    def test_render_combined_menu_with_operations_and_args(
        self, mock_clear, mock_print
    ):
        """Test rendering the menu with specific operations requiring extra args."""
        images_data = [
            {"name": "test.png", "dims": "100x100", "size": "10KB", "fmt": "PNG"}
        ]
        operations = [
            {"dest": "scale", "values": ["0.5x"]},
            {"dest": "edge_detection", "values": ["kovalevsky"]},
        ]
        extra_args = {"resample": "bicubic", "threshold": 120}

        rich_menu.render_combined_menu(images_data, operations, extra_args)

        # Verify it runs without error
        mock_clear.assert_called_once()
        self.assertTrue(mock_print.called)


if __name__ == "__main__":
    unittest.main()
