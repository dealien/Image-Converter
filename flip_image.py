"""Functions for flipping images.

Provides a function to flip an image horizontally, vertically, or both.
"""

from PIL import Image, ImageFile


def flip_image(image_input: ImageFile, direction: str):
    """Flip an image horizontally, vertically, or both.

    Args:
        image_input (ImageFile): The image to modify.
        direction (str): The direction to flip the image. Can be 'horizontal', 'vertical', or 'both'.

    Returns:
        Image.Image: The flipped image.

    Raises:
        ValueError: If an invalid direction is provided.
    """
    if direction == "horizontal":
        return image_input.transpose(Image.FLIP_LEFT_RIGHT)
    elif direction == "vertical":
        return image_input.transpose(Image.FLIP_TOP_BOTTOM)
    elif direction == "both":
        return image_input.transpose(Image.FLIP_LEFT_RIGHT).transpose(
            Image.FLIP_TOP_BOTTOM
        )
    else:
        raise ValueError(
            f"Invalid flip direction: {direction}. Available directions: 'horizontal', 'vertical', 'both'"
        )
