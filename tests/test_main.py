import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image, ImageChops
import glob

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main function that we want to test
from main import main
# Import the image filter functions to create an expected image
from image_filters import invert_colors, grayscale
# We need to patch functions in the 'processing' module now
import processing


class TestMain(unittest.TestCase):

    # Patch the function where it is looked up: in the 'processing' module
    @patch('processing.remove_background')
    @patch('main.move_images_to_subdirectory')
    def test_wildcard_file_argument(self, mock_move, mock_remove_background):
        """Test that wildcard file arguments are handled correctly."""
        mock_remove_background.return_value = Image.new('RGBA', (10, 10))

        # There are 2 images with "Tree" in the name in the test assets
        with patch.object(sys, 'argv', ['main.py', '-bg', 'tests/test_images/Tree*.png']):
            main()

        # Check that the mocked function was called for each matching file
        self.assertEqual(mock_remove_background.call_count, 2)

    # Patch the function where it is looked up: in the 'processing' module
    @patch('processing.remove_background')
    @patch('main.move_images_to_subdirectory')
    @patch('glob.glob')
    @patch('os.path.isfile')
    def test_all_files_argument(self, mock_isfile, mock_glob, mock_move, mock_remove_background):
        """Test the wildcard '*' to process all files in the directory."""
        mock_remove_background.return_value = Image.new('RGBA', (10, 10))

        # Mock glob.glob to return a list of dummy file paths
        mock_glob.return_value = ['Base Images/file1.png', 'Base Images/file2.png', 'Base Images/file3.png', 'Base Images/file4.png']
        # Mock os.path.isfile to always return True for the dummy paths
        mock_isfile.return_value = True

        # Image.open is called from within main.py, so patching it there is correct
        with patch('main.Image.open', MagicMock(return_value=Image.new('RGB', (10, 10)))):
            with patch.object(sys, 'argv', ['main.py', '-bg', '*']):
                main()

        # Check that the mocked function was called for each file
        self.assertEqual(mock_remove_background.call_count, 4)


    def test_multiple_operations_in_order(self):
        """Test that multiple operations are applied in the correct order."""
        input_image_path = 'tests/test_images/Tree Clear Sky 1.png'
        output_image_path = 'Output/Tree Clear Sky 1.png'

        # Ensure the output directory exists
        os.makedirs('Output', exist_ok=True)

        # Create the expected image by applying operations directly
        with Image.open(input_image_path) as img:
            # It's important to apply operations in the same order as the command
            expected_image = grayscale(invert_colors(img.copy()))

        # Run the main function with command line arguments
        # We patch move_images_to_subdirectory to prevent it from moving our test images
        with patch('main.move_images_to_subdirectory'):
            with patch.object(sys, 'argv', ['main.py', input_image_path, '--invert', '--grayscale']):
                main()

        # Check that the output file was created
        self.assertTrue(os.path.exists(output_image_path))

        # Compare the actual output with the expected image
        with Image.open(output_image_path) as actual_image:
            # Convert both to RGB to ensure comparison is valid
            diff = ImageChops.difference(expected_image.convert('RGB'), actual_image.convert('RGB'))
            self.assertIsNone(diff.getbbox(), "The output image is not as expected.")

        # Clean up the created file
        if os.path.exists(output_image_path):
            os.remove(output_image_path)


if __name__ == '__main__':
    unittest.main()
