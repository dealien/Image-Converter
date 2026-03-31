import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import piexif
from PIL import Image

from image_converter.metadata import (
    build_reverse_exif_map,
    cast_exif_value,
    handle_author,
    handle_copy_metadata,
    handle_copyright,
    handle_export_metadata,
    handle_set_metadata,
    handle_strip_metadata,
    handle_update_metadata,
    handle_view_metadata,
    parse_metadata_input,
)


class TestMetadata(unittest.TestCase):
    def test_build_reverse_exif_map(self):
        """Test that the reverse map builds correctly."""
        mapping = build_reverse_exif_map()
        self.assertIn("Artist", mapping)
        self.assertIn("Copyright", mapping)
        self.assertEqual(mapping["Artist"]["id"], 315)
        self.assertEqual(mapping["Copyright"]["id"], 33432)

    def test_cast_exif_value(self):
        """Test casting string inputs to appropriate EXIF types."""
        # Rational
        self.assertEqual(cast_exif_value("XResolution", "72/1"), (72, 1))
        self.assertEqual(cast_exif_value("YResolution", "300"), (300, 1))
        # Ascii
        self.assertEqual(cast_exif_value("Artist", "Jane Doe"), b"Jane Doe")
        # Short/Long
        self.assertEqual(cast_exif_value("ResolutionUnit", "2"), 2)

        # Test None
        self.assertIsNone(cast_exif_value("Artist", "None"))
        self.assertIsNone(cast_exif_value("Artist", None))

        # Undefined
        self.assertEqual(cast_exif_value("ExifVersion", "0231"), b"0231")

        # Unknown tag should raise ValueError
        with self.assertRaises(ValueError):
            cast_exif_value("UnknownTag", "123")

        # Error during parsing
        with self.assertRaisesRegex(ValueError, "Failed to cast"):
            cast_exif_value("ResolutionUnit", "invalid")

    def test_parse_metadata_input_inline_json(self):
        """Test parsing an inline JSON string."""
        values = ['{"Artist": "Jane Doe", "Copyright": "2026"}']
        result = parse_metadata_input(values)
        self.assertEqual(result, {"Artist": "Jane Doe", "Copyright": "2026"})

    def test_parse_metadata_input_key_value(self):
        """Test parsing Key=Value pairs."""
        values = ["Artist=Jane Doe", "Copyright=2026"]
        result = parse_metadata_input(values)
        self.assertEqual(result, {"Artist": "Jane Doe", "Copyright": "2026"})

    def test_parse_metadata_input_json_file(self):
        """Test parsing a JSON file."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
            json.dump({"Artist": "Jane Doe", "Copyright": "2026"}, f)
            temp_path = f.name

        try:
            values = [temp_path]
            result = parse_metadata_input(values)
            self.assertEqual(result, {"Artist": "Jane Doe", "Copyright": "2026"})
        finally:
            os.remove(temp_path)

    @patch("image_converter.metadata.console.print")
    def test_handle_view_metadata(self, mock_print):
        """Test viewing metadata."""
        mock_image = MagicMock(spec=Image.Image)
        exif_dict = {"0th": {piexif.ImageIFD.Artist: b"Jane Doe"}}
        exif_bytes = piexif.dump(exif_dict)
        mock_image.info = {"exif": exif_bytes}

        handle_view_metadata(mock_image, "test.jpg", [], None)
        mock_print.assert_any_call("      [cyan]Artist[/]: [white]Jane Doe[/]")

    def test_handle_export_metadata(self):
        """Test exporting metadata into the args manifest."""
        mock_image = MagicMock(spec=Image.Image)
        exif_dict = {"0th": {piexif.ImageIFD.Artist: b"Jane Doe"}}
        mock_image.info = {"exif": piexif.dump(exif_dict)}

        mock_args = MagicMock()
        del mock_args.metadata_manifest  # Ensure it's not pre-populated

        handle_export_metadata(mock_image, "test.jpg", ["custom_tags.json"], mock_args)
        self.assertTrue(hasattr(mock_args, "metadata_manifest"))
        self.assertEqual(mock_args.metadata_manifest["test.jpg"]["Artist"], "Jane Doe")
        self.assertEqual(mock_args.export_metadata_path, "custom_tags.json")

    def test_handle_strip_metadata(self):
        """Test stripping metadata while preserving ICC, DPI, and Orientation."""
        mock_image = MagicMock(spec=Image.Image)
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Artist: b"Jane Doe",
                piexif.ImageIFD.Orientation: 8,
            },
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
            "thumbnail": None,
        }
        mock_image.info = {
            "exif": piexif.dump(exif_dict),
            "icc_profile": b"icc_data",
            "dpi": (300, 300),
        }

        result_image = handle_strip_metadata(mock_image, "test.jpg", [], None)
        new_info = result_image.info

        self.assertIn("icc_profile", new_info)
        self.assertIn("dpi", new_info)
        self.assertIn("exif", new_info)

        # Check EXIF
        new_exif_dict = piexif.load(new_info["exif"])
        self.assertNotIn(piexif.ImageIFD.Artist, new_exif_dict["0th"])
        self.assertEqual(new_exif_dict["0th"][piexif.ImageIFD.Orientation], 8)

    def test_handle_set_metadata(self):
        """Test complete overwrite of metadata."""
        mock_image = MagicMock(spec=Image.Image)
        # Existing metadata
        mock_image.info = {
            "exif": piexif.dump({"0th": {piexif.ImageIFD.Copyright: b"Old Copyright"}})
        }

        # Overwrite with set
        handle_set_metadata(mock_image, "test.jpg", ["Artist=Jane Doe"], None)

        new_exif_dict = piexif.load(mock_image.info["exif"])
        self.assertEqual(new_exif_dict["0th"].get(piexif.ImageIFD.Artist), b"Jane Doe")
        self.assertNotIn(piexif.ImageIFD.Copyright, new_exif_dict["0th"])

    def test_handle_update_metadata(self):
        """Test merging new metadata with existing metadata."""
        mock_image = MagicMock(spec=Image.Image)
        # Existing metadata
        mock_image.info = {
            "exif": piexif.dump({"0th": {piexif.ImageIFD.Copyright: b"Old Copyright"}})
        }

        # Update with new tag
        handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane Doe"], None)

        new_exif_dict = piexif.load(mock_image.info["exif"])
        self.assertEqual(new_exif_dict["0th"].get(piexif.ImageIFD.Artist), b"Jane Doe")
        self.assertEqual(
            new_exif_dict["0th"].get(piexif.ImageIFD.Copyright), b"Old Copyright"
        )

    def test_handle_author_and_copyright(self):
        """Test the quick-access author and copyright handlers."""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.info = {}
        mock_args = MagicMock()

        handle_author(mock_image, "test.jpg", ["Jane Doe"], mock_args)
        new_exif_dict = piexif.load(mock_image.info["exif"])
        self.assertEqual(new_exif_dict["0th"].get(piexif.ImageIFD.Artist), b"Jane Doe")

        handle_copyright(mock_image, "test.jpg", ["2026 Dealien"], mock_args)
        new_exif_dict = piexif.load(mock_image.info["exif"])
        self.assertEqual(
            new_exif_dict["0th"].get(piexif.ImageIFD.Copyright), b"2026 Dealien"
        )

    def test_handle_copy_metadata(self):
        """Test copying EXIF from a source image."""
        # Create a real temporary source image with EXIF
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jpg") as f:
            temp_path = f.name

        try:
            # Create a simple image and save it with EXIF
            src_img = Image.new("RGB", (10, 10))
            exif_dict = {"0th": {piexif.ImageIFD.Artist: b"Copied Artist"}}
            exif_bytes = piexif.dump(exif_dict)
            src_img.save(temp_path, "JPEG", exif=exif_bytes)

            mock_image = MagicMock(spec=Image.Image)
            mock_image.info = {}

            # Use a mock that doesn't interfere with hasattr/getattr expectations
            class MockArgs:
                pass

            mock_args = MockArgs()

            handle_copy_metadata(mock_image, "target.jpg", [temp_path], mock_args)

            new_exif_dict = piexif.load(mock_image.info["exif"])
            self.assertEqual(
                new_exif_dict["0th"].get(piexif.ImageIFD.Artist), b"Copied Artist"
            )
        finally:
            os.remove(temp_path)
