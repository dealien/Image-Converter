import os
import time
import unittest
from unittest.mock import MagicMock, patch
import sys
import concurrent.futures

# Mock dependencies
sys.modules["questionary"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["rich"] = MagicMock()
sys.modules["rich.table"] = MagicMock()
sys.modules["rich.text"] = MagicMock()
sys.modules["rich.panel"] = MagicMock()
sys.modules["rich.box"] = MagicMock()
sys.modules["rich.console"] = MagicMock()

import rich_menu


# Define a mock Image.open that takes some time
def mock_open(path):
    time.sleep(0.01)  # 10ms delay per image
    mock_img = MagicMock()
    mock_img.width = 100
    mock_img.height = 100
    mock_img.format = "PNG"
    # To support "with Image.open(path) as img:"
    mock_img.__enter__.return_value = mock_img
    return mock_img


rich_menu.Image.open.side_effect = mock_open


def benchmark_sequential(image_files, image_dir):
    start_time = time.time()
    images_data = []
    for f in image_files:
        path = os.path.join(image_dir, f)
        # Using the private function directly for sequential baseline
        dims, size_str, fmt = rich_menu._get_image_metadata(path)
        images_data.append(
            {"name": f, "path": path, "dims": dims, "size": size_str, "fmt": fmt}
        )
    end_time = time.time()
    return end_time - start_time


def benchmark_refactored(image_files, image_dir):
    # We need to mock questionary.checkbox(...).ask() as it is called in run_image_selector
    with patch("questionary.checkbox") as mock_checkbox:
        mock_checkbox.return_value.ask.return_value = []
        start_time = time.time()
        rich_menu.run_image_selector(image_files, image_dir)
        end_time = time.time()
    return end_time - start_time


if __name__ == "__main__":
    num_images = 100
    image_dir = "test_dir"
    image_files = [f"test_{i}.png" for i in range(num_images)]

    # Mock os.path.getsize
    with unittest.mock.patch("os.path.getsize", return_value=1024):
        print(f"Benchmarking for {num_images} images with 10ms artificial delay...")

        seq_duration = benchmark_sequential(image_files, image_dir)
        print(f"Sequential duration (baseline): {seq_duration:.4f} seconds")

        ref_duration = benchmark_refactored(image_files, image_dir)
        print(f"Refactored duration (parallel): {ref_duration:.4f} seconds")

        improvement = (seq_duration - ref_duration) / seq_duration * 100
        print(f"Improvement: {improvement:.2f}%")
