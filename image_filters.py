from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageColor


def invert_colors(image: Image.Image) -> Image.Image:
    """
    Inverts the colors of an image.
    :param image: The input image.
    :return: The image with inverted colors.
    """
    return ImageOps.invert(image.convert("RGB"))


def grayscale(image: Image.Image) -> Image.Image:
    """
    Converts an image to grayscale.
    :param image: The input image.
    :return: The grayscale image.
    """
    return ImageOps.grayscale(image)


def edge_detection(image: Image.Image, method: str, threshold: int = 50) -> Image.Image:
    """
    Applies edge detection to an image using one of three methods.
    :param image: The input image.
    :param method: The edge detection method ('sobel', 'canny', 'kovalevsky').
    :param threshold: The sensitivity threshold for the Kovalevsky method.
    :return: The image with edges detected.
    """

    try:
        # Not every system has scikit-image installed, and it's not a required
        # dependency for the main functionality
        from skimage import feature, filters

        import numpy as np
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
        if width >= 6:
            # Chunk rows to cap peak memory while maintaining vectorized speed
            chunk_size = 512
            for i in range(0, height, chunk_size):
                chunk = img_array[i : i + chunk_size]
                # Calculate absolute differences between adjacent pixels in the same row
                # np.diff computes img[:, 1:] - img[:, :-1] along the specified axis
                h_diffs = np.abs(np.diff(chunk, axis=1)).sum(axis=2, dtype=np.int32)

                # Create slices for the 5-pixel comparison window
                d0 = h_diffs[:, :-4]
                d1 = h_diffs[:, 1:-3]
                d2 = h_diffs[:, 2:-2]  # The center difference
                d3 = h_diffs[:, 3:-1]
                d4 = h_diffs[:, 4:]

                # Apply Kovalevsky condition: center is a local maximum and above threshold
                h_condition = (
                    (d2 > threshold) & (d2 > d0) & (d2 > d1) & (d2 > d3) & (d2 > d4)
                )
                # Mark detected edges in the edge map
                edge_map[i : i + chunk_size, 3:-2][h_condition] = 255

        # --- Vertical Scan ---
        if height >= 6:
            # Chunk columns to cap peak memory
            chunk_size = 512
            for i in range(0, width, chunk_size):
                chunk = img_array[:, i : i + chunk_size]
                # Calculate absolute differences between adjacent pixels in the same column
                v_diffs = np.abs(np.diff(chunk, axis=0)).sum(axis=2, dtype=np.int32)

                # Create slices for the 5-pixel comparison window
                d0 = v_diffs[:-4, :]
                d1 = v_diffs[1:-3, :]
                d2 = v_diffs[2:-2, :]  # The center difference
                d3 = v_diffs[3:-1, :]
                d4 = v_diffs[4:, :]

                # Apply Kovalevsky condition
                v_condition = (
                    (d2 > threshold) & (d2 > d0) & (d2 > d1) & (d2 > d3) & (d2 > d4)
                )
                # Mark detected edges in the edge map
                edge_map[3:-2, i : i + chunk_size][v_condition] = 255

        # Convert the NumPy array back to an image
        edge_image = Image.fromarray(edge_map, mode="L")
        return edge_image


