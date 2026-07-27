import argparse
import os
import shutil
import unittest

from PIL import Image

from image_converter import processing


class TestMetadataPreservation(unittest.TestCase):
    def setUp(self):
        self.output_dir = "Output"
        self.test_dir = "tests/temp_metadata_test"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_metadata_preservation_png_to_jpg(self):
        # Create a source image with specific DPI and EXIF
        img_path = os.path.join(self.test_dir, "source.png")
        img = Image.new("RGB", (100, 100), color="red")

        # Set DPI
        dpi = (300, 300)

        # Set some EXIF data (Note: PNG doesn't support EXIF the same way JPEG does in Pillow,
        # but we can test DPI preservation across formats)
        img.save(img_path, "PNG", dpi=dpi)

        # Process: Convert to JPEG
        images_data = [("source.png", img_path)]
        args = argparse.Namespace(format=["jpg"], quality=[90])

        processing.process_images_and_save(images_data, [], args)

        output_path = os.path.join(self.output_dir, "source.jpg")
        self.assertTrue(os.path.exists(output_path))

        with Image.open(output_path) as out_img:
            # Check DPI
            self.assertEqual(out_img.info.get("dpi"), (300, 300))

    def test_exif_preservation_jpg(self):
        # Create a source JPEG with EXIF
        img_path = os.path.join(self.test_dir, "source_exif.jpg")
        img = Image.new("RGB", (100, 100), color="blue")

        # Add basic EXIF
        exif = img.getexif()
        exif[0x0110] = "Test Model"  # Model tag

        img.save(img_path, "JPEG", exif=exif)

        # Process: Invert and save as JPEG again
        images_data = [("source_exif.jpg", img_path)]
        args = argparse.Namespace(format=["jpg"], quality=[95])
        ops = [{"dest": "invert", "values": []}]

        processing.process_images_and_save(images_data, ops, args)

        output_path = os.path.join(self.output_dir, "source_exif.jpg")
        self.assertTrue(os.path.exists(output_path))

        with Image.open(output_path) as out_img:
            out_exif = out_img.getexif()
            self.assertEqual(out_exif.get(0x0110), "Test Model")


if __name__ == "__main__":
    unittest.main()
