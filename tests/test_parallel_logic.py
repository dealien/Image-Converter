import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# We need to mock dependencies before importing rich_menu or menu
mock_pil = MagicMock()
sys.modules["PIL"] = mock_pil
sys.modules["PIL.Image"] = mock_pil.Image
sys.modules["questionary"] = MagicMock()
sys.modules["rich"] = MagicMock()
sys.modules["rich.table"] = MagicMock()
sys.modules["rich.text"] = MagicMock()
sys.modules["rich.panel"] = MagicMock()
sys.modules["rich.box"] = MagicMock()
sys.modules["rich.console"] = MagicMock()
sys.modules["rich.rule"] = MagicMock()
sys.modules["rich.progress"] = MagicMock()
sys.modules["rich.live"] = MagicMock()
sys.modules["prompt_toolkit"] = MagicMock()
sys.modules["prompt_toolkit.formatted_text"] = MagicMock()
sys.modules["prompt_toolkit.lexers"] = MagicMock()
sys.modules["prompt_toolkit.validation"] = MagicMock()
sys.modules["prompt_toolkit.styles"] = MagicMock()
sys.modules["prompt_toolkit.application"] = MagicMock()
sys.modules["prompt_toolkit.application.current"] = MagicMock()
sys.modules["coloredlogs"] = MagicMock()
sys.modules["skimage"] = MagicMock()
sys.modules["skimage.filters"] = MagicMock()
sys.modules["skimage.feature"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["rembg"] = MagicMock()

import rich_menu
import menu


class TestParallelLogic(unittest.TestCase):
    @patch("rich_menu._get_image_metadata")
    @patch("questionary.checkbox")
    def test_run_image_selector_parallel(self, mock_checkbox, mock_get_metadata):
        mock_get_metadata.side_effect = [
            ("100x100", "1KB", "PNG"),
            ("200x200", "2KB", "JPG"),
        ]
        mock_checkbox.return_value.ask.return_value = ["path1", "path2"]

        image_files = ["img1.png", "img2.jpg"]
        image_dir = "test_dir"

        selected = rich_menu.run_image_selector(image_files, image_dir)

        self.assertEqual(selected, ["path1", "path2"])
        self.assertEqual(mock_get_metadata.call_count, 2)


class TestMenuParallelLogic(unittest.TestCase):
    @patch("menu._get_image_metadata")
    @patch("menu.select_images")
    @patch("menu.select_manipulations")
    @patch("menu.process_images_and_save")
    def test_interactive_menu_parallel(
        self, mock_process, mock_sel_manips, mock_sel_imgs, mock_get_metadata
    ):
        mock_sel_imgs.return_value = ["path1", "path2"]
        mock_get_metadata.side_effect = [
            ("100x100", "1KB", "PNG"),
            ("200x200", "2KB", "JPG"),
        ]
        mock_sel_manips.return_value = ([], {})

        menu.interactive_menu()

        self.assertEqual(mock_get_metadata.call_count, 2)
        mock_process.assert_called_once()


if __name__ == "__main__":
    unittest.main()
