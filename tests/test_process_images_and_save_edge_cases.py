import argparse
import os
import shutil
import unittest
from unittest.mock import patch


from image_converter import processing


class TestProcessImagesAndSaveEdgeCases(unittest.TestCase):
    def setUp(self):
        self.output_dir = "Output"
        self.test_image_dir = "tests/test_images"
        self.test_image_name = "Tree Clear Sky 1.png"
        self.test_image_path = os.path.join(self.test_image_dir, self.test_image_name)

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_img_copy_when_no_ops(self):
        """Verifies that an image is explicitly copied if no operations mutated it."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()

        with patch("image_converter.processing.Image.Image.copy") as mock_copy:
            # We mock copy to ensure it gets called
            mock_copy.return_value.width = 100
            mock_copy.return_value.height = 100
            processing.process_images_and_save(images_data, ordered_operations, args)

            mock_copy.assert_called_once()

    @patch("image_converter.processing.os.remove")
    def test_temp_file_removal_error(self, mock_remove):
        """Verifies that an OSError during temporary file removal is gracefully caught."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()

        # We need os.path.exists to return True for the temp file check in `finally`, but we
        # don't want to mock the whole thing which causes infinite recursion.
        # Instead, we mock os.replace to raise an exception, preventing temp file from being removed normally

        original_exists = os.path.exists

        def mock_exists_side_effect(path, *args, **kwargs):
            if isinstance(path, str) and ".tmp." in path:
                return True
            return original_exists(path)

        with patch(
            "image_converter.processing.os.replace",
            side_effect=Exception("mock replace error"),
        ):
            with patch(
                "image_converter.processing.os.path.exists",
                side_effect=mock_exists_side_effect,
            ):
                mock_remove.side_effect = OSError("Mocked removal error")

                # Test shouldn't crash
                processing.process_images_and_save(
                    images_data, ordered_operations, args
                )

                # Assert remove was attempted
                self.assertTrue(mock_remove.called)

    @patch("image_converter.processing.os.path.getsize")
    def test_file_size_formatting_bytes(self, mock_getsize):
        """Verifies that file size < 1024 bytes formats to B."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()

        # Mock getsize to return 500 bytes to trigger the `< 1024` branch
        mock_getsize.return_value = 500

        with patch("image_converter.processing.console.print") as mock_print:
            processing.process_images_and_save(images_data, ordered_operations, args)

        # Check that "500 B" was printed in the results table.
        # Note: console.print might receive a Table object instead of a string directly.
        found_bytes_format = False
        for call_args, _ in mock_print.call_args_list:
            for arg in call_args:
                if hasattr(arg, "rows"):  # Check if it's a Table object
                    for row in arg.rows:
                        # row is a Row object or similar, we iterate through its cells (Renderables)
                        # Instead of iterating through row, we just cast the whole table to string via rich Console
                        from rich.console import Console

                        console = Console()
                        with console.capture() as capture:
                            console.print(arg)
                        table_str = capture.get()
                        if "500 B" in table_str:
                            found_bytes_format = True

        self.assertTrue(found_bytes_format, "Should have formatted size as 500 B")
