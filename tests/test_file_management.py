import os
import sys
import shutil
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from file_management import move_images_to_subdirectory

class TestFileManagement(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a dummy file for testing."""
        self.test_dir = "test_images"
        self.test_file = "test_image.png"
        # Create a dummy file
        with open(self.test_file, "w") as f:
            f.write("dummy content")

    def tearDown(self):
        """Clean up the temporary directory and dummy file."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_move_images_to_subdirectory(self):
        """Test that image files are moved to the correct subdirectory."""
        move_images_to_subdirectory(self.test_dir)
        # Check that the file was moved
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, self.test_file)))
        # Check that the original file is gone
        self.assertFalse(os.path.exists(self.test_file))

if __name__ == '__main__':
    unittest.main()
