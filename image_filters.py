from PIL import Image, ImageOps

def invert_colors(image: Image.Image) -> Image.Image:
    """
    Inverts the colors of an image.
    :param image: The input image.
    :return: The image with inverted colors.
    """
    return ImageOps.invert(image.convert('RGB'))

def grayscale(image: Image.Image) -> Image.Image:
    """
    Converts an image to grayscale.
    :param image: The input image.
    :return: The grayscale image.
    """
    return ImageOps.grayscale(image)
