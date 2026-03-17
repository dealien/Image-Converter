import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock


def setup_mocks():
    """Mock dependencies that might not be installed."""
    mock_pil = MagicMock()
    sys.modules["PIL"] = mock_pil
    sys.modules["PIL.Image"] = mock_pil.Image
    sys.modules["PIL.ImageFile"] = mock_pil.ImageFile
    sys.modules["PIL.ImageFilter"] = mock_pil.ImageFilter
    sys.modules["PIL.ImageEnhance"] = mock_pil.ImageEnhance
    sys.modules["PIL.ImageOps"] = mock_pil.ImageOps
    sys.modules["PIL.ImageDraw"] = mock_pil.ImageDraw
    sys.modules["PIL.ImageFont"] = mock_pil.ImageFont
    sys.modules["PIL.ImageChops"] = mock_pil.ImageChops

    sys.modules["rembg"] = MagicMock()
    sys.modules["pytest"] = MagicMock()
    sys.modules["pytest.fixture"] = lambda f: f
    sys.modules["questionary"] = MagicMock()

    sys.modules["rich"] = MagicMock()
    sys.modules["rich.table"] = MagicMock()
    sys.modules["rich.text"] = MagicMock()
    sys.modules["rich.panel"] = MagicMock()
    sys.modules["rich.box"] = MagicMock()
    sys.modules["rich.console"] = MagicMock()
    sys.modules["rich.progress"] = MagicMock()
    sys.modules["rich.rule"] = MagicMock()
    sys.modules["rich.live"] = MagicMock()

    sys.modules["prompt_toolkit"] = MagicMock()
    sys.modules["prompt_toolkit.formatted_text"] = MagicMock()
    sys.modules["prompt_toolkit.lexers"] = MagicMock()
    sys.modules["prompt_toolkit.validation"] = MagicMock()
    sys.modules["prompt_toolkit.styles"] = MagicMock()
    sys.modules["prompt_toolkit.application"] = MagicMock()
    sys.modules["prompt_toolkit.application.current"] = MagicMock()

    sys.modules["coloredlogs"] = MagicMock()
    sys.modules["skimage"] = MagicMock()
    sys.modules["skimage.filters"] = MagicMock()
    sys.modules["skimage.feature"] = MagicMock()
    sys.modules["numpy"] = MagicMock()


if __name__ == "__main__":
    setup_mocks()

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        # Load the test from the specified file
        loader = unittest.TestLoader()
        if test_file.endswith(".py"):
            if not os.path.exists(test_file):
                print(f"Error: Test file {test_file} does not exist")
                sys.exit(1)

            # Import the module from file path
            module_name = os.path.basename(test_file)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            if spec is None or spec.loader is None:
                print(f"Error: Could not load test file {test_file}")
                sys.exit(1)
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
