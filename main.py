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

        # Normalize values: None -> empty list, str/int -> list[str/int], keep list as-is
        if values is None:
            norm_values = []
        elif isinstance(values, (str, int)):
            norm_values = [values]
        else:
            norm_values = values

        namespace.ordered_operations.append({'dest': self.dest, 'values': norm_values})

# --- Operation Handlers ---

def handle_flip(image, image_name, values, args):
    print(f'Flipping "{image_name}" {values[0]}...')
    return flip_image(image, values[0])

def handle_scale(image, image_name, values, args):
    scale_params = values
    scale_factor = None
    new_size = None
    if len(scale_params) == 1 and scale_params[0].lower().endswith('x'):
        try:
            scale_factor = float(scale_params[0][:-1])
        except ValueError:
            print(f"Invalid scale factor: {scale_params[0]}")
            return image # Return original image on error
    elif len(scale_params) == 2:
        try:
            width = int(scale_params[0].lower().replace('px', ''))
            height = int(scale_params[1].lower().replace('px', ''))
            new_size = (width, height)
        except ValueError:
            print(f"Invalid size format: {scale_params}")
            return image
    else:
        print("Invalid format for --scale argument. Use '1.5x' or '400px 300px'.")
        return image

    print(f'Scaling "{image_name}"...')
    return scale_image(image, scale_factor=scale_factor, new_size=new_size,
                       resample_filter=args.resample)

def handle_remove_background(image, image_name, values, args):
    print(f'Removing background of "{image_name}"...')
    return remove_background(image)

def handle_invert(image, image_name, values, args):
    print(f'Inverting the colors of "{image_name}"...')
    return invert_colors(image)

def handle_grayscale(image, image_name, values, args):
    print(f'Converting "{image_name}" to grayscale...')
    return grayscale(image)

def handle_edge_detection(image, image_name, values, args):
    method = values[0]
    if method == 'kovalevsky':
        print(f'Applying {method} edge detection to "{image_name}" with threshold {args.threshold}...')
        return edge_detection(image, 'kovalevsky', args.threshold)
    else:
        print(f'Applying {method} edge detection to "{image_name}"...')
        return edge_detection(image, method)

def handle_brightness(image, image_name, values, args):
    print(f'Adjusting brightness of "{image_name}" by {values[0]}...')
    return adjust_brightness(image, values[0])

def handle_contrast(image, image_name, values, args):
    print(f'Adjusting contrast of "{image_name}" by {values[0]}...')
    return adjust_contrast(image, values[0])

def handle_saturation(image, image_name, values, args):
    print(f'Adjusting saturation of "{image_name}" by {values[0]}...')
    return adjust_saturation(image, values[0])


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

    if not hasattr(args, 'ordered_operations'):
        print('No actions specified. Exiting...')
        import sys
        sys.exit(2)

    operation_handlers = {
        'flip': handle_flip,
        'scale': handle_scale,
        'remove_background': handle_remove_background,
        'invert': handle_invert,
        'grayscale': handle_grayscale,
        'edge_detection': handle_edge_detection,
        'brightness': handle_brightness,
        'contrast': handle_contrast,
        'saturation': handle_saturation,
    }

    move_images_to_subdirectory('Base Images')

    if not args.file or args.file == '*':
        images = []
        for root, dirs, files in os.walk('Base Images/'):
            for file in files:
                filepath = os.path.join(root, file)
                with Image.open(filepath) as input_image:
                    input_image.load()
                    images.append([file, input_image.copy()])
    else:
        try:
            images = []
            for filepath in glob.glob(args.file):
                with Image.open(filepath) as input_image:
                    input_image.load()
                    filename = Path(filepath).name
                    images.append([filename, input_image.copy()])
        except Exception as e:
            print(f'Error while loading file: {e}')
            exit()

    for image_data in images:
        output_image = image_data[1]
        image_name = image_data[0]

        for operation in args.ordered_operations:
            op_dest = operation['dest']
            op_values = operation['values']

            handler = operation_handlers.get(op_dest)
            if handler:
                output_image = handler(output_image, image_name, op_values, args)

        if not os.path.exists('Output/'):
            os.makedirs('Output/')
        output_image.save("Output/.tmp.png")
        filename = Path(image_name).stem
        os.replace("Output/.tmp.png", 'Output/' + filename + '.png')
        print("Image saved successfully:", 'Output/' + filename + '.png')


if __name__ == "__main__":
    main()
