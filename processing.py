import os
from pathlib import Path
import logging


from flip_image import flip_image
from image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    edge_detection,
    grayscale,
    invert_colors,
    apply_blur,
    apply_sharpen,
    apply_color_balance,
    rotate_hue,
    apply_posterize,
    apply_border,
    rotate_image,
)
from remove_background import remove_background
from scale_image import scale_image

logger = logging.getLogger(__name__)

# --- Operation Handlers ---


def handle_flip(image, image_name, values, args):
    logger.info(f"  > Flipping {values[0]}...")
    return flip_image(image, values[0])


def handle_scale(image, image_name, values, args):
    scale_params = values
    scale_factor = None
    new_size = None

    if len(scale_params) == 1:
        # Handle single argument as scale factor (e.g., "1.5", "0.5x")
        try:
            # Remove 'x' if present, then parse float
            clean_param = scale_params[0].lower().replace("x", "")
            scale_factor = float(clean_param)
        except ValueError:
            logger.error(f"Invalid scale factor: {scale_params[0]}")
            return image

    elif len(scale_params) == 2:
        try:
            width = int(scale_params[0].lower().replace("px", ""))
            height = int(scale_params[1].lower().replace("px", ""))
            new_size = (width, height)
        except ValueError:
            # If parsing as explicit size fails, check if it was intended as something else?
            # But 2 args implies list of dimensions typically.
            logger.error(f"Invalid size format: {scale_params}")
            return image
    else:
        logger.error(
            "Invalid format for --scale argument. Use '1.5', '1.5x' or '400px 300px'."
        )
        return image
    if scale_factor is not None:
        logger.info(f"  > Scaling by factor: {scale_factor}...")
    elif new_size is not None:
        logger.info(f"  > Scaling to dimensions: {new_size}...")
    else:
        logger.info("  > Scaling...")
    return scale_image(
        image,
        scale_factor=scale_factor,
        new_size=new_size,
        resample_filter=args.resample,
    )


def handle_remove_background(image, image_name, values, args):
    logger.info("  > Removing background...")
    return remove_background(image)


def handle_invert(image, image_name, values, args):
    logger.info("  > Inverting colors...")
    return invert_colors(image)


def handle_grayscale(image, image_name, values, args):
    logger.info("  > Converting to grayscale...")
    return grayscale(image)


def handle_edge_detection(image, image_name, values, args):
    method = values[0]
    if method == "kovalevsky":
        logger.info(
            f"  > Applying {method} edge detection (threshold: {args.threshold})..."
        )
        return edge_detection(image, "kovalevsky", args.threshold)
    else:
        logger.info(f"  > Applying {method} edge detection...")
        return edge_detection(image, method)


def handle_brightness(image, image_name, values, args):
    logger.info(f"  > Adjusting brightness by {values[0]}...")
    return adjust_brightness(image, values[0])


def handle_contrast(image, image_name, values, args):
    logger.info(f"  > Adjusting contrast by {values[0]}...")
    return adjust_contrast(image, values[0])


def handle_saturation(image, image_name, values, args):
    logger.info(f"  > Adjusting saturation by {values[0]}...")
    return adjust_saturation(image, values[0])


def handle_blur(image, image_name, values, args):
    logger.info(f"  > Applying Gaussian Blur (radius: {values[0]})...")
    return apply_blur(image, values[0])


def handle_sharpen(image, image_name, values, args):
    logger.info(f"  > Applying Sharpen (intensity: {values[0]})...")
    return apply_sharpen(image, values[0])


def handle_color_balance(image, image_name, values, args):
    logger.info(
        f"  > Applying Color Balance (R:{values[0]}, G:{values[1]}, B:{values[2]})..."
    )
    return apply_color_balance(image, values[0], values[1], values[2])


def handle_hue_rotation(image, image_name, values, args):
    logger.info(f"  > Rotating Hue by {values[0]} degrees...")
    return rotate_hue(image, values[0])


def handle_posterize(image, image_name, values, args):
    logger.info(f"  > Posterizing to {values[0]} bits...")
    return apply_posterize(image, values[0])


def handle_border(image, image_name, values, args):
    """
    values: [thickness, color, position]
    Expects thickness to be int (or convertible string), color (str), position (str).
    """
    try:
        thickness = int(values[0])
        color = values[1]
        position = values[2]
        logger.info(f"  > Adding border: {thickness}px, {color}, {position}")
        return apply_border(image, thickness, color, position)
    except (ValueError, IndexError) as e:
        logger.error(f"  [ERROR] Invalid border arguments: {values}. Error: {e}")
        return image


def handle_rotate(image, image_name, values, args):
    """
    values: [angle]
    Expects angle to be int.
    """
    logger.info(f"  > Rotating image by {values[0]} degrees...")
    return rotate_image(image, values[0])


# --- Core Processing Function ---


def process_images_and_save(images_data, ordered_operations, cli_args):
    operation_handlers = {
        "flip": handle_flip,
        "scale": handle_scale,
        "remove_background": handle_remove_background,
        "invert": handle_invert,
        "grayscale": handle_grayscale,
        "edge_detection": handle_edge_detection,
        "brightness": handle_brightness,
        "contrast": handle_contrast,
        "saturation": handle_saturation,
        "blur": handle_blur,
        "sharpen": handle_sharpen,
        "color_balance": handle_color_balance,
        "hue_rotation": handle_hue_rotation,
        "posterize": handle_posterize,
        "border": handle_border,
        "rotate": handle_rotate,
    }

    if not images_data:
        logger.info("No images to process.")
        return
    logger.info(f"\nProcessing {len(images_data)} image(s)...")
    total_images = len(images_data)
    for i, (image_name, image_to_process) in enumerate(images_data, 1):
        logger.info(f"\n{'=' * 50}")
        logger.info(f'[{i}/{total_images}] Processing: "{image_name}"')
        logger.info(f"{'=' * 50}")

        temp_path = None  # Initialize temp_path to None
        try:
            output_image = image_to_process.copy()
            for operation in ordered_operations:
                op_dest = operation["dest"]
                op_values = operation.get("values", [])
                handler = operation_handlers.get(op_dest)
                if handler:
                    output_image = handler(
                        output_image, image_name, op_values, cli_args
                    )
            if not os.path.exists("Output/"):
                os.makedirs("Output/")
            output_filename = Path(image_name).stem + ".png"
            output_path = os.path.join("Output", output_filename)
            temp_path = os.path.join("Output", f".tmp.{output_filename}")
            output_image.save(temp_path, "PNG")
            os.replace(temp_path, output_path)
            logger.info(f"  [SUCCESS] Saved to: {output_path}")
        except Exception:
            logger.exception(
                f"  [ERROR] An error occurred while processing {image_name}"
            )
            continue

        finally:
            # Ensure the temp file is removed if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as e:
                    logger.error(f"Error removing temp file {temp_path}: {e}")
