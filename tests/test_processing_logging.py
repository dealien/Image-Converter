import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
import processing


class TestProcessingLogging(unittest.TestCase):
    @patch("processing.logger")
    @patch("processing.scale_image")
    def test_handle_scale_logging(self, mock_scale_image, mock_logger):
        # Setup
        image = MagicMock()
        args = SimpleNamespace(resample="bilinear")

        # Test Case 1: Scale Factor
        values_factor = ["1.5x"]
        processing.handle_scale(image, "test.png", values_factor, args)

        # Verify logger called with scale factor message
        # We look for the call that contains "Scaling by factor: 1.5"
        found = False
        for call in mock_logger.info.call_args_list:
            if "Scaling by factor: 1.5" in call[0][0]:
                found = True
                break
        self.assertTrue(found, "Logger should log scale factor")

        # Test Case 2: Dimensions
        values_dims = ["400px", "300px"]
        processing.handle_scale(image, "test.png", values_dims, args)

        # Verify logger called with dimensions message
        found = False
        for call in mock_logger.info.call_args_list:
            if "Scaling to dimensions: (400, 300)" in call[0][0]:
                found = True
                break
        self.assertTrue(found, "Logger should log dimensions")


if __name__ == "__main__":
    unittest.main()
