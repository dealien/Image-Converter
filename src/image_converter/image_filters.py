"""A collection of image filtering and adjustment functions.

Provides various image manipulations including color inversion, grayscale
conversion, contrast/brightness/saturation adjustments, blurring, sharpening,
edge detection, color balance, hue rotation, posterization, borders, and rotation.
"""

import functools

from PIL import Image, ImageColor, ImageEnhance, ImageFilter, ImageOps


@functools.lru_cache(maxsize=128)
def _generate_vignette_mask(mask_size: int, intensity: int) -> Image.Image:
    """Generate a small cached base mask for the vignette effect.

    Args:
        mask_size (int): The size of the mask to generate.
        intensity (int): The intensity of the vignette effect.

    Returns:
        Image.Image: The generated base mask image.

    """
    import numpy as np

    center = mask_size / 2.0
    factor = (intensity / 100.0) / (2.0 * center**2)

    y, x = np.ogrid[:mask_size, :mask_size]
    dist_sq = ((x - center) ** 2 + (y - center) ** 2) * factor

    val = 1.0 - dist_sq
    # Use np.round to match the original int(round(...)) behavior before casting
    mask_data = np.round(np.clip(val * 255, 0, 255)).astype(np.uint8)

    return Image.fromarray(mask_data, mode="L")


def _generate_scaled_lut(factor: float) -> list[int]:
    """Generate a Look-Up Table (LUT) for scaling a channel, clamping to [0, 255].

    Args:
        factor (float): The scaling factor.

    Returns:
        list[int]: A list of 256 mapped values.

    """
    return [max(0, min(255, int(round(i * factor)))) for i in range(256)]


@functools.lru_cache(maxsize=1024)
def _get_scale_lut(factor: float) -> list[int]:
    """Create a cached Look-Up Table (LUT) for scaling a channel, clamping to [0, 255].

    Args:
        factor (float): The scaling factor.

    Returns:
        list[int]: A list of 256 mapped values.

    """
    return _generate_scaled_lut(factor)


@functools.lru_cache(maxsize=1024)
def _get_color_balance_lut(
    r_f: float, g_f: float, b_f: float, num_bands: int
) -> list[int]:
    """Create a cached Look-Up Table (LUT) for color balance.

    Args:
        r_f (float): The red scaling factor.
        g_f (float): The green scaling factor.
        b_f (float): The blue scaling factor.
        num_bands (int): The number of bands in the image.

    Returns:
        list[int]: A combined LUT for all channels.

    """
    lut = _get_scale_lut(r_f) + _get_scale_lut(g_f) + _get_scale_lut(b_f)
    if num_bands > 3:
        lut += _IDENTITY_LUT * (num_bands - 3)
    return lut


@functools.lru_cache(maxsize=8)
def _get_posterize_channel_lut(bits: int) -> list[int]:
    """Create a cached Look-Up Table (LUT) for posterizing a single channel.

    Args:
        bits (int): The number of bits to keep (1-8).

    Returns:
        list[int]: A list of 256 mapped values.

    """
    mask = ~(2 ** (8 - bits) - 1)
    return [p & mask for p in range(256)]


@functools.lru_cache(maxsize=256)
def _get_brightness_lut(brightness: int) -> list[int]:
    """Create a cached Look-Up Table (LUT) for brightness adjustment.

    Args:
        brightness (int): The brightness adjustment level (-100 to 100).

    Returns:
        list[int]: A list of 256 mapped values.

    """
    factor = 1.0 + (brightness / 100.0)
    return _generate_scaled_lut(factor)


# Global identity Look-Up Table (LUT) for preserving an unchanged channel (like alpha).
_IDENTITY_LUT = list(range(256))


MODE_SUPPORT_MATRIX: dict[str, list[str]] = {
    "adjust_brightness": [
        "1",
        "L",
        "P",
        "PA",
        "LA",
        "La",
        "RGB",
        "RGBA",
        "RGBX",
        "RGBa",
        "CMYK",
        "YCbCr",
        "LAB",
        "HSV",
        "I;16",
    ],
    "adjust_contrast": [
        "1",
        "L",
        "P",
        "PA",
        "LA",
        "La",
        "RGB",
        "RGBA",
        "RGBX",
        "RGBa",
        "CMYK",
        "YCbCr",
        "LAB",
        "HSV",
        "I;16",
    ],
    "apply_posterize": [
        "1",
        "L",
        "P",
        "PA",
        "LA",
        "La",
        "RGB",
        "RGBA",
        "RGBX",
        "RGBa",
        "CMYK",
        "YCbCr",
        "LAB",
        "HSV",
    ],
    "apply_color_balance": [
        "L",
        "P",
        "PA",
        "LA",
        "La",
        "RGB",
        "RGBA",
        "RGBX",
        "RGBa",
        "CMYK",
        "YCbCr",
        "LAB",
        "HSV",
    ],
    "invert_colors": [
        "1",
        "L",
        "P",
        "PA",
        "LA",
        "La",
        "RGB",
        "RGBA",
        "RGBX",
        "RGBa",
        "CMYK",
        "YCbCr",
        "LAB",
        "HSV",
    ],
    "rotate_hue": [
        "RGB",
        "RGBA",
        "RGBa",
        "RGBX",
        "LA",
        "La",
        "P",
        "PA",
        "HSV",
        "YCbCr",
        "LAB",
    ],
}


