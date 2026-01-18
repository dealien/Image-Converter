from PIL import Image, ImageOps, ImageEnhance, ImageFilter


def invert_colors(image: Image.Image) -> Image.Image:
    """
    Inverts the colors of an image.
    :param image: The input image.
    :return: The image with inverted colors.
    """
    return ImageOps.invert(image.convert('RGB'))


from skimage import feature, filters
from skimage.util import img_as_ubyte
import numpy as np


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
        from skimage import feature, filters
        from skimage.util import img_as_ubyte
        import numpy as np
    except ImportError:
        raise ImportError("scikit-image and numpy are required for edge detection.")

    if method not in ['sobel', 'canny', 'kovalevsky']:
        raise ValueError("Method must be 'sobel', 'canny', or 'kovalevsky'")

    if method == 'sobel':
        # Convert to grayscale and then to numpy array
        grayscale_img = image.convert('L')
        img_array = np.array(grayscale_img)
        # Apply Sobel filter
        edge_map = filters.sobel(img_array)
        # Convert the result back to an image
        edge_map_uint8 = np.clip(edge_map * 255, 0, 255).astype(np.uint8)
        edge_image = Image.fromarray(edge_map_uint8, mode='L')
        return edge_image

    elif method == 'canny':
        # Convert to grayscale and then to numpy array
        grayscale_img = image.convert('L')
        img_array = np.array(grayscale_img)
        # Apply Canny filter
        edge_map = feature.canny(img_array)
        # Convert the boolean array to a uint8 array (0s and 255s)
        edge_map_uint8 = (edge_map * 255).astype(np.uint8)
        # Convert the result back to an image
        edge_image = Image.fromarray(edge_map_uint8)
        return edge_image

    elif method == 'kovalevsky':
        # Convert the image to a NumPy array for efficient processing
        img_array = np.array(image.convert('RGB'), dtype=np.int16)
        height, width, _ = img_array.shape

        # Guard against images smaller than the required 6-pixel window
        if height < 6 or width < 6:
            return Image.new('L', (width, height), 0)

        # Create a new black image to draw the edges onto
        edge_map = np.zeros((height, width), dtype=np.uint8)

        # --- Horizontal Scan ---
        if width >= 6:
            for y in range(height):
                for x in range(width - 5):
                    pixels = img_array[y, x:x + 6]
                    diffs = np.abs(pixels[1:] - pixels[:-1]).sum(axis=1)
                    center_diff = diffs[2]
                    if (center_diff > threshold and
                            center_diff > diffs[0] and
                            center_diff > diffs[1] and
                            center_diff > diffs[3] and
                            center_diff > diffs[4]):
                        edge_map[y, x + 3] = 255

        # --- Vertical Scan ---
        if height >= 6:
            for x in range(width):
                for y in range(height - 5):
                    pixels = img_array[y:y + 6, x]
                    diffs = np.abs(pixels[1:] - pixels[:-1]).sum(axis=1)
                    center_diff = diffs[2]
                    if (center_diff > threshold and
                            center_diff > diffs[0] and
                            center_diff > diffs[1] and
                            center_diff > diffs[3] and
                            center_diff > diffs[4]):
                        edge_map[y + 3, x] = 255

        # Convert the NumPy array back to an image
        edge_image = Image.fromarray(edge_map, mode='L')
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

    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        rgb = Image.merge('RGB', (r, g, b))
        enhanced = ImageEnhance.Brightness(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge('RGBA', (r2, g2, b2, a))

    # 'L' is supported for brightness; convert other modes to 'RGB'
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
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

    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        rgb = Image.merge('RGB', (r, g, b))
        enhanced = ImageEnhance.Contrast(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge('RGBA', (r2, g2, b2, a))

    # 'L' is supported for contrast; convert other modes to 'RGB'
    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
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


    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        rgb = Image.merge('RGB', (r, g, b))
        enhanced = ImageEnhance.Color(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge('RGBA', (r2, g2, b2, a))

    # No-op for grayscale to preserve mode and avoid unintended conversion
    if image.mode == 'L':
        return image

    # Convert other modes to 'RGB'
    if image.mode != 'RGB':
        image = image.convert('RGB')
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


    if image.mode == 'RGBA':
        r, g, b, a = image.split()
        rgb = Image.merge('RGB', (r, g, b))
        enhanced = ImageEnhance.Sharpness(rgb).enhance(factor)
        r2, g2, b2 = enhanced.split()
        return Image.merge('RGBA', (r2, g2, b2, a))

    if image.mode not in ('RGB', 'L'):
        image = image.convert('RGB')
    
    return ImageEnhance.Sharpness(image).enhance(factor)


def apply_color_balance(image: Image.Image, red_factor: float, green_factor: float, blue_factor: float) -> Image.Image:
    """
    Adjusts the color balance of an image by scaling RGB channels.
    :param image: The input image.
    :param red_factor: Multiplier for the red channel.
    :param green_factor: Multiplier for the green channel.
    :param blue_factor: Multiplier for the blue channel.
    :return: The color-balanced image.
    """
    if str(red_factor).lower() == 'nan' or str(green_factor).lower() == 'nan' or str(blue_factor).lower() == 'nan':
         raise ValueError("Factors cannot be NaN")

    # Handle float conversion and validation
    try:
        r_f = float(red_factor)
        g_f = float(green_factor)
        b_f = float(blue_factor)
    except (ValueError, TypeError):
        raise TypeError("Color balance factors must be numbers.")
        
    if r_f < 0 or g_f < 0 or b_f < 0:
        raise ValueError("Color balance factors must be non-negative.")

    if image.mode != 'RGB' and image.mode != 'RGBA':
        image = image.convert('RGB')

    # split the image into individual bands
    bands = image.split()
    
    # Process R, G, B
    r = bands[0].point(lambda i: i * r_f)
    g = bands[1].point(lambda i: i * g_f)
    b = bands[2].point(lambda i: i * b_f)

    # Recombine (preserve alpha if present)
    if len(bands) >= 4:
         return Image.merge(image.mode, (r, g, b, bands[3]))
    return Image.merge('RGB', (r, g, b))


def rotate_hue(image: Image.Image, degrees: int) -> Image.Image:
    """
    Rotates the hue of the image.
    :param image: The input image.
    :param degrees: The angle to rotate the hue (0-360).
    :return: The image with rotated hue.
    """
    if not isinstance(degrees, (int, float)):
        raise TypeError("Degrees must be a number.")
    
    # Normalize degrees
    degrees = degrees % 360

    if degrees == 0:
        return image

    img_hsv = image.convert('HSV')
    h, s, v = img_hsv.split()
    
    # Hue is 0-255 in PIL HSV. 360 degrees = 255.
    # New Hue = (Old Hue + (degrees/360 * 255)) % 255
    shift = (degrees / 360.0) * 255.0
    
    def shift_hue(p):
        # Add shift, round to nearest int, and ensure result is in 0-255 range
        val = round(p + shift) % 256
        return val


    h = h.point(shift_hue)
    
    new_img = Image.merge('HSV', (h, s, v))
    if image.mode == 'RGBA':
        return new_img.convert('RGBA')
    return new_img.convert('RGB')


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
        
    if image.mode != 'RGB' and image.mode != 'L':
         # Posterize works on RGB or L
         return ImageOps.posterize(image.convert('RGB'), bits)

    return ImageOps.posterize(image, bits)
