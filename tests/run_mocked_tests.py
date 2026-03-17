import importlib.util
import os
import sys
import unittest
from unittest.mock import MagicMock


def setup_mocks():
    """Mock dependencies that might not be installed."""
    # Mock PIL and submodules
    mock_pil = MagicMock()

    # Configure Image.new to return an object with a size attribute
    def mock_new(mode, size, color=None):
        img = MagicMock()
        img.size = size
        img.mode = mode
        img.width = size[0]
        img.height = size[1]
        # Make it behave like a PIL Image for point() etc if needed
        img.point.return_value = img
        img.convert.return_value = img
        img.getpixel.return_value = (0, 0, 0)
        img.getbands.return_value = list(mode)

        def mock_resize(new_size, resample=None):
            new_img = mock_new(img.mode, new_size)
            return new_img
        img.resize.side_effect = mock_resize

        def mock_copy():
            return mock_new(img.mode, img.size)
        img.copy.side_effect = mock_copy

        def mock_getchannel(channel):
            c = MagicMock()
            c.point.return_value = c
            return c
        img.getchannel.side_effect = mock_getchannel

        def mock_rotate(angle, expand=False):
            if expand and angle in [90, 270]:
                return mock_new(img.mode, (img.height, img.width))
            return mock_new(img.mode, img.size)
        img.rotate.side_effect = mock_rotate

        return img

    mock_pil.Image.new.side_effect = mock_new
    mock_pil.Image.fromarray.side_effect = lambda arr, mode="RGB": mock_new(mode, (10, 10))
    mock_pil.Image.Resampling.NEAREST = 0
    mock_pil.Image.Resampling.BILINEAR = 1
    mock_pil.Image.Resampling.BICUBIC = 2
    mock_pil.Image.Resampling.LANCZOS = 3

    mock_pil.ImageOps.grayscale.side_effect = lambda img: mock_new("L", img.size)
    mock_pil.ImageOps.invert.side_effect = lambda img: mock_new(img.mode, img.size)
    mock_pil.ImageOps.posterize.side_effect = lambda img, bits: mock_new(img.mode, img.size)
    mock_pil.ImageOps.expand.side_effect = lambda img, border=0, fill=0: mock_new(img.mode, (img.width + 2*border, img.height + 2*border))

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

    # Mock rich
    sys.modules["rich"] = MagicMock()
    sys.modules["rich.console"] = MagicMock()
    sys.modules["rich.panel"] = MagicMock()
    sys.modules["rich.progress"] = MagicMock()
    sys.modules["rich.rule"] = MagicMock()
    sys.modules["rich.table"] = MagicMock()
    sys.modules["rich.text"] = MagicMock()
    sys.modules["rich.box"] = MagicMock()

    # Mock coloredlogs
    sys.modules["coloredlogs"] = MagicMock()

    # Mock questionary
    sys.modules["questionary"] = MagicMock()

    # Mock prompt_toolkit
    sys.modules["prompt_toolkit"] = MagicMock()

    # Mock numpy
    mock_np = MagicMock()
    sys.modules["numpy"] = mock_np

    # Mock skimage
    sys.modules["skimage"] = MagicMock()
    sys.modules["skimage.feature"] = MagicMock()
    sys.modules["skimage.filters"] = MagicMock()


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
