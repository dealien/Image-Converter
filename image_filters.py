from PIL import Image, ImageOps


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
        edge_map_uint8 = (edge_map * 255).astype(np.uint8)
        # Convert the result back to an image with explicit grayscale mode
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
        if height < 6 and width < 6:
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
