from PIL import Image, ImageFile

RESAMPLE_FILTERS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}

def scale_image(image_input: ImageFile, scale_factor: float = None, new_size: tuple = None, resample_filter: str = "bilinear"):
    """
    Scale an image up or down, preserving aspect ratio.

    :param image_input: The image to modify.
    :param scale_factor: The factor to scale the image by.
    :param new_size: The new size of the image as a tuple (width, height) to fit within.
    :param resample_filter: The resampling filter to use.
    :return: The scaled image.
    """
    original_width, original_height = image_input.size
    new_width, new_height = original_width, original_height

    if scale_factor is not None:
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
    elif new_size is not None:
        target_width, target_height = new_size
        ratio = min(target_width / original_width, target_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

    resample = RESAMPLE_FILTERS.get(resample_filter.lower())
    if resample is None:
        raise ValueError(f"Invalid resample filter: {resample_filter}. Available filters: {list(RESAMPLE_FILTERS.keys())}")

    scaled_image = image_input.resize((new_width, new_height), resample=resample)
    return scaled_image
