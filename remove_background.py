import os
from rembg import remove
from PIL import Image, ImageOps, ImageChops, ImageFile


def remove_background(image_input: ImageFile, opt_border_width: int = 0):
    """
    Remove the background from an image.

    :param image_input: The image to modify.
    :param opt_border_width: The number of pixels to be removed from the border.
    :return:
    """

    # Add white border
    image_input = ImageOps.expand(image_input, border=int(opt_border_width))
    # Removes background
    output = remove(image_input)
    # Removes white border that .expand() added
    output = trim(output)
    return output


def trim(image):
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox)
    return image
