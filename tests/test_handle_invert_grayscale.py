import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import sys

# Mocking external dependencies that might not be present in the environment
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.progress'] = MagicMock()
sys.modules['rich.table'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.rule'] = MagicMock()
sys.modules['rich.text'] = MagicMock()
sys.modules['rich.box'] = MagicMock()
sys.modules['flip_image'] = MagicMock()
sys.modules['image_filters'] = MagicMock()
sys.modules['remove_background'] = MagicMock()
sys.modules['scale_image'] = MagicMock()

import processing

class TestHandleInvertGrayscale(unittest.TestCase):
    @patch("processing.console.print")
    @patch("processing.invert_colors")
    def test_handle_invert(self, mock_invert_colors, mock_console_print):
        # Setup
        image = MagicMock()
        image_name = "test.png"
        values = []
        args = SimpleNamespace()
        mock_inverted_image = MagicMock()
        mock_invert_colors.return_value = mock_inverted_image

        # Execute
        result = processing.handle_invert(image, image_name, values, args)

        # Verify
        mock_console_print.assert_called_with(
            "  [bright_yellow]›[/] [yellow]Inverting colors...[/]"
        )
        mock_invert_colors.assert_called_once_with(image)
        self.assertEqual(result, mock_inverted_image)

    @patch("processing.console.print")
    @patch("processing.grayscale")
    def test_handle_grayscale(self, mock_grayscale, mock_console_print):
        # Setup
        image = MagicMock()
        image_name = "test.png"
        values = []
        args = SimpleNamespace()
        mock_grayscale_image = MagicMock()
        mock_grayscale.return_value = mock_grayscale_image

        # Execute
        result = processing.handle_grayscale(image, image_name, values, args)

        # Verify
        mock_console_print.assert_called_with(
            "  [bright_yellow]›[/] [yellow]Converting to grayscale...[/]"
        )
        mock_grayscale.assert_called_once_with(image)
        self.assertEqual(result, mock_grayscale_image)


if __name__ == "__main__":
    unittest.main()
