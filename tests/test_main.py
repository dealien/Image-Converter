import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import main


class TestMain(unittest.TestCase):

    @patch('main.remove_background')
    @patch('main.move_images_to_subdirectory')
    def test_wildcard_file_argument(self, mock_move, mock_remove_background):
        """Test that wildcard file arguments are handled correctly."""
        # Mock the image processing functions
        mock_remove_background.return_value = Image.new('RGBA', (10, 10))

        # There are 2 images with "Tree" in the name
        with patch.object(sys, 'argv', ['main.py', '-bg', 'tests/test_images/Tree*.png']):
            main()

        # Check that remove_background was called for each wildcard match
        self.assertEqual(mock_remove_background.call_count, 2)

    @patch('main.remove_background')
    @patch('main.move_images_to_subdirectory')
    @patch('os.walk')
    def test_all_files_argument(self, mock_walk, mock_move, mock_remove_background):
        """Test the wildcard '*' to process all files in the directory."""
        # Mock the image processing functions
        mock_remove_background.return_value = Image.new('RGBA', (10, 10))

        # Mock os.walk to return a list of files
        mock_walk.return_value = [
            ('Base Images/', [], ['file1.png', 'file2.png', 'file3.png', 'file4.png'])
        ]

        # Mock Image.open to return a dummy image
        with patch('main.Image.open', MagicMock(return_value=Image.new('RGB', (10, 10)))):
            with patch.object(sys, 'argv', ['main.py', '-bg', '*']):
                main()

        # Check that remove_background was called for each file in the directory
        self.assertEqual(mock_remove_background.call_count, 4)


if __name__ == '__main__':
    unittest.main()
