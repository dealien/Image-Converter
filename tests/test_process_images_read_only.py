import unittest
import argparse
from unittest.mock import patch, MagicMock
from image_converter import processing


class TestProcessImagesReadOnly(unittest.TestCase):
    @patch("image_converter.processing.Progress")
    @patch("image_converter.processing.Image.open")
    def test_process_images_and_save_read_only_skips_save(
        self, mock_image_open, mock_progress_class
    ):
        """Verifies that an image is not saved when only read-only operations are applied."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.copy.return_value = mock_img
        mock_image_open.return_value.__enter__.return_value = mock_img

        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        # We need to simulate the progress bar adding a task to get an ID
        mock_progress.add_task.return_value = 1

        images_data = [("test_image.png", "test_path.png")]

        ordered_operations = [{"dest": "view_metadata", "values": []}]

        args = argparse.Namespace()
        args.format = None
        args.quality = None
        args.resample = "bicubic"
        args.threshold = 120

        # Patch the handler directly
        with patch(
            "image_converter.processing.handle_view_metadata"
        ) as mock_view_metadata:
            mock_view_metadata.return_value = mock_img
            processing.process_images_and_save(images_data, ordered_operations, args)

        # Verify progress update was called with the right descriptions
        update_calls = mock_progress.update.call_args_list
        found_skipping = any(
            "Skipping save, read-only" in str(call) for call in update_calls
        )
        self.assertTrue(found_skipping, "Should have logged 'Skipping save, read-only'")

        # Verify img.save was not called
        mock_img.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