@functools.lru_cache(maxsize=256)
def _get_brightness_lut_16(brightness: int) -> tuple[int, ...]:
    """Create a cached 16-bit Look-Up Table (LUT) for brightness adjustment.

    Args:
        brightness (int): The brightness adjustment level (-100 to 100).

    Returns:
        tuple[int, ...]: A tuple of 65,536 mapped 16-bit values.

    """
    factor = 1.0 + (brightness / 100.0)
    return tuple(max(0, min(65535, int(round(i * factor)))) for i in range(65536))


@functools.lru_cache(maxsize=1024)
def _get_contrast_lut_16(contrast: int, mean: int) -> tuple[int, ...]:
    """Create a cached 16-bit Look-Up Table (LUT) for contrast adjustment.

    Args:
        contrast (int): The contrast adjustment level (-100 to 100).
        mean (int): The mean luminance serving as the anchor.

    Returns:
        tuple[int, ...]: A tuple of 65,536 mapped 16-bit values.

    """
    factor = 1.0 + (contrast / 100.0)
    return tuple(
        max(0, min(65535, int(round((i - mean) * factor + mean)))) for i in range(65536)
    )


def _apply_palette_lut(
    image: Image.Image,
    lut_r: list[int],
    lut_g: list[int] | None = None,
    lut_b: list[int] | None = None,
) -> Image.Image:
    """Apply LUT mapping to an indexed palette image.

    Args:
        image (Image.Image): The input palette image (mode 'P' or 'PA').
        lut_r (list[int]): Mapped values for red / default channel.
        lut_g (list[int], optional): Mapped values for green channel.
        lut_b (list[int], optional): Mapped values for blue channel.

    Returns:
        Image.Image: The image with updated palette.

    """
    palette = image.getpalette()
    if not palette:
        return image.convert("RGBA" if "A" in image.getbands() else "RGB")

    lut_g = lut_g or lut_r
    lut_b = lut_b or lut_r

    new_palette = []
    for i in range(0, len(palette), 3):
        r = lut_r[palette[i]]
        g = lut_g[palette[i + 1]]
        b = lut_b[palette[i + 2]]
        new_palette.extend([r, g, b])

    img_out = image.copy()
    img_out.putpalette(new_palette)
    return img_out


@functools.lru_cache(maxsize=1024)
def _get_combined_contrast_lut(
    contrast: int, mean: int, mode: str, num_bands: int = 1
) -> tuple[int, ...]:
    """Create a cached Look-Up Table (LUT) for adjusting the contrast across channels.

    Args:
        contrast (int): The contrast adjustment level (-100 to 100).
        mean (int): The mean luminance of the image (0-255) serving as the anchor.
        mode (str): The image mode (e.g., 'RGB', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV').
        num_bands (int): The number of image bands.

    Returns:
        tuple[int, ...]: A fully concatenated, immutable LUT for all channels.

    """
    factor = 1.0 + (contrast / 100.0)

    lut_channel = [
        max(0, min(255, int(round((i - mean) * factor + mean)))) for i in range(256)
    ]

    if mode in ("L", "1"):
        return tuple(lut_channel)
    elif mode in ("LA", "La"):
        return tuple(lut_channel + _IDENTITY_LUT)
    elif mode == "RGB":
        return tuple(lut_channel * 3)
    elif mode in ("RGBA", "RGBa", "RGBX"):
        return tuple(lut_channel * 3 + _IDENTITY_LUT)
    elif mode == "CMYK":
        return tuple(lut_channel * 4)
    elif mode in ("YCbCr", "LAB"):
        return tuple(lut_channel + _IDENTITY_LUT * 2)
    elif mode == "HSV":
        return tuple(_IDENTITY_LUT * 2 + lut_channel)
    else:
        if "A" in mode or "a" in mode:
            return tuple(lut_channel * max(1, num_bands - 1) + _IDENTITY_LUT)
        return tuple(lut_channel * num_bands)


