import argparse
from file_management import *
from remove_background import *
from scale_image import *
from image_filters import (invert_colors, grayscale, edge_detection,
                           adjust_brightness, adjust_contrast, adjust_saturation)
from flip_image import *
import glob
from pathlib import Path


class StoreInOrder(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, 'ordered_operations'):
            setattr(namespace, 'ordered_operations', [])
        namespace.ordered_operations.append({'dest': self.dest, 'values': values})


def main():
    parser = argparse.ArgumentParser(description="Process command line arguments.")
    parser.add_argument('file', type=str, nargs='?', default=None, help='the image file path')
    parser.add_argument('-bg', '--remove-background', dest='remove_background', action=StoreInOrder, nargs=0,
                        help='remove image background')
    parser.add_argument('-s', '--scale', dest='scale', action=StoreInOrder, nargs='+',
                        help='scale image by factor (e.g., 1.5x) or to fit within a bounding box (e.g., 400px 300px)')
    parser.add_argument('--resample', type=str, default='bilinear',
                        choices=['nearest', 'bilinear', 'bicubic', 'lanczos'],
                        help='resampling filter to use for scaling')
    parser.add_argument('-i', '--invert', dest='invert', action=StoreInOrder, nargs=0,
                        help='inverts the colors of an image')
    parser.add_argument('-g', '--grayscale', dest='grayscale', action=StoreInOrder, nargs=0,
                        help='converts an image to grayscale')
    parser.add_argument('--flip', dest='flip', action=StoreInOrder, type=str,
                        choices=['horizontal', 'vertical', 'both'],
                        help='flip image horizontally, vertically, or both')
    parser.add_argument('--edge-detection', dest='edge_detection', action=StoreInOrder, type=str,
                        choices=['sobel', 'canny', 'kovalevsky'],
                        help='apply edge detection using the specified method')
    parser.add_argument('--threshold', type=int, default=50,
                        help='threshold for the Kovalevsky edge detection method')
    parser.add_argument('--brightness', dest='brightness', action=StoreInOrder, type=int,
                        help='adjust brightness (-100 to 100)')
    parser.add_argument('--contrast', dest='contrast', action=StoreInOrder, type=int,
                        help='adjust contrast (-100 to 100)')
    parser.add_argument('--saturation', dest='saturation', action=StoreInOrder, type=int,
                        help='adjust saturation (-100 to 100)')
    args = parser.parse_args()

    # TODO: If no arguments are passed, switch to a menu

    if not hasattr(args, 'ordered_operations'):
        print('No actions specified. Exiting...')
        import sys
        sys.exit(2)  # Early exit with non-zero status

    # Move images to the Base Images directory
    move_images_to_subdirectory('Base Images')

    if not args.file or args.file == '*':  # For all files in "Base Images" directory
        images = []
        for root, dirs, files in os.walk('Base Images/'):
            for file in files:
                filepath = os.path.join(root, file)
                with Image.open(filepath) as input_image:
                    input_image.load()
                    images.append([file, input_image.copy()])
                # print([file, input_image])
    else:  # For specified file(s)
        try:
            images = []
            # Use glob to handle wildcards in the file path
            for filepath in glob.glob(args.file):
                with Image.open(filepath) as input_image:
                    input_image.load()
                    # Extract just the filename for display/saving purposes
                    filename = Path(filepath).name
                    images.append([filename, input_image.copy()])
        except Exception as e:
            # If no files are found or an error occurs, print an error and exit
            print(f'Error while loading file: {e}')
            exit()

    for image in images:
        output_image = image[1]

        for operation in args.ordered_operations:
            op_dest = operation['dest']
            op_values = operation['values']

            if op_dest == 'flip':
                print(f'Flipping "{image[0]}" {op_values}...')
                output_image = flip_image(output_image, op_values)
            elif op_dest == 'scale':
                scale_params = op_values
                scale_factor = None
                new_size = None
                if len(scale_params) == 1 and scale_params[0].lower().endswith('x'):
                    try:
                        scale_factor = float(scale_params[0][:-1])
                    except ValueError:
                        print(f"Invalid scale factor: {scale_params[0]}")
                        continue
                elif len(scale_params) == 2:
                    try:
                        width = int(scale_params[0].lower().replace('px', ''))
                        height = int(scale_params[1].lower().replace('px', ''))
                        new_size = (width, height)
                    except ValueError:
                        print(f"Invalid size format: {scale_params}")
                        continue
                else:
                    print("Invalid format for --scale argument. Use '1.5x' or '400px 300px'.")
                    continue

                print(f'Scaling "{image[0]}"...')
                output_image = scale_image(output_image, scale_factor=scale_factor, new_size=new_size,
                                           resample_filter=args.resample)
            elif op_dest == 'remove_background':
                print(f'Removing background of "{image[0]}"...')
                output_image = remove_background(output_image)
            elif op_dest == 'invert':
                print(f'Inverting the colors of "{image[0]}"...')
                output_image = invert_colors(output_image)
            elif op_dest == 'grayscale':
                print(f'Converting "{image[0]}" to grayscale...')
                output_image = grayscale(output_image)
            elif op_dest == 'edge_detection':
                if op_values == 'kovalevsky':
                    print(
                        f'Applying {op_values} edge detection to "{image[0]}" with threshold {args.threshold}...')
                    output_image = edge_detection(output_image, 'kovalevsky', args.threshold)
                else:
                    print(f'Applying {op_values} edge detection to "{image[0]}"...')
                    output_image = edge_detection(output_image, op_values)
            elif op_dest == 'brightness':
                print(f'Adjusting brightness of "{image[0]}" by {op_values}...')
                output_image = adjust_brightness(output_image, op_values)
            elif op_dest == 'contrast':
                print(f'Adjusting contrast of "{image[0]}" by {op_values}...')
                output_image = adjust_contrast(output_image, op_values)
            elif op_dest == 'saturation':
                print(f'Adjusting saturation of "{image[0]}" by {op_values}...')
                output_image = adjust_saturation(output_image, op_values)

        # Saves final output image
        if not os.path.exists('Output/'):
            os.makedirs('Output/')
        output_image.save("Output/.tmp.png")
        filename = Path(image[0]).stem
        os.replace("Output/.tmp.png", 'Output/' + filename + '.png')
        print("Image saved successfully:", 'Output/' + filename + '.png')


if __name__ == "__main__":
    main()
