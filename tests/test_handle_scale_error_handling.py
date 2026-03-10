import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import processing

class TestHandleScaleErrorHandling(unittest.TestCase):
    @patch("processing.logger")
    @patch("processing.scale_image")
    def test_handle_scale_invalid_factor(self, mock_scale_image, mock_logger):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case: Invalid scale factor (non-float)
        values = ["invalid_factor"]
        result = processing.handle_scale(image, "test.png", values, args)

        # Verify
        mock_logger.error.assert_called_with("Invalid scale factor: invalid_factor")
        self.assertEqual(result, image)
        mock_scale_image.assert_not_called()

    @patch("processing.logger")
    @patch("processing.scale_image")
    def test_handle_scale_invalid_size(self, mock_scale_image, mock_logger):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case: Invalid size format (one of the dimensions is not int)
        values = ["400px", "invalid_height"]
        result = processing.handle_scale(image, "test.png", values, args)

        # Verify
        mock_logger.error.assert_called_with(f"Invalid size format: {values}")
        self.assertEqual(result, image)
        mock_scale_image.assert_not_called()

    @patch("processing.logger")
    @patch("processing.scale_image")
    def test_handle_scale_invalid_args_count(self, mock_scale_image, mock_logger):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case: Invalid number of arguments (more than 2)
        values = ["400px", "300px", "extra"]
        result = processing.handle_scale(image, "test.png", values, args)

        # Verify
        mock_logger.error.assert_called_with(
            "Invalid format for --scale argument. Use '1.5', '1.5x' or '400px 300px'."
        )
        self.assertEqual(result, image)
        mock_scale_image.assert_not_called()

if __name__ == "__main__":
    unittest.main()
