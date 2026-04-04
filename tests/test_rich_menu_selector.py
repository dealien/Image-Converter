import unittest
from unittest.mock import patch, MagicMock
from image_converter import rich_menu


class TestRichMenuSelector(unittest.TestCase):
    def test_run_image_selector_empty_list(self):
        """Verifies that an empty image list returns an empty list without prompting."""
        result = rich_menu.run_image_selector([], "/fake/dir")
        self.assertEqual(result, [])

    @patch("image_converter.rich_menu.questionary.checkbox")
    @patch("image_converter.rich_menu._get_image_metadata")
    @patch("image_converter.rich_menu.console.print")
    def test_run_image_selector_with_files(
        self, mock_print, mock_metadata, mock_checkbox
    ):
        """Verifies that file selection returns the selected paths and handles long names."""
        mock_metadata.return_value = ("100x100", "10KB", "PNG")
        mock_checkbox.return_value.ask.return_value = ["/fake/dir/test.png"]

        # Add one normal name and one extremely long name to trigger truncation
        files = ["test.png", "a" * 35 + ".png"]
        result = rich_menu.run_image_selector(files, "/fake/dir")

        self.assertEqual(result, ["/fake/dir/test.png"])
        mock_checkbox.assert_called_once()

        # Verify choices formatting
        choices = mock_checkbox.call_args[1]["choices"]
        self.assertEqual(len(choices), 2)
        # Check that the long name was truncated correctly with an ellipsis
        long_choice_title = choices[1].title
        self.assertIn("aaaaaaaaaaaaaaaaaaaaaaaaaaaaa…", long_choice_title)

    @patch("image_converter.rich_menu.questionary.checkbox")
    @patch("image_converter.rich_menu._get_image_metadata")
    @patch("image_converter.rich_menu.console.print")
    def test_run_image_selector_cancelled(
        self, mock_print, mock_metadata, mock_checkbox
    ):
        """Verifies that returning None from the prompt returns None."""
        mock_metadata.return_value = ("100x100", "10KB", "PNG")
        mock_checkbox.return_value.ask.return_value = None

        result = rich_menu.run_image_selector(["test.png"], "/fake/dir")
        self.assertIsNone(result)

    @patch("image_converter.rich_menu.os.path.getsize")
    def test_get_image_metadata_mb(self, mock_getsize):
        """Verifies that files >= 1MB are formatted correctly."""
        mock_getsize.return_value = 1048576 * 2.5
        with patch("image_converter.rich_menu.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.width = 100
            mock_img.height = 100
            mock_img.format = "PNG"
            mock_open.return_value.__enter__.return_value = mock_img
            dims, size_str, fmt = rich_menu._get_image_metadata("dummy.png")
            self.assertEqual(size_str, "2.5 MB")

    @patch("image_converter.rich_menu.os.path.getsize")
    def test_get_image_metadata_b(self, mock_getsize):
        """Verifies that files < 1KB are formatted correctly and handles None format."""
        mock_getsize.return_value = 500
        with patch("image_converter.rich_menu.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.width = 100
            mock_img.height = 100
            mock_img.format = None
            mock_open.return_value.__enter__.return_value = mock_img
            dims, size_str, fmt = rich_menu._get_image_metadata("dummy.png")
            self.assertEqual(size_str, "500 B")
            self.assertEqual(fmt, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
