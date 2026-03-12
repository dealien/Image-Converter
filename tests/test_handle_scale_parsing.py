import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import processing


class TestHandleScaleParsing(unittest.TestCase):
    @patch("processing.console.print")
    @patch("processing.scale_image")
    def test_handle_scale_factor_parsing(self, mock_scale_image, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")
        mock_scale_image.return_value = "scaled_image"

        # Test Case 1: scale factor with 'x' (e.g. '1.5x')
        values = ["1.5x"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_called_with(
            image, scale_factor=1.5, new_size=None, resample_filter="bilinear"
        )
        self.assertEqual(result, "scaled_image")

        mock_scale_image.reset_mock()

        # Test Case 2: scale factor without 'x' (e.g. '2.0')
        values = ["2.0"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_called_with(
            image, scale_factor=2.0, new_size=None, resample_filter="bilinear"
        )
        self.assertEqual(result, "scaled_image")

    @patch("processing.console.print")
    @patch("processing.scale_image")
    def test_handle_scale_size_parsing(self, mock_scale_image, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bicubic")
        mock_scale_image.return_value = "scaled_image"

        # Test Case 1: size with 'px' (e.g. '400px', '300px')
        values = ["400px", "300px"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_called_with(
            image, scale_factor=None, new_size=(400, 300), resample_filter="bicubic"
        )
        self.assertEqual(result, "scaled_image")

        mock_scale_image.reset_mock()

        # Test Case 2: size without 'px' (e.g. '800', '600')
        values = ["800", "600"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_called_with(
            image, scale_factor=None, new_size=(800, 600), resample_filter="bicubic"
        )
        self.assertEqual(result, "scaled_image")

    @patch("processing.console.print")
    @patch("processing.scale_image")
    def test_handle_scale_invalid_strings(self, mock_scale_image, mock_console_print):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case 1: invalid single string
        values = ["invalid"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_not_called()
        self.assertEqual(result, image)

        # Test Case 2: invalid double strings
        values = ["400px", "invalid"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_not_called()
        self.assertEqual(result, image)

        # Test Case 3: invalid argument counts
        values = ["400px", "300px", "200px"]
        result = processing.handle_scale(image, "test.png", values, args)
        mock_scale_image.assert_not_called()
        self.assertEqual(result, image)


if __name__ == "__main__":
    unittest.main()
