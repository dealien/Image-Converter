import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
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
