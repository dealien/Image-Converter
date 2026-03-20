import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from image_converter import processing


class TestProcessingLogging(unittest.TestCase):
    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.scale_image")
    def test_handle_scale_logging(self, mock_scale_image, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case 1: Scale Factor
        values_factor = ["1.5x"]
        processing.handle_scale(image, "test.png", values_factor, args)

        # Verify logger called with scale factor message
        # We look for the call that contains "Scaling by factor: 1.5"
        found = False
        for call in mock_console_print.call_args_list:
            if "Scaling by factor: 1.5" in call[0][0]:
                found = True
                break
        self.assertTrue(found, "Logger should log scale factor")

        # Test Case 2: Dimensions
        values_dims = ["400px", "300px"]
        processing.handle_scale(image, "test.png", values_dims, args)

        # Verify logger called with dimensions message
        found = False
        for call in mock_console_print.call_args_list:
            if "Scaling to dimensions: 400x300" in call[0][0]:
                found = True
                break
        self.assertTrue(found, "Logger should log dimensions")


class TestStyledTimeElapsedColumn(unittest.TestCase):
    def test_render_styled_time(self):
        # Setup
        column = processing.StyledTimeElapsedColumn(style="bold blue")
        task = MagicMock()
        # Mocking task.elapsed to a fixed value
        task.elapsed = 1.0

        # We need to mock the parent render or check the output
        # TimeElapsedColumn.render returns a Text object
        text = column.render(task)

        from rich.text import Text

        self.assertIsInstance(text, Text)
        self.assertEqual(str(text), "0:00:01")
        self.assertEqual(text.style, "bold blue")

    def test_init_default_style(self):
        column = processing.StyledTimeElapsedColumn()
        self.assertEqual(column.style, "none")


if __name__ == "__main__":
    unittest.main()
