"""Functions for removing backgrounds from images.

Provides functionality to remove image backgrounds using `rembg`
and trim empty space from the resulting image.
"""

from rembg import remove
from PIL import Image, ImageOps, ImageChops


def remove_background(
    image_input: Image.Image, opt_border_width: int = 0
) -> Image.Image:
    """Remove the background from an image.

    Args:
        image_input (Image.Image): The image to modify.
        opt_border_width (int, optional): The number of pixels to be added and later removed from the border. Defaults to 0.

    Returns:
        Image.Image: The image with its background removed and trimmed.

    """
    # Add white border
    image_input = ImageOps.expand(image_input, border=int(opt_border_width))
    # Removes background
    output = remove(image_input)
    # Removes white border that .expand() added
    output = trim(output)
    return output


def trim(image: Image.Image) -> Image.Image:
    """Trim empty background space from an image by finding its bounding box.

    Args:
        image (Image.Image): The image to be trimmed.

    Returns:
        Image.Image: The cropped image if a bounding box was found, otherwise the original image.

    """
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox)
    return image