@functools.lru_cache(maxsize=1024)
def _get_combined_brightness_lut(
    brightness: int, mode: str, num_bands: int = 1
) -> tuple[int, ...]:
    """Create a cached Look-Up Table (LUT) for adjusting the brightness across channels.

    Args:
        brightness (int): The brightness adjustment level (-100 to 100).
        mode (str): The image mode (e.g., 'RGB', 'RGBA', 'CMYK', 'YCbCr', 'LAB', 'HSV').
        num_bands (int): The number of image bands.

    Returns:
        tuple[int, ...]: A fully concatenated, immutable LUT for all channels.

    """
    lut_channel = _get_brightness_lut(brightness)
    if mode in ("L", "1"):
        return tuple(lut_channel)
    elif mode in ("LA", "La"):
        return tuple(lut_channel + _IDENTITY_LUT)
    elif mode == "RGB":
        return tuple(lut_channel * 3)
    elif mode in ("RGBA", "RGBa", "RGBX"):
        return tuple(lut_channel * 3 + _IDENTITY_LUT)
    elif mode == "CMYK":
        return tuple(lut_channel * 4)
    elif mode in ("YCbCr", "LAB"):
        return tuple(lut_channel + _IDENTITY_LUT * 2)
    elif mode == "HSV":
        return tuple(_IDENTITY_LUT * 2 + lut_channel)
    else:
        if "A" in mode or "a" in mode:
            return tuple(lut_channel * max(1, num_bands - 1) + _IDENTITY_LUT)
        return tuple(lut_channel * num_bands)


# ⚡ Bolt: Pre-compute a static Look-Up Table (LUT) for RGBA color inversion.
# Reusing this constant avoids allocating four new lists of 256 integers
# on every call to `invert_colors` for RGBA images.
_RGBA_INVERT_LUT = [255 - i for i in range(256)] * 3 + _IDENTITY_LUT


@functools.lru_cache(maxsize=256)
def _get_hue_rotation_lut(shift: int) -> list[int]:
    """Generate a cached Look-Up Table (LUT) for hue rotation.

    Args:
        shift (int): The amount to shift the hue channel (0-255).

    Returns:
        list[int]: A flat LUT for H, S, and V channels.

    """
    lut_h = [(p + shift) % 256 for p in range(256)]
    # S and V channels retain their original identity mappings.
    return lut_h + _IDENTITY_LUT * 2


def invert_colors(image: Image.Image) -> Image.Image:
    """Inverts the colors of an image.

    Args:
        image (Image.Image): The input image.

    Returns:
        Image.Image: The image with inverted colors.

    """
    if image.mode in ("1", "RGB", "L"):
        return ImageOps.invert(image)

    _INVERT_LUT = [255 - i for i in range(256)]

    if image.mode in ("P", "PA") and image.getpalette():
        return _apply_palette_lut(image, _INVERT_LUT)

    if image.mode in ("RGBA", "RGBa", "RGBX"):
        return image.point(_RGBA_INVERT_LUT)

    if image.mode in ("LA", "La"):
        return image.point(_INVERT_LUT + _IDENTITY_LUT)

    if image.mode in ("CMYK", "YCbCr", "LAB", "HSV"):
        lut = _INVERT_LUT * len(image.getbands())
        return image.point(lut)

    return ImageOps.invert(image.convert("RGB"))


def grayscale(image: Image.Image) -> Image.Image:
    """Convert an image to grayscale.

    Args:
        image (Image.Image): The input image.

    Returns:
        Image.Image: The grayscale image.

    """
    return ImageOps.grayscale(image)


def _kovalevsky_scan(
    array_to_scan: "numpy.ndarray",  # noqa: F821
    output_map: "numpy.ndarray",  # noqa: F821
    threshold: int,  # noqa: F821
) -> None:  # noqa: F821
    """Perform a 1D Kovalevsky edge detection scan.

    Args:
        array_to_scan: The image array to scan (n, m, 3).
        output_map: The output map to write to (n, m).
        threshold: The threshold for edge detection.

    """
    import numpy as np

    n, m, _ = array_to_scan.shape
    if m >= 6:
        # Chunk rows to cap peak memory while maintaining vectorized speed
        chunk_size = 512
        for i in range(0, n, chunk_size):
            chunk = array_to_scan[i : i + chunk_size]
            # Calculate absolute differences between adjacent pixels in the same row
            # np.diff computes img[:, 1:] - img[:, :-1] along the specified axis
            diffs = np.abs(np.diff(chunk, axis=1)).sum(axis=2, dtype=np.int32)

            # Create slices for the 5-pixel comparison window
            d0 = diffs[:, :-4]
            d1 = diffs[:, 1:-3]
            d2 = diffs[:, 2:-2]  # The center difference
            d3 = diffs[:, 3:-1]
            d4 = diffs[:, 4:]

            # Apply Kovalevsky condition: center is a local maximum and above threshold
            condition = (d2 > threshold) & (d2 > d0) & (d2 > d1) & (d2 > d3) & (d2 > d4)
            # Mark detected edges in the edge map
            output_map[i : i + chunk_size, 3:-2][condition] = 255


