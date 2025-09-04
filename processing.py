import os
from pathlib import Path

from PIL import Image

from file_management import move_images_to_subdirectory
from flip_image import flip_image
from image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    edge_detection,
    grayscale,
    invert_colors,
)
from remove_background import remove_background
from scale_image import scale_image

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
            return image
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
    return scale_image(image, scale_factor=scale_factor, new_size=new_size, resample_filter=args.resample)

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
        print(f'Applying {method} edge detection to "{image_naem}" with threshold {args.threshold}...')
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

# --- Core Processing Function ---

def process_images_and_save(images_data, ordered_operations, cli_args):
    operation_handlers = {
        'flip': handle_flip, 'scale': handle_scale, 'remove_background': handle_remove_background,
        'invert': handle_invert, 'grayscale': handle_grayscale, 'edge_detection': handle_edge_detection,
        'brightness': handle_brightness, 'contrast': handle_contrast, 'saturation': handle_saturation,
    }
    if not images_data:
        print("No images to process.")
        return
    print(f"\nProcessing {len(images_data)} image(s)...")
    for image_name, image_to_process in images_data:
        output_image = image_to_process.copy()
        for operation in ordered_operations:
            op_dest = operation['dest']
            op_values = operation.get('values', [])
            handler = operation_handlers.get(op_dest)
            if handler:
                output_image = handler(output_image, image_name, op_values, cli_args)
        if not os.path.exists('Output/'):
            os.makedirs('Output/')
        output_filename = Path(image_name).stem + '.png'
        output_path = os.path.join('Output', output_filename)
        temp_path = os.path.join('Output', '.tmp.png')
        output_image.save(temp_path, 'PNG')
        os.replace(temp_path, output_path)
        print(f"Image saved successfully: {output_path}")
