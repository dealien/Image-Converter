"""Entry point for the Image Converter CLI application.

Handles command-line arguments and either launches the interactive menu
or executes CLI-specified image processing operations.
"""

import argparse
import glob
import os
import sys
from pathlib import Path

import pillow_avif  # noqa: F401
from pi_heif import register_heif_opener
from rich.console import Console

from .file_management import move_images_to_subdirectory
from .processing import process_images_and_save

# Register HEIF opener to support HEIC/HEIF files
register_heif_opener()

# Create a global console instance to be shared across modules
console = Console()


class StoreInOrder(argparse.Action):
    """Custom argparse Action to store arguments in the order they are provided."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Stores the argument destination and values in the 'ordered_operations' list.

        Args:
            parser (argparse.ArgumentParser): The ArgumentParser object.
            namespace (argparse.Namespace): The Namespace object that will hold the parsed attributes.
            values (str | list): The parsed argument values.
            option_string (str, optional): The option string that was used to invoke this action. Defaults to None.

        """
        if not hasattr(namespace, "ordered_operations"):
            setattr(namespace, "ordered_operations", [])
        if values is None:
            norm_values = []
        elif isinstance(values, (str, int, float)):
            norm_values = [values]

        else:
            norm_values = values
        namespace.ordered_operations.append({"dest": self.dest, "values": norm_values})


# --- Main Execution ---


def main():
    """Main entry point for the image conversion CLI application.

    Parses command-line arguments and executes the specified image processing
    pipeline. If no arguments are provided or the `--menu` flag is used, it
    launches the interactive menu interface. By default, the program searches
    for images in the `Base Images/` directory if no specific file path is given.
    """
    # If --menu is used or no arguments are provided, start the menu.

    if "--menu" in sys.argv or len(sys.argv) == 1:
        # Import dynamically to prevent circular dependency issues with tests
        from .menu import interactive_menu

        interactive_menu()
        return

    parser = argparse.ArgumentParser(
        description="A versatile command-line image manipulation tool."
    )
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        default=None,
        help='The image file or pattern to process (e.g., "input.jpg", "images/*.png"). '
        'If omitted or set to "*", searches in the "Base Images/" directory by default.',
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Start the application in interactive menu mode.",
    )
    # Initialize ordered_operations to an empty list by default
    parser.set_defaults(ordered_operations=[])

    parser.add_argument(
        "-bg",
        "--remove-background",
        dest="remove_background",
        action=StoreInOrder,
        nargs=0,
        help="Remove image background.",
    )
    parser.add_argument(
        "-s",
        "--scale",
        dest="scale",
        action=StoreInOrder,
        nargs="+",
        help="Scale image by factor (e.g., '1.5x') or to a specific size (e.g., '400px 300px').",
    )
    parser.add_argument(
        "--resample",
        type=str,
        default="bilinear",
        choices=["nearest", "bilinear", "bicubic", "lanczos"],
        help="Resampling filter for scaling.",
    )
    parser.add_argument(
        "-i",
        "--invert",
        dest="invert",
        action=StoreInOrder,
        nargs=0,
        help="Invert the colors of an image.",
    )
    parser.add_argument(
        "-g",
        "--grayscale",
        dest="grayscale",
        action=StoreInOrder,
        nargs=0,
        help="Convert an image to grayscale.",
    )
    parser.add_argument(
        "--flip",
        dest="flip",
        action=StoreInOrder,
        type=str,
        choices=["horizontal", "vertical", "both"],
        help="Flip image horizontally, vertically, or both.",
    )
    parser.add_argument(
        "--edge-detection",
        dest="edge_detection",
        action=StoreInOrder,
        type=str,
        choices=["sobel", "canny", "kovalevsky"],
        help="Apply edge detection using the specified method.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=50,
        help="Threshold for the Kovalevsky edge detection method (0-255).",
    )
    parser.add_argument(
        "--brightness",
        dest="brightness",
        action=StoreInOrder,
        type=int,
        help="Adjust brightness (-100 to 100).",
    )
    parser.add_argument(
        "--contrast",
        dest="contrast",
        action=StoreInOrder,
        type=int,
        help="Adjust contrast (-100 to 100).",
    )
    parser.add_argument(
        "--saturation",
        dest="saturation",
        action=StoreInOrder,
        type=int,
        help="Adjust saturation (-100 to 100).",
    )
    parser.add_argument(
        "--blur",
        dest="blur",
        action=StoreInOrder,
        type=float,
        help="Apply Gaussian Blur with specified radius.",
    )
    parser.add_argument(
        "--sharpen",
        dest="sharpen",
        action=StoreInOrder,
        type=int,
        help="Resulting image sharpness (0-100).",
    )
    parser.add_argument(
        "--color-balance",
        dest="color_balance",
        action=StoreInOrder,
        nargs=3,
        type=float,
        help="Adjust R, G, B channels (e.g., 1.2 0.8 1.0).",
    )
    parser.add_argument(
        "--hue-rotation",
        dest="hue_rotation",
        action=StoreInOrder,
        type=int,
        help="Rotate hue by specified degrees (0-360).",
    )
    parser.add_argument(
        "--posterize",
        dest="posterize",
        action=StoreInOrder,
        type=int,
        help="Reduce color depth to N bits (1-8).",
    )
    parser.add_argument(
        "--border",
        dest="border",
        action=StoreInOrder,
        nargs=3,
        help="Add border: thickness (int) color (str) position (expand/inside).",
    )
    parser.add_argument(
        "--vignette",
        dest="vignette",
        action=StoreInOrder,
        type=int,
        help="Apply vignette effect with intensity (0-100).",
    )
    parser.add_argument(
        "--rotate",
        dest="rotate",
        action=StoreInOrder,
        type=int,
        help="Rotate image by 90-degree increments (0, 90, 180, 270).",
    )
    # Global output options (not piped)
    parser.add_argument(
        "--format",
        action="append",
        type=str,
        help="Output format (e.g. png, jpg, webp, heic, avif). Can be used multiple times.",
    )
    parser.add_argument(
        "--quality",
        action="append",
        type=int,
        help="Output quality (1-100) per format. Evaluated in order of --format arguments.",
    )

    args = parser.parse_args()

    # Check if any action was specified (operations or explicit formats)
    if not args.ordered_operations and not args.format:
        console.print(
            "[yellow]No actions specified. Please provide at least one operation flag (e.g., --invert, --scale 2x) "
            "or an output format (e.g., --format webp).[/]\n"
            "[dim white]To see all available options, run with --help or use the interactive --menu.[/]"
        )
        return

    move_images_to_subdirectory("Base Images")
    images_data = []
    image_path_pattern = (
        args.file if args.file and args.file != "*" else "Base Images/*"
    )

    try:
        filepaths = glob.glob(image_path_pattern)
        if not filepaths:
            console.print(
                f"[yellow]No files found matching pattern: '{image_path_pattern}'[/]\n"
                f"[dim white]Please verify the file path or ensure images exist in the target directory.[/]"
            )
            console.print(
                "[dim white]Please check the path or place some images in the specified directory and try again.[/]"
            )
            return
        for filepath in filepaths:
            if os.path.isfile(filepath):
                filename = Path(filepath).name
                images_data.append([filename, filepath])
    except Exception as e:
        console.print(f"[red]Error while loading file(s): {e}[/]")
        return

    process_images_and_save(images_data, args.ordered_operations, args)


if __name__ == "__main__":
    main()