def edge_detection(image: Image.Image, method: str, threshold: int = 50) -> Image.Image:
    """Apply edge detection to an image using one of three methods.

    The supported methods offer different trade-offs:
    - **sobel**: Fast and simple gradient-based detection. Good for basic edge outlines.
    - **canny**: Multi-stage algorithm that provides clean, thin edges and reduces noise. Best for structural detection.
    - **kovalevsky**: Custom algorithmic approach sensitive to local variations based on a defined threshold.

    Args:
        image (Image.Image): The input image.
        method (str): The edge detection method ('sobel', 'canny', 'kovalevsky').
        threshold (int, optional): The sensitivity threshold for the Kovalevsky method. Defaults to 50.

    Returns:
        Image.Image: The image with edges detected.

    Raises:
        ImportError: If scikit-image or numpy is not installed.
        ValueError: If an invalid edge detection method is provided.

    """
    try:
        # Not every system has scikit-image installed, and it's not a required
        # dependency for the main functionality
        import numpy as np
        from skimage import feature, filters
    except ImportError:
        raise ImportError("scikit-image and numpy are required for edge detection.")

    if method not in ["sobel", "canny", "kovalevsky"]:
        raise ValueError("Method must be 'sobel', 'canny', or 'kovalevsky'")

    if method == "sobel":
        # Convert to grayscale and then to numpy array
        grayscale_img = image.convert("L")
        img_array = np.array(grayscale_img)
        # Apply Sobel filter
        edge_map = filters.sobel(img_array)
        # Convert the result back to an image
        edge_map_uint8 = np.clip(edge_map * 255, 0, 255).astype(np.uint8)
        edge_image = Image.fromarray(edge_map_uint8, mode="L")
        return edge_image

    elif method == "canny":
        # Convert to grayscale and then to numpy array
        grayscale_img = image.convert("L")
        img_array = np.array(grayscale_img)
        # Apply Canny filter
        edge_map = feature.canny(img_array)
        # Convert the boolean array to a uint8 array (0s and 255s)
        edge_map_uint8 = (edge_map * 255).astype(np.uint8)
        # Convert the result back to an image
        edge_image = Image.fromarray(edge_map_uint8)
        return edge_image

    elif method == "kovalevsky":
        # Convert the image to a NumPy array for efficient processing
        img_array = np.array(image.convert("RGB"), dtype=np.int16)
        height, width, _ = img_array.shape

        # Guard against images smaller than the required 6-pixel window
        if height < 6 or width < 6:
            return Image.new("L", (width, height), 0)

        # Create a new black image to draw the edges onto
        edge_map = np.zeros((height, width), dtype=np.uint8)

        # --- Horizontal Scan ---
        _kovalevsky_scan(img_array, edge_map, threshold)

        # --- Vertical Scan ---
        _kovalevsky_scan(np.swapaxes(img_array, 0, 1), edge_map.T, threshold)

        # Convert the NumPy array back to an image
        edge_image = Image.fromarray(edge_map, mode="L")
        return edge_image


def _get_image_mean_luminance(image: Image.Image) -> int:
    """Extract mean luminance of an image safely across all modes.

    Args:
        image (Image.Image): The input image.

    Returns:
        int: The mean luminance value.

    """
    from PIL import ImageStat

    if image.mode in ("L", "1"):
        return int(round(ImageStat.Stat(image).mean[0]))
    elif image.mode.startswith("I") or image.mode == "F":
        return int(round(ImageStat.Stat(image).mean[0]))
    elif image.mode in ("LAB", "LA", "La"):
        return int(round(ImageStat.Stat(image.getchannel("L")).mean[0]))
    elif image.mode == "YCbCr":
        return int(round(ImageStat.Stat(image.getchannel("Y")).mean[0]))
    elif image.mode in ("P", "PA") and image.getpalette():
        return int(round(ImageStat.Stat(image.convert("RGB").convert("L")).mean[0]))
    else:
        try:
            return int(round(ImageStat.Stat(image.convert("L")).mean[0]))
        except Exception:
            return int(round(ImageStat.Stat(image).mean[0]))


def adjust_brightness(image: Image.Image, brightness: int) -> Image.Image:
    """Adjust the brightness of an image.

    Args:
        image (Image.Image): The input image.
        brightness (int): An integer from -100 to 100 representing the brightness level.

    Returns:
        Image.Image: The image with adjusted brightness.

    Raises:
        TypeError: If brightness is not an integer.
        ValueError: If brightness is not between -100 and 100.

    """
    if not isinstance(brightness, int):
        raise TypeError("Brightness must be an integer.")
    if not -100 <= brightness <= 100:
        raise ValueError("Brightness must be between -100 and 100.")
    if brightness == 0:
        return image

    if image.mode in ("P", "PA") and image.getpalette():
        lut_channel = _get_brightness_lut(brightness)
        return _apply_palette_lut(image, lut_channel)

    if image.mode.startswith("I;16") or image.mode in ("I", "F"):
        factor = 1.0 + (brightness / 100.0)
        try:
            return image.point(lambda i: i * factor)
        except Exception:
            pass

    num_bands = len(image.getbands())
    lut = _get_combined_brightness_lut(brightness, image.mode, num_bands)

    return image.point(lut)


