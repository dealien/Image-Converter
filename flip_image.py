from PIL import Image, ImageFile


def flip_image(image_input: ImageFile, direction: str):
    """
    Flip an image horizontally, vertically, or both.

    :param image_input: The image to modify.
    :param direction: The direction to flip the image. Can be 'horizontal', 'vertical', or 'both'.
    :return: The flipped image.
    """
    if direction == 'horizontal':
        return image_input.transpose(Image.FLIP_LEFT_RIGHT)
    elif direction == 'vertical':
        return image_input.transpose(Image.FLIP_TOP_BOTTOM)
    elif direction == 'both':
        return image_input.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)
    else:
        raise ValueError(f"Invalid flip direction: {direction}. Available directions: 'horizontal', 'vertical', 'both'")
