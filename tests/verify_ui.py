"""
Verify UI Functionality

This script is used to quickly verify that the UI is working
correctly using a small set of test images and simple operations.

It is not intended to be a comprehensive test, but rather a quick
verification that the UI appears as expected.
"""

import sys
from pathlib import Path

sys.path.append(str(Path.cwd()))

from image_converter.processing import process_images_and_save


class MockArgs:
    def __init__(self):
        self.resample = "bicubic"
        self.threshold = 50


test_images = [
    ("Hill Castle.png", "tests/test_images/Hill Castle.png"),
    ("Spacecraft.png", "tests/test_images/Spacecraft.png"),
    ("Tree Clear Sky 1.png", "tests/test_images/Tree Clear Sky 1.png"),
]

operations = [
    {"dest": "flip", "values": ["horizontal"]},
    {"dest": "grayscale", "values": []},
]

if __name__ == "__main__":
    process_images_and_save(test_images, operations, MockArgs())