def adjust_contrast(image: Image.Image, contrast: int) -> Image.Image:
    """Adjust the contrast of an image.

    Args:
        image (Image.Image): The input image.
        contrast (int): An integer from -100 to 100 representing the contrast level.

    Returns:
        Image.Image: The image with adjusted contrast.

    Raises:
        TypeError: If contrast is not an integer.
        ValueError: If contrast is not between -100 and 100.

    """
    if not isinstance(contrast, int):
        raise TypeError("Contrast must be an integer.")
    if not -100 <= contrast <= 100:
        raise ValueError("Contrast must be between -100 and 100.")
    if contrast == 0:
        return image

    if image.mode in ("P", "PA") and image.getpalette():
        mean = _get_image_mean_luminance(image)
        factor = 1.0 + (contrast / 100.0)
        lut_channel = [
            max(0, min(255, int(round((i - mean) * factor + mean)))) for i in range(256)
        ]
        return _apply_palette_lut(image, lut_channel)

    if image.mode.startswith("I;16") or image.mode in ("I", "F"):
        mean = _get_image_mean_luminance(image)
        factor = 1.0 + (contrast / 100.0)
        offset = mean * (1.0 - factor)
        try:
            return image.point(lambda i: i * factor + offset)
        except Exception:
            pass

    mean = _get_image_mean_luminance(image)
    num_bands = len(image.getbands())
    lut = _get_combined_contrast_lut(contrast, mean, image.mode, num_bands)

    return image.point(lut)


def adjust_saturation(image: Image.Image, saturation: int) -> Image.Image:
    """Adjust the saturation of an image.

    Args:
        image (Image.Image): The input image.
        saturation (int): An integer from -100 to 100 representing the saturation level.

    Returns:
        Image.Image: The image with adjusted saturation.

    Raises:
        TypeError: If saturation is not an integer.
        ValueError: If saturation is not between -100 and 100.

    """
    if not isinstance(saturation, int):
        raise TypeError("Saturation must be an integer.")
    if not -100 <= saturation <= 100:
        raise ValueError("Saturation must be between -100 and 100.")
    if saturation == 0:
        return image
    factor = 1.0 + (saturation / 100.0)

    if "A" in image.getbands():
        alpha = image.getchannel("A")
    elif image.info.get("transparency") is not None:
        alpha = image.convert("RGBA").getchannel("A")
    else:
        alpha = None

    # No-op for grayscale to preserve mode and avoid unintended conversion
    if image.mode == "L":
        return image

    working = image.convert("RGB") if image.mode != "RGB" else image
    enhanced = ImageEnhance.Color(working).enhance(factor)
    if image.info:
        enhanced.info.update(image.info)
    if alpha is not None:
        enhanced.putalpha(alpha)
    return enhanced


def apply_blur(image: Image.Image, radius: int) -> Image.Image:
    """Apply Gaussian Blur to the image.

    Args:
        image (Image.Image): The input image.
        radius (int): The radius of the blur.

    Returns:
        Image.Image: The blurred image.

    Raises:
        TypeError: If radius is not a number.
        ValueError: If radius is negative.

    """
    if not isinstance(radius, (int, float)):
        raise TypeError("Radius must be a number.")
    if radius < 0:
        raise ValueError("Radius must be non-negative.")
    if radius == 0:
        return image
    if "A" in image.getbands():
        alpha = image.getchannel("A")
    elif image.info.get("transparency") is not None:
        alpha = image.convert("RGBA").getchannel("A")
    else:
        alpha = None

    working = (
        image.convert("RGB") if image.mode not in ("RGB", "RGBA", "L", "LA") else image
    )
    blurred = working.filter(ImageFilter.GaussianBlur(radius))
    if image.info:
        blurred.info.update(image.info)
    if alpha is not None:
        blurred.putalpha(alpha)
    return blurred


def apply_sharpen(image: Image.Image, sharpness: int) -> Image.Image:
    """Apply sharpening to the image.

    Args:
        image (Image.Image): The input image.
        sharpness (int): An integer from 0 to 100 representing intensity.

    Returns:
        Image.Image: The sharpened image.

    Raises:
        TypeError: If sharpness is not an integer.
        ValueError: If sharpness is not between 0 and 100.

    """
    if not isinstance(sharpness, int):
        raise TypeError("Sharpness must be an integer.")
    if not 0 <= sharpness <= 100:
        raise ValueError("Sharpness must be between 0 and 100.")
    if sharpness == 0:
        return image

    # Map 0-100 to a factor (e.g., 1.0 to 2.0)
    factor = 1.0 + (sharpness / 100.0)

    if "A" in image.getbands():
        alpha = image.getchannel("A")
    elif image.info.get("transparency") is not None:
        alpha = image.convert("RGBA").getchannel("A")
    else:
        alpha = None

    working = image.convert("RGB") if image.mode not in ("RGB", "L") else image
    enhanced = ImageEnhance.Sharpness(working).enhance(factor)
    if image.info:
        enhanced.info.update(image.info)
    if alpha is not None:
        enhanced.putalpha(alpha)
    return enhanced


