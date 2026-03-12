import os
import sys
import shutil
import unittest
from unittest.mock import patch
import io

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from file_management import move_images_to_subdirectory  # noqa: E402


class TestFileManagement(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory and a dummy file for testing."""
        self.test_dir = "tests/test_images"
        self.test_file = os.path.join(self.test_dir, "Hill Castle.png")
        self.base_dir = "test_base_images"
        self.moved_file_path = os.path.join(self.base_dir, "Hill Castle.png")

        # Ensure the base directory exists and is empty
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        os.makedirs(self.base_dir)

        # Create a dummy file in the root to be moved
        shutil.copy(self.test_file, "Hill Castle.png")

    def tearDown(self):
        """Clean up the temporary directory and dummy file."""
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        if os.path.exists("Hill Castle.png"):
            os.remove("Hill Castle.png")

    def test_move_images_to_subdirectory(self):
        """Test that image files are moved to the correct subdirectory."""
        move_images_to_subdirectory(self.base_dir)
        # Check that the file was moved
        self.assertTrue(os.path.exists(self.moved_file_path))
        # Check that the original file is gone
        self.assertFalse(os.path.exists("Hill Castle.png"))

    @patch("file_management.os.listdir")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_move_images_to_subdirectory_error_handling(
        self, mock_stdout, mock_listdir
    ):
        """Test that move_images_to_subdirectory handles and prints errors correctly."""
        # Setup mock to raise an exception
        error_message = "Mocked listdir error"
        mock_listdir.side_effect = Exception(error_message)

        # Call the function
        move_images_to_subdirectory(self.base_dir)

        # Assert output
        output = mock_stdout.getvalue()
        self.assertIn(f"An error occurred: {error_message}", output)

    @patch("file_management.os.path.exists")
    @patch("file_management.os.makedirs")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_move_images_to_subdirectory_makedirs_error(
        self, mock_stdout, mock_makedirs, mock_exists
    ):
        """Test that move_images_to_subdirectory handles and prints makedirs errors correctly."""
        # Setup mock to ensure makedirs is called, and then raise an exception
        mock_exists.return_value = False
        error_message = "Mocked makedirs error"
        mock_makedirs.side_effect = Exception(error_message)

        # Call the function
        move_images_to_subdirectory(self.base_dir)

        # Assert output
        output = mock_stdout.getvalue()
        self.assertIn(f"An error occurred: {error_message}", output)


if __name__ == "__main__":
    unittest.main()
