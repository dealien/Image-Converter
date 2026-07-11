import argparse
import os
import shutil
import unittest
from unittest.mock import patch, MagicMock


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

    @patch("image_converter.processing.Image.Image.save")
    def test_format_quality_alignment(self, mock_save):
        """Verifies that missing qualities are padded with the last specified quality or 90."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()

        # Test case 1: quality provided but shorter than format list
        args.format = ["webp", "jpg"]
        args.quality = [80]

        processing.process_images_and_save(images_data, ordered_operations, args)

        self.assertEqual(mock_save.call_count, 2)

        # Check that both saves happened with quality=80 (the second padded with the last value)
        call_1_kwargs = mock_save.call_args_list[0][1]
        call_2_kwargs = mock_save.call_args_list[1][1]

        self.assertEqual(call_1_kwargs.get("format"), "WEBP")
        self.assertEqual(call_1_kwargs.get("quality"), 80)
        self.assertEqual(call_2_kwargs.get("format"), "JPEG")
        self.assertEqual(call_2_kwargs.get("quality"), 80)

        mock_save.reset_mock()

        # Test case 2: format list provided but quality is totally empty
        args.format = ["webp", "jpg"]
        args.quality = []

        processing.process_images_and_save(images_data, ordered_operations, args)

        self.assertEqual(mock_save.call_count, 2)
        call_1_kwargs = mock_save.call_args_list[0][1]
        call_2_kwargs = mock_save.call_args_list[1][1]

        # Should default to 90
        self.assertEqual(call_1_kwargs.get("quality"), 90)
        self.assertEqual(call_2_kwargs.get("quality"), 90)

    @patch("image_converter.processing.Image.Image.save")
    def test_convert_to_rgb_on_save(self, mock_save):
        """Verifies that RGBA/LA/P images are converted to RGB when saved as JPG/BMP."""
        images_data = [("test_rgba.png", self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()
        args.format = ["jpg"]
        args.quality = [90]

        from unittest.mock import MagicMock

        with patch("image_converter.processing.Image.open") as mock_open:
            # We mock the opened image to simulate an RGBA image using MagicMock
            mock_img = MagicMock(spec=processing.Image.Image)
            mock_img.mode = "RGBA"
            mock_img.info = {}

            # The context manager __enter__ should return our mock
            mock_open.return_value.__enter__.return_value = mock_img
            # Also set the direct return value for any non-context usage
            mock_open.return_value = mock_img

            # Set up the copy so that if the logic checks `if output_image is img: output_image = img.copy()`
            mock_img_copy = MagicMock(spec=processing.Image.Image)
            mock_img_copy.mode = "RGBA"
            mock_img_copy.info = {}
            mock_img.copy.return_value = mock_img_copy

            # Set up the converted return
            mock_converted = MagicMock(spec=processing.Image.Image)
            mock_converted.info = {}
            mock_img_copy.convert.return_value = mock_converted

            processing.process_images_and_save(images_data, ordered_operations, args)

            # Assert convert("RGB") was called on the copied image
            mock_img_copy.convert.assert_called_once_with("RGB")
            # Assert save was called on the CONVERTED image
            mock_converted.save.assert_called_once()

    @patch("image_converter.processing.Image.Image.save")
    def test_save_format_tiff(self, mock_save):
        """Verifies that 'tif' format is mapped to 'TIFF' for Pillow."""
        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = []
        args = argparse.Namespace()
        args.format = ["tif"]
        args.quality = [90]

        processing.process_images_and_save(images_data, ordered_operations, args)

        mock_save.assert_called_once()
        self.assertEqual(mock_save.call_args[1].get("format"), "TIFF")

    @patch("image_converter.processing.console.print")
    @patch("image_converter.processing.Progress")
    @patch("image_converter.processing.Image.open")
    def test_read_only_skip_save(self, mock_open, mock_progress_class, mock_print):
        """Verifies that processing skips the save step for read-only operations when no format is specified."""
        # Configure mock progress context manager
        mock_progress = MagicMock()
        mock_progress_class.return_value.__enter__.return_value = mock_progress

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_open.return_value.__enter__.return_value = mock_img

        images_data = [(self.test_image_name, self.test_image_path)]
        ordered_operations = [{"dest": "view_metadata", "values": []}]

        args = argparse.Namespace()
        args.format = None
        args.quality = None

        processing.process_images_and_save(images_data, ordered_operations, args)

        # Verify that the skip save message was displayed
        found_skip = False
        for call in mock_progress.update.call_args_list:
            if "Skipping save, read-only" in str(call):
                found_skip = True

        self.assertTrue(
            found_skip, "Should have skipped saving for read-only operations"
        )
        mock_img.save.assert_not_called()