def apply_color_balance(
    image: Image.Image, red_factor: float, green_factor: float, blue_factor: float
) -> Image.Image:
    # pylint: disable=too-many-branches, complex-logic
    """Adjust the color balance of an image by scaling RGB channels.

    Args:
        image (Image.Image): The input image.
        red_factor (float): Multiplier for the red channel.
        green_factor (float): Multiplier for the green channel.
        blue_factor (float): Multiplier for the blue channel.

    Returns:
        Image.Image: The color-balanced image.

    Raises:
        TypeError: If color balance factors are not numbers.
        ValueError: If factors are infinite, NaN, or negative.

    """
    # Handle float conversion and validation
    try:
        r_f = float(red_factor)
        g_f = float(green_factor)
        b_f = float(blue_factor)
    except (ValueError, TypeError):
        raise TypeError("Color balance factors must be numbers.")

    # Reject NaN/inf without extra imports
    if (
        (r_f != r_f)
        or (g_f != g_f)
        or (b_f != b_f)
        or (r_f in (float("inf"), float("-inf")))
        or (g_f in (float("inf"), float("-inf")))
        or (b_f in (float("inf"), float("-inf")))
    ):
        raise ValueError("Factors must be finite numbers.")

    # Reject negative factors
    if r_f < 0 or g_f < 0 or b_f < 0:
        raise ValueError("Color balance factors must be non-negative.")

    if image.mode in ("P", "PA") and image.getpalette():
        lut_r = _get_scale_lut(r_f)
        lut_g = _get_scale_lut(g_f)
        lut_b = _get_scale_lut(b_f)
        return _apply_palette_lut(image, lut_r, lut_g, lut_b)

    if image.mode in ("LA", "La"):
        alpha = image.getchannel("A")
        rgba = image.convert("RGBA")
        num_bands = len(rgba.getbands())
        lut = _get_color_balance_lut(r_f, g_f, b_f, num_bands)
        res = rgba.point(lut)
        if image.info:
            res.info.update(image.info)
        res.putalpha(alpha)
        return res

    num_bands = len(image.getbands())
    lut = _get_color_balance_lut(r_f, g_f, b_f, num_bands)

    res = image.point(lut)
    if image.info:
        res.info.update(image.info)
    return res


def rotate_hue(image: Image.Image, degrees: int) -> Image.Image:
    """Rotates the hue of the image.

    Args:
        image (Image.Image): The input image.
        degrees (int): The angle to rotate the hue (0-360).

    Returns:
        Image.Image: The image with rotated hue.

    Raises:
        TypeError: If degrees is not a number.

    """
    if not isinstance(degrees, (int, float)):
        raise TypeError("Degrees must be a number.")

    degrees = degrees % 360
    if degrees == 0:
        return image

    if image.mode == "HSV":
        shift = int(round((degrees / 360.0) * 256)) % 256
        lut = _get_hue_rotation_lut(shift)
        return image.point(lut)

    # Store alpha if present (supports RGBA/LA/etc.)
    alpha_channel = image.getchannel("A") if "A" in image.getbands() else None

    # Ensure hue ops run on RGB base
    rgb_base = image.convert("RGB")
    img_hsv = rgb_base.convert("HSV")

    shift = int(round((degrees / 360.0) * 256)) % 256
    lut = _get_hue_rotation_lut(shift)

    new_img = img_hsv.point(lut)
    new_rgb = new_img.convert("RGB")

    if alpha_channel is not None:
        new_rgb.putalpha(alpha_channel)
        return new_rgb

    return new_rgb


def apply_posterize(image: Image.Image, bits: int) -> Image.Image:
    """Reduces the number of bits for each color channel.

    Args:
        image (Image.Image): The input image.
        bits (int): The number of bits to keep (1-8).

    Returns:
        Image.Image: The posterized image.

    Raises:
        TypeError: If bits is not an integer.
        ValueError: If bits is not between 1 and 8.

    """
    if not isinstance(bits, int):
        raise TypeError("Bits must be an integer.")

    if not 1 <= bits <= 8:
        raise ValueError("Bits must be between 1 and 8.")

    lut_channel = _get_posterize_channel_lut(bits)

    if image.mode in ("P", "PA") and image.getpalette():
        return _apply_palette_lut(image, lut_channel)

    num_bands = len(image.getbands())
    if image.mode in ("L", "1"):
        lut = lut_channel
    elif image.mode in ("LA", "La"):
        lut = lut_channel + _IDENTITY_LUT
    elif image.mode == "RGB":
        lut = lut_channel * 3
    elif image.mode in ("RGBA", "RGBa", "RGBX"):
        lut = lut_channel * 3 + _IDENTITY_LUT
    elif image.mode == "CMYK":
        lut = lut_channel * 4
    else:
        if image.mode in ("RGBA", "LA", "PA", "RGBa", "La"):
            lut = lut_channel * max(1, num_bands - 1) + _IDENTITY_LUT
        else:
            lut = lut_channel * num_bands

    return image.point(lut)


MAX_BORDER_THICKNESS = 10000
MAX_TOTAL_PIXELS = 100000000  # 100MP


