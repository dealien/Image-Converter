import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from image_converter import processing


class TestHandleBorderErrorHandling(unittest.TestCase):
    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_border")
    def test_handle_border_value_error(self, mock_apply_border, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace()

        # Test Case: Invalid thickness (non-int)
        values = ["invalid_thickness", "black", "expand"]
        result = processing.handle_border(image, "test.png", values, args)

        # Verify
        mock_console_print.assert_called_with(
            "  [bright_red]✗[/] [red]Invalid border arguments: ['invalid_thickness', 'black', 'expand']. Error: invalid literal for int() with base 10: 'invalid_thickness'[/]"
        )
        self.assertEqual(result, image)
        mock_apply_border.assert_not_called()

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_border")
    def test_handle_border_index_error(self, mock_apply_border, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace()

        # Test Case: Missing position
        values = ["10", "black"]
        result = processing.handle_border(image, "test.png", values, args)

        # Verify
        mock_console_print.assert_called_with(
            "  [bright_red]✗[/] [red]Invalid border arguments: ['10', 'black']. Error: list index out of range[/]"
        )
        self.assertEqual(result, image)
        mock_apply_border.assert_not_called()

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.apply_border")
    def test_handle_border_valid(self, mock_apply_border, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace()
        mock_apply_border.return_value = "bordered_image"

        # Test Case: Valid arguments
        values = ["10", "black", "expand"]
        result = processing.handle_border(image, "test.png", values, args)

        # Verify
        mock_console_print.assert_called_with(
            "  [bright_yellow]›[/] [yellow]Adding border: 10px, black, expand[/]"
        )
        self.assertEqual(result, "bordered_image")
        mock_apply_border.assert_called_once_with(image, 10, "black", "expand")


if __name__ == "__main__":
    unittest.main()
