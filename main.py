import argparse
import glob
import os
import sys
from pathlib import Path

from PIL import Image

from file_management import move_images_to_subdirectory
from processing import process_images_and_save


class StoreInOrder(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, 'ordered_operations'):
            setattr(namespace, 'ordered_operations', [])
        if values is None:
            norm_values = []
        elif isinstance(values, (str, int)):
            norm_values = [values]
        else:
            norm_values = values
        namespace.ordered_operations.append({'dest': self.dest, 'values': norm_values})

# --- Main Execution ---

def main():
    # If --menu is used or no arguments are provided, start the menu.
    if '--menu' in sys.argv or len(sys.argv) == 1:
        # Import dynamically to prevent circular dependency issues with tests
        from menu import interactive_menu
        interactive_menu()
        return

    parser = argparse.ArgumentParser(description="A versatile command-line image manipulation tool.")
    parser.add_argument('file', type=str, nargs='?', default=None, help='The image file or pattern to process (e.g., "input.jpg", "images/*.png").')
    parser.add_argument('--menu', action='store_true', help='Start the application in interactive menu mode.')
    parser.add_argument('-bg', '--remove-background', dest='remove_background', action=StoreInOrder, nargs=0, help='Remove image background.')
    parser.add_argument('-s', '--scale', dest='scale', action=StoreInOrder, nargs='+', help="Scale image by factor (e.g., '1.5x') or to a specific size (e.g., '400px 300px').")
    parser.add_argument('--resample', type=str, default='bilinear', choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], help='Resampling filter for scaling.')
    parser.add_argument('-i', '--invert', dest='invert', action=StoreInOrder, nargs=0, help='Invert the colors of an image.')
    parser.add_argument('-g', '--grayscale', dest='grayscale', action=StoreInOrder, nargs=0, help='Convert an image to grayscale.')
    parser.add_argument('--flip', dest='flip', action=StoreInOrder, type=str, choices=['horizontal', 'vertical', 'both'], help='Flip image horizontally, vertically, or both.')
    parser.add_argument('--edge-detection', dest='edge_detection', action=StoreInOrder, type=str, choices=['sobel', 'canny', 'kovalevsky'], help='Apply edge detection using the specified method.')
    parser.add_argument('--threshold', type=int, default=50, help='Threshold for the Kovalevsky edge detection method (0-255).')
    parser.add_argument('--brightness', dest='brightness', action=StoreInOrder, type=int, help='Adjust brightness (-100 to 100).')
    parser.add_argument('--contrast', dest='contrast', action=StoreInOrder, type=int, help='Adjust contrast (-100 to 100).')
    parser.add_argument('--saturation', dest='saturation', action=StoreInOrder, type=int, help='Adjust saturation (-100 to 100).')

    args = parser.parse_args()

    if not hasattr(args, 'ordered_operations'):
        print('No actions specified. To see available options, run with --help.')
        return

    move_images_to_subdirectory('Base Images')
    images_data = []
    image_path_pattern = args.file if args.file and args.file != '*' else 'Base Images/*'

    try:
        filepaths = glob.glob(image_path_pattern)
        if not filepaths:
            print(f"No files found matching pattern: {image_path_pattern}")
            return
        for filepath in filepaths:
            if os.path.isfile(filepath):
                with Image.open(filepath) as input_image:
                    input_image.load()
                    filename = Path(filepath).name
                    images_data.append([filename, input_image.copy()])
    except Exception as e:
        print(f'Error while loading file(s): {e}')
        return

    process_images_and_save(images_data, args.ordered_operations, args)

if __name__ == "__main__":
    main()
