import unittest
from unittest.mock import patch
import os
from image_converter import rich_menu
from image_converter import menu


class TestMetadataParallel(unittest.TestCase):
    @patch("image_converter.rich_menu._get_image_metadata")
    @patch("image_converter.rich_menu.questionary.checkbox")
    @patch("image_converter.rich_menu.Console")
    def test_run_image_selector_parallel(
        self, mock_console, mock_checkbox, mock_get_metadata
    ):
        # Mock metadata return values
        mock_get_metadata.side_effect = [
            ("100 × 100", "1.0 KB", "PNG"),
            ("200 × 200", "2.0 KB", "JPEG"),
        ]
        # Mock checkbox to return selections
        mock_checkbox.return_value.ask.return_value = ["path/to/img1.png"]

        image_files = ["img1.png", "img2.jpg"]
        image_dir = "Base Images"

        selected = rich_menu.run_image_selector(image_files, image_dir)

        self.assertEqual(selected, ["path/to/img1.png"])
        # Ensure it was called for all files in the list
        self.assertEqual(mock_get_metadata.call_count, 2)

    @patch("image_converter.menu._get_image_metadata")
    @patch("image_converter.menu.select_images")
    @patch("image_converter.menu.select_manipulations")
    @patch("image_converter.menu.process_images_and_save")
    def test_interactive_menu_parallel(
        self, mock_process, mock_sel_manips, mock_sel_imgs, mock_get_metadata
    ):
        # Mock selected paths
        mock_sel_imgs.return_value = ["path1.png", "path2.jpg"]
        # Mock metadata for the selected paths
        mock_get_metadata.side_effect = [
            ("100 × 100", "1.0 KB", "PNG"),
            ("200 × 200", "2.0 KB", "JPEG"),
        ]
        # Mock manipulations to just return and exit
        mock_sel_manips.return_value = ([], {}, [], [])

        # We need to mock os.path.basename since it's used in the parallel loop
        with patch(
            "image_converter.menu.os.path.basename", side_effect=os.path.basename
        ):
            menu.interactive_menu()

        # Ensure metadata was fetched for each selected path
        self.assertEqual(mock_get_metadata.call_count, 2)
        mock_process.assert_called_once()


if __name__ == "__main__":
    unittest.main()