def adjust_brightness(image: Image.Image, brightness: int) -> Image.Image:
    """
    Adjusts the brightness of an image.
    :param image: The input image.
    :param brightness: An integer from -100 to 100.
    :return: The image with adjusted brightness.
    """
    if not isinstance(brightness, int):
        raise TypeError("Brightness must be an integer.")
    if not -100 <= brightness <= 100:
        raise ValueError("Brightness must be between -100 and 100.")
    if brightness == 0:
        return image
    factor = 1.0 + (brightness / 100.0)

    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        enhanced = ImageEnhance.Brightness(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge("RGBA", (r2, g2, b2, a))

    # 'L' is supported for brightness; convert other modes to 'RGB'
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    return ImageEnhance.Brightness(image).enhance(factor)


def adjust_contrast(image: Image.Image, contrast: int) -> Image.Image:
    """
    Adjusts the contrast of an image.
    :param image: The input image.
    :param contrast: An integer from -100 to 100.
    :return: The image with adjusted contrast.
    """
    if not isinstance(contrast, int):
        raise TypeError("Contrast must be an integer.")
    if not -100 <= contrast <= 100:
        raise ValueError("Contrast must be between -100 and 100.")
    if contrast == 0:
        return image
    factor = 1.0 + (contrast / 100.0)

    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        enhanced = ImageEnhance.Contrast(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge("RGBA", (r2, g2, b2, a))

    # 'L' is supported for contrast; convert other modes to 'RGB'
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    return ImageEnhance.Contrast(image).enhance(factor)


def adjust_saturation(image: Image.Image, saturation: int) -> Image.Image:
    """
    Adjusts the saturation of an image.
    :param image: The input image.
    :param saturation: An integer from -100 to 100.
    :return: The image with adjusted saturation.
    """
    if not isinstance(saturation, int):
        raise TypeError("Saturation must be an integer.")
    if not -100 <= saturation <= 100:
        raise ValueError("Saturation must be between -100 and 100.")
    if saturation == 0:
        return image
    factor = 1.0 + (saturation / 100.0)

    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        enhanced = ImageEnhance.Color(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge("RGBA", (r2, g2, b2, a))

    # No-op for grayscale to preserve mode and avoid unintended conversion
    if image.mode == "L":
        return image

    # Convert other modes to 'RGB'
    if image.mode != "RGB":
        image = image.convert("RGB")
    return ImageEnhance.Color(image).enhance(factor)


def apply_blur(image: Image.Image, radius: int) -> Image.Image:
    """
    Applies Gaussian Blur to the image.
    :param image: The input image.
    :param radius: The radius of the blur.
    :return: The blurred image.
    """
    if not isinstance(radius, (int, float)):
        raise TypeError("Radius must be a number.")
    if radius < 0:
        raise ValueError("Radius must be non-negative.")
    if radius == 0:
        return image
    return image.filter(ImageFilter.GaussianBlur(radius))


def apply_sharpen(image: Image.Image, sharpness: int) -> Image.Image:
    """
    Applies sharpening to the image.
    :param image: The input image.
    :param sharpness: An integer from 0 to 100 representing intensity.
    :return: The sharpened image.
    """
    if not isinstance(sharpness, int):
        raise TypeError("Sharpness must be an integer.")
    if not 0 <= sharpness <= 100:
        raise ValueError("Sharpness must be between 0 and 100.")
    if sharpness == 0:
        return image

    # Map 0-100 to a factor (e.g., 1.0 to 2.0)
    factor = 1.0 + (sharpness / 100.0)

    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb = Image.merge("RGB", (r, g, b))
        enhanced = ImageEnhance.Sharpness(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge("RGBA", (r2, g2, b2, a))

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    return ImageEnhance.Sharpness(image).enhance(factor)


def apply_color_balance(
    image: Image.Image, red_factor: float, green_factor: float, blue_factor: float
) -> Image.Image:
    # pylint: disable=too-many-branches, complex-logic
    """
    Adjusts the color balance of an image by scaling RGB channels.
    :param image: The input image.
    :param red_factor: Multiplier for the red channel.
    :param green_factor: Multiplier for the green channel.
    :param blue_factor: Multiplier for the blue channel.
    :return: The color-balanced image.
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

    # Convert to RGB if not already
    if image.mode != "RGB" and image.mode != "RGBA":
        image = image.convert("RGB")

    def _scale_lut(factor: float):
        """
        Creates a Look-Up Table (LUT) for scaling a channel, clamping to [0, 255].
        :param factor: The scaling factor.
        :return: A list of 256 mapped values.
        """
        return [max(0, min(255, int(round(i * factor)))) for i in range(256)]

    # Precompute the LUT for R, G, and B channels
    lut = _scale_lut(r_f) + _scale_lut(g_f) + _scale_lut(b_f)

    # For images with more than 3 bands (e.g., RGBA), preserve the extra bands
    # by adding an identity mapping to the LUT
    num_bands = len(image.getbands())
    if num_bands > 3:
        for _ in range(3, num_bands):
            lut += list(range(256))

    # Apply the LUT directly to the image (faster than split, point with lambda, merge)
    return image.point(lut)


def rotate_hue(image: Image.Image, degrees: int) -> Image.Image:
    """
    Rotates the hue of the image.
    :param image: The input image.
    :param degrees: The angle to rotate the hue (0-360).
    :return: The image with rotated hue.
    """
    if not isinstance(degrees, (int, float)):
        raise TypeError("Degrees must be a number.")

    degrees = degrees % 360
    if degrees == 0:
        return image

    # Store alpha if present (supports RGBA/LA/etc.)
    alpha_channel = image.getchannel("A") if "A" in image.getbands() else None

    # Ensure hue ops always run on RGB data
    rgb_base = image.convert("RGB")

    img_hsv = rgb_base.convert("HSV")
    h, s, v = img_hsv.split()

    # Hue is 0-255 in PIL HSV. Full circle is 256 steps.
    shift = int((degrees / 360.0) * 256) % 256

    h = h.point(lambda p: (p + shift) % 256)

    new_img = Image.merge("HSV", (h, s, v))
    new_rgb = new_img.convert("RGB")

    if alpha_channel is not None:
        new_rgb.putalpha(alpha_channel)
        return new_rgb

    return new_rgb


def apply_posterize(image: Image.Image, bits: int) -> Image.Image:
    """
    Reduces the number of bits for each color channel.
    :param image: The input image.
    :param bits: The number of bits to keep (1-8).
    :return: The posterized image.
    """
    if not isinstance(bits, int):
        raise TypeError("Bits must be an integer.")

    if not 1 <= bits <= 8:
        raise ValueError("Bits must be between 1 and 8.")

    # Store alpha if present (supports RGBA/LA/etc.)
    alpha_channel = image.getchannel("A") if "A" in image.getbands() else None

    # Posterize operates on 'RGB' or 'L'
    if image.mode == "L":
        base = image
    else:
        base = image.convert("RGB")

    posterized = ImageOps.posterize(base, bits)

    if alpha_channel is not None:
        posterized.putalpha(alpha_channel)
        return posterized

    return posterized


MAX_BORDER_THICKNESS = 10000
MAX_TOTAL_PIXELS = 100000000  # 100MP


def apply_border(
    image: Image.Image, thickness: int, color_str: str, position: str = "expand"
) -> Image.Image:
    """
    Adds a solid color border to the image.
    :param image: The input image.
    :param thickness: Thickness of the border in pixels.
    :param color_str: Color in Hex or RGB format (e.g., '#FF0000', 'red', '255,0,0').
    :param position: 'expand' to add border outside, 'inside' to overlay border.
    :return: Image with border.
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
    """
    Rotates the image by a given angle, clamped to 90-degree increments.
    :param image: The input image.
    :param angle: The angle to rotate (will be rounded to nearest 90).
    :return: Rotated image.
    """
    # Clamp to nearest 90 degrees
    # 0, 90, 180, 270. 360 -> 0. -90 -> 270.
    clamped_angle = int(round(angle / 90.0)) * 90 % 360

    if clamped_angle == 0:
        return image

    # expand=True ensures the image is resized to fit the rotated content
    # For 90 degree rotations, this swaps width/height appropriately.
    return image.rotate(clamped_angle, expand=True)