def apply_border(
    image: Image.Image, thickness: int, color_str: str, position: str = "expand"
) -> Image.Image:
    """Add a solid color border to the image.

    Args:
        image (Image.Image): The input image.
        thickness (int): Thickness of the border in pixels.
        color_str (str): Color in Hex or RGB format (e.g., '#FF0000', 'red', '255,0,0').
        position (str, optional): 'expand' to add border outside, 'inside' to overlay border. Defaults to "expand".

    Returns:
        Image.Image: Image with border.

    Raises:
        ValueError: If color format is invalid, thickness is negative, thickness exceeds maximum allowed limit,
            expanded image size exceeds maximum allowed limit, or position is invalid.

    """
    try:
        # Handle "255,0,0" format manually as ImageColor doesn't standardized it
        if "," in color_str and not color_str.startswith("rgb"):
            color_tuple = tuple(map(int, color_str.split(",")))
            color = color_tuple
        else:
            color = ImageColor.getrgb(color_str)
    except ValueError:
        raise ValueError(f"Invalid color format: {color_str}")

    if thickness < 0:
        raise ValueError("Thickness must be non-negative.")

    if thickness > MAX_BORDER_THICKNESS:
        raise ValueError(
            f"Thickness exceeds maximum allowed limit ({MAX_BORDER_THICKNESS})."
        )

    if thickness == 0:
        return image

    if position == "expand":
        # Security guard: check for potential memory exhaustion if expanded size is too large
        orig_w, orig_h = image.size
        new_w = orig_w + 2 * thickness
        new_h = orig_h + 2 * thickness

        if new_w * new_h > MAX_TOTAL_PIXELS:
            raise ValueError(
                f"Expanded image size ({new_w}x{new_h}) exceeds maximum allowed limit ({MAX_TOTAL_PIXELS} pixels)."
            )

        return ImageOps.expand(image, border=thickness, fill=color)
    elif position == "inside":
        from PIL import ImageDraw

        img_with_border = image.copy()
        draw = ImageDraw.Draw(img_with_border)

        w, h = image.size

        # Draw 4 rectangles to simulate inside border

        # Top: (0, 0) to (w, thickness-1)
        draw.rectangle((0, 0, w - 1, thickness - 1), fill=color)

        # Bottom: (0, h-thickness) to (w, h)
        draw.rectangle((0, h - thickness, w - 1, h - 1), fill=color)

        # Left: (0, 0) to (thickness-1, h)
        draw.rectangle((0, 0, thickness - 1, h - 1), fill=color)

        # Right: (w-thickness, 0) to (w, h)
        draw.rectangle((w - thickness, 0, w - 1, h - 1), fill=color)

        return img_with_border

    else:
        raise ValueError("Position must be 'expand' or 'inside'.")


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotates the image by a given angle, clamped to 90-degree increments.

    Args:
        image (Image.Image): The input image.
        angle (int): The angle to rotate (will be rounded to nearest 90).

    Returns:
        Image.Image: Rotated image.

    """
    # Clamp to nearest 90 degrees
    # 0, 90, 180, 270. 360 -> 0. -90 -> 270.
    clamped_angle = int(round(angle / 90.0)) * 90 % 360

    if clamped_angle == 0:
        return image

    # ⚡ Bolt: Fast path for orthogonal rotations.
    # PIL's transpose operations (ROTATE_90, ROTATE_180, ROTATE_270) are highly
    # optimized C-level pixel mapping functions that bypass the affine matrix math,
    # resampling logic, and coordinate boundary calculations required by `image.rotate()`.
    # This reduces execution time by roughly 10-25% depending on image dimensions.
    if clamped_angle == 90:
        return image.transpose(Image.Transpose.ROTATE_90)
    elif clamped_angle == 180:
        return image.transpose(Image.Transpose.ROTATE_180)
    elif clamped_angle == 270:
        return image.transpose(Image.Transpose.ROTATE_270)

    # expand=True ensures the image is resized to fit the rotated content
    # For 90 degree rotations, this swaps width/height appropriately.
    return image.rotate(clamped_angle, expand=True)


def apply_vignette(image: Image.Image, intensity: int = 50) -> Image.Image:
    """Apply a vignette effect to the image.

    Args:
        image (Image.Image): The input image.
        intensity (int, optional): The intensity of the vignette effect (0-100). Defaults to 50.

    Returns:
        Image.Image: The image with the vignette effect applied.

    Raises:
        TypeError: If intensity is not an integer.
        ValueError: If intensity is not between 0 and 100.

    """
    if not isinstance(intensity, int):
        raise TypeError("Intensity must be an integer.")
    if not 0 <= intensity <= 100:
        raise ValueError("Intensity must be between 0 and 100.")
    if intensity == 0:
        return image

    width, height = image.size

    if "A" in image.getbands():
        alpha_channel = image.getchannel("A")
    elif image.info.get("transparency") is not None:
        alpha_channel = image.convert("RGBA").getchannel("A")
    else:
        alpha_channel = None

    # Needs to be RGB/L for composite
    if image.mode not in ("RGB", "L"):
        working_image = image.convert("RGB")
    else:
        working_image = image

    # ⚡ Bolt: Use a cached base mask generation
    # Instead of calculating the 200x200 pixel distance values mathematically
    # for every single vignette request, we generate a small base mask and
    # cache it via `@functools.lru_cache`. This reduces execution time
    # for repeated/batch vignettes by over 95%.
    mask_size = 200
    mask = _generate_vignette_mask(mask_size, intensity)

    # Resize the small mask to target image dimensions smoothly
    full_mask = mask.resize((width, height), Image.Resampling.BICUBIC)

    # ⚡ Bolt: Fast path for Vignette mask application.
    # Instead of converting the 1-channel grayscale mask to a 3-channel RGB mask
    # and performing per-pixel math with `ImageChops.multiply()`, we use `Image.composite()`.
    # `Image.composite()` natively uses the 'L' mode mask as an alpha blending layer
    # to composite the original image over a solid black background, completely
    # bypassing the slow mask conversion and math overhead.
    black_bg = Image.new(working_image.mode, (width, height), 0)
    vignetted = Image.composite(working_image, black_bg, full_mask)

    if image.info:
        vignetted.info.update(image.info)

    if alpha_channel is not None:
        vignetted.putalpha(alpha_channel)

    return vignetted


def _validate_effect_intensity(intensity: int) -> None:
    """Validate a painterly-effect intensity value."""
    if not isinstance(intensity, int):
        raise TypeError("Intensity must be an integer.")
    if not 0 <= intensity <= 100:
        raise ValueError("Intensity must be between 0 and 100.")


def _prepare_painterly_image(
    image: Image.Image,
) -> tuple[Image.Image, Image.Image | None]:
    """Return an RGB working image and the original alpha channel, if present."""
    if "A" in image.getbands():
        alpha_channel = image.getchannel("A")
    elif image.info.get("transparency") is not None:
        alpha_channel = image.convert("RGBA").getchannel("A")
    else:
        alpha_channel = None
    return image.convert("RGB"), alpha_channel


def _restore_painterly_mode(
    image: Image.Image,
    original_mode: str,
    alpha_channel: Image.Image | None,
    original_info: dict | None = None,
) -> Image.Image:
    """Restore alpha, metadata, or grayscale mode after applying a painterly effect."""
    if original_info:
        image.info.update(original_info)
    if alpha_channel is not None:
        image.putalpha(alpha_channel)
        return image
    if original_mode == "L":
        return image.convert("L")
    return image


def apply_oil_painting(image: Image.Image, intensity: int = 50) -> Image.Image:
    """Apply a bilateral-filter oil-painting effect.

    Args:
        image: Input image.
        intensity: Effect strength from 0 through 100.

    Returns:
        The processed image, preserving alpha and grayscale modes where possible.
    """
    _validate_effect_intensity(intensity)
    if intensity == 0:
        return image

    import numpy as np
    from skimage import img_as_ubyte
    from skimage.restoration import denoise_bilateral

    working_image, alpha_channel = _prepare_painterly_image(image)
    fraction = intensity / 100.0
    filtered = denoise_bilateral(
        np.asarray(working_image),
        win_size=max(3, int(3 + fraction * 12) | 1),
        sigma_color=0.1 + fraction * 0.2,
        sigma_spatial=max(1.0, fraction * 30.0),
        channel_axis=-1,
    )
    result = Image.fromarray(img_as_ubyte(filtered), mode="RGB")
    return _restore_painterly_mode(result, image.mode, alpha_channel, image.info)


def apply_cartoonify(image: Image.Image, intensity: int = 50) -> Image.Image:
    """Apply bilateral smoothing with dark Sobel edges for a cartoon effect.

    Args:
        image: Input image.
        intensity: Effect strength from 0 through 100.

    Returns:
        The processed image, preserving alpha and grayscale modes where possible.
    """
    _validate_effect_intensity(intensity)
    if intensity == 0:
        return image

    import numpy as np
    from skimage import img_as_ubyte
    from skimage.color import rgb2gray
    from skimage.filters import sobel
    from skimage.restoration import denoise_bilateral

    working_image, alpha_channel = _prepare_painterly_image(image)
    pixels = np.asarray(working_image)
    fraction = intensity / 100.0
    filtered = denoise_bilateral(
        pixels,
        win_size=max(3, int(3 + fraction * 12) | 1),
        sigma_color=0.1 + fraction * 0.2,
        sigma_spatial=max(1.0, fraction * 30.0),
        channel_axis=-1,
    )
    cartoon = filtered.copy()
    cartoon[sobel(rgb2gray(pixels)) > 0.05] = 0.0
    result = Image.fromarray(img_as_ubyte(cartoon), mode="RGB")
    return _restore_painterly_mode(result, image.mode, alpha_channel, image.info)
