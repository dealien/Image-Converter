import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock


def setup_mocks():
    """Mock dependencies that might not be installed."""
    # Mock PIL and submodules
    mock_pil = MagicMock()
    sys.modules["PIL"] = mock_pil
    sys.modules["PIL.Image"] = mock_pil.Image
    sys.modules["PIL.ImageFile"] = mock_pil.ImageFile
    sys.modules["PIL.ImageFilter"] = mock_pil.ImageFilter
    sys.modules["PIL.ImageEnhance"] = mock_pil.ImageEnhance
    sys.modules["PIL.ImageOps"] = mock_pil.ImageOps
    sys.modules["PIL.ImageDraw"] = mock_pil.ImageDraw
    sys.modules["PIL.ImageFont"] = mock_pil.ImageFont

    # Mock rembg
    sys.modules["rembg"] = MagicMock()


if __name__ == "__main__":
    setup_mocks()

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        # Load the test from the specified file
        loader = unittest.TestLoader()
        if test_file.endswith(".py"):
            # Import the module from file path
            module_name = os.path.basename(test_file)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            suite = loader.loadTestsFromModule(module)
        else:
            suite = loader.loadTestsFromName(test_file)

        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        sys.exit(not result.wasSuccessful())
    else:
        # Default to running all tests in tests/ directory that don't depend heavily on PIL actually working
        # But for this task, we'll probably just run our specific test files.
        print("Please provide a test file to run.")
        sys.exit(1)
