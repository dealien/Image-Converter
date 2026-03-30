import argparse
import unittest
from unittest.mock import patch, MagicMock, mock_open


class TestProcessingMetadataExport(unittest.TestCase):
    def setUp(self):
        self.mock_img = MagicMock()
        self.mock_img.mode = "RGB"
        self.mock_img.info = {}

        self.args = argparse.Namespace()
        self.args.format = None
        self.args.quality = None

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    @patch("image_converter.processing.console.print")
    def test_metadata_export_single_fallback(
        self, mock_print, mock_getsize, mock_img_open
    ):
        """Verifies that exporting a single file defaults to the correct fallback file path."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [("test_image.jpg", "path/to/test_image.jpg")]
        ordered_operations = []
        self.args.metadata_manifest = {"test_image.jpg": {"Artist": "Me"}}
        self.args.export_metadata_path = None

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", mock_open()) as mocked_file:
            process_images_and_save(images_data, ordered_operations, self.args)

            mocked_file.assert_called_once_with(
                "test_image_tags.json", "w", encoding="utf-8"
            )

            found_success = False
            for call in mock_print.call_args_list:
                if "Exported metadata manifest to" in str(call):
                    found_success = True
            self.assertTrue(found_success)

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    def test_metadata_export_batch_fallback(self, mock_getsize, mock_img_open):
        """Verifies that exporting multiple files defaults to 'batch_tags.json'."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [
            ("test1.jpg", "path/to/test1.jpg"),
            ("test2.jpg", "path/to/test2.jpg"),
        ]
        ordered_operations = []
        self.args.metadata_manifest = {"test1.jpg": {"Artist": "Me"}, "test2.jpg": {}}
        self.args.export_metadata_path = None

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", mock_open()) as mocked_file:
            process_images_and_save(images_data, ordered_operations, self.args)

            mocked_file.assert_called_once_with(
                "batch_tags.json", "w", encoding="utf-8"
            )

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    def test_metadata_export_list_fallback(self, mock_getsize, mock_img_open):
        """Verifies that parsing a single None list argument resolves back to 'batch_tags.json'."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [("test.jpg", "path/to/test.jpg")]
        ordered_operations = []
        self.args.metadata_manifest = {"test.jpg": {"Artist": "Me"}}
        self.args.export_metadata_path = [None]  # List fallback

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", mock_open()) as mocked_file:
            process_images_and_save(images_data, ordered_operations, self.args)

            mocked_file.assert_called_once_with(
                "batch_tags.json", "w", encoding="utf-8"
            )

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    def test_metadata_export_list_value(self, mock_getsize, mock_img_open):
        """Verifies that parsing a custom path from a single-item list works correctly."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [("test.jpg", "path/to/test.jpg")]
        ordered_operations = []
        self.args.metadata_manifest = {"test.jpg": {"Artist": "Me"}}
        self.args.export_metadata_path = ["custom_tags.json"]  # List fallback

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", mock_open()) as mocked_file:
            process_images_and_save(images_data, ordered_operations, self.args)

            mocked_file.assert_called_once_with(
                "custom_tags.json", "w", encoding="utf-8"
            )

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    @patch("image_converter.processing.os.makedirs")
    def test_metadata_export_with_directory(
        self, mock_makedirs, mock_getsize, mock_img_open
    ):
        """Verifies that parent directories are created properly when exporting metadata."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [("test.jpg", "path/to/test.jpg")]
        ordered_operations = []
        self.args.metadata_manifest = {"test.jpg": {"Artist": "Me"}}
        self.args.export_metadata_path = "output_dir/tags.json"

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", mock_open()) as mocked_file:
            process_images_and_save(images_data, ordered_operations, self.args)

            mock_makedirs.assert_called_once()
            self.assertEqual(str(mock_makedirs.call_args[0][0]), "output_dir")
            mocked_file.assert_called_once_with(
                "output_dir/tags.json", "w", encoding="utf-8"
            )

    @patch("image_converter.processing.Image.open")
    @patch("image_converter.processing.os.path.getsize")
    @patch("image_converter.processing.console.print")
    def test_metadata_export_error_handling(
        self, mock_print, mock_getsize, mock_img_open
    ):
        """Verifies that an exception during export triggers an error print statement."""
        mock_img_open.return_value.__enter__.return_value = self.mock_img
        mock_getsize.return_value = 1000

        images_data = [("test.jpg", "path/to/test.jpg")]
        ordered_operations = []
        self.args.metadata_manifest = {"test.jpg": {"Artist": "Me"}}
        self.args.export_metadata_path = "tags.json"

        from image_converter.processing import process_images_and_save

        with patch("builtins.open", side_effect=Exception("Mocked open error")):
            process_images_and_save(images_data, ordered_operations, self.args)

            found_error = False
            for call in mock_print.call_args_list:
                if "Error exporting metadata manifest to" in str(call):
                    found_error = True
            self.assertTrue(found_error)


if __name__ == "__main__":
    unittest.main()
