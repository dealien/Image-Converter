"""Benchmarks for image processing functions."""

import numpy as np
import pytest
from PIL import Image

from image_converter.image_filters import (
    invert_colors,
    grayscale,
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_blur,
    apply_sharpen,
    apply_color_balance,
    rotate_hue,
    apply_posterize,
    apply_border,
    rotate_image,
    apply_vignette,
    edge_detection,
)
from image_converter.flip_image import flip_image
from image_converter.scale_image import scale_image
from image_converter.remove_background import trim


@pytest.fixture(params=[512, 2000], ids=["512x512", "2000x2000"])
def rgb_image(request):
    """Create a parameterized RGB test image with a gradient pattern."""
    size = request.param
    # Explicitly allow large images for benchmarking purposes
    Image.MAX_IMAGE_PIXELS = None

    arr = np.zeros((size, size, 3), dtype=np.uint8)
    x = np.arange(size)
    y = np.arange(size)
    xx, yy = np.meshgrid(x, y)
    arr[:, :, 0] = xx % 256
    arr[:, :, 1] = yy % 256
    arr[:, :, 2] = (xx + yy) % 256
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def rgba_image(rgb_image):
    """Create an RGBA version of the test image."""
    rgba = rgb_image.convert("RGBA")
    alpha = Image.new("L", rgba.size, 200)
    rgba.putalpha(alpha)
    return rgba


@pytest.fixture
def cmyk_image(rgb_image):
    """Create a CMYK version of the test image."""
    return rgb_image.convert("CMYK")


@pytest.fixture
def palette_image(rgb_image):
    """Create a Palette (P) version of the test image."""
    return rgb_image.convert("P")


# --- Invert Colors ---


def test_bench_invert_colors_rgb(benchmark, rgb_image):
    benchmark(invert_colors, rgb_image)


def test_bench_invert_colors_rgba(benchmark, rgba_image):
    benchmark(invert_colors, rgba_image)


# --- Grayscale ---


def test_bench_grayscale(benchmark, rgb_image):
    benchmark(grayscale, rgb_image)


# --- Brightness ---


def test_bench_adjust_brightness_rgb(benchmark, rgb_image):
    benchmark(adjust_brightness, rgb_image, 50)


def test_bench_adjust_brightness_rgba(benchmark, rgba_image):
    benchmark(adjust_brightness, rgba_image, 50)


def test_bench_adjust_brightness_cmyk(benchmark, cmyk_image):
    benchmark(adjust_brightness, cmyk_image, 50)


def test_bench_adjust_brightness_palette(benchmark, palette_image):
    benchmark(adjust_brightness, palette_image, 50)


# --- Contrast ---


def test_bench_adjust_contrast_rgb(benchmark, rgb_image):
    benchmark(adjust_contrast, rgb_image, 50)


def test_bench_adjust_contrast_rgba(benchmark, rgba_image):
    benchmark(adjust_contrast, rgba_image, 50)


# --- Saturation ---


def test_bench_adjust_saturation_rgb(benchmark, rgb_image):
    benchmark(adjust_saturation, rgb_image, 50)


def test_bench_adjust_saturation_rgba(benchmark, rgba_image):
    benchmark(adjust_saturation, rgba_image, 50)


# --- Blur ---


def test_bench_apply_blur_rgb(benchmark, rgb_image):
    benchmark(apply_blur, rgb_image, 5)


def test_bench_apply_blur_rgba(benchmark, rgba_image):
    benchmark(apply_blur, rgba_image, 5)


# --- Sharpen ---


def test_bench_apply_sharpen_rgb(benchmark, rgb_image):
    benchmark(apply_sharpen, rgb_image, 50)


def test_bench_apply_sharpen_rgba(benchmark, rgba_image):
    benchmark(apply_sharpen, rgba_image, 50)


# --- Color Balance ---


def test_bench_apply_color_balance_rgb(benchmark, rgb_image):
    benchmark(apply_color_balance, rgb_image, 1.5, 0.8, 1.2)


def test_bench_apply_color_balance_rgba(benchmark, rgba_image):
    benchmark(apply_color_balance, rgba_image, 1.5, 0.8, 1.2)


# --- Hue Rotation ---


def test_bench_rotate_hue_rgb(benchmark, rgb_image):
    benchmark(rotate_hue, rgb_image, 120)


def test_bench_rotate_hue_rgba(benchmark, rgba_image):
    benchmark(rotate_hue, rgba_image, 120)


# --- Posterize ---


def test_bench_apply_posterize_rgb(benchmark, rgb_image):
    benchmark(apply_posterize, rgb_image, 4)


def test_bench_apply_posterize_rgba(benchmark, rgba_image):
    benchmark(apply_posterize, rgba_image, 4)


# --- Border ---


def test_bench_apply_border_expand(benchmark, rgb_image):
    benchmark(apply_border, rgb_image, 20, "red", "expand")


def test_bench_apply_border_inside(benchmark, rgb_image):
    benchmark(apply_border, rgb_image, 20, "#0000FF", "inside")


# --- Rotation ---


def test_bench_rotate_image_90(benchmark, rgb_image):
    benchmark(rotate_image, rgb_image, 90)


# --- Vignette ---


def test_bench_apply_vignette_rgb(benchmark, rgb_image):
    benchmark(apply_vignette, rgb_image, 75)


def test_bench_apply_vignette_rgba(benchmark, rgba_image):
    benchmark(apply_vignette, rgba_image, 75)


# --- Edge Detection ---


def test_bench_edge_detection_sobel(benchmark, rgb_image):
    benchmark(edge_detection, rgb_image, "sobel")


def test_bench_edge_detection_canny(benchmark, rgb_image):
    benchmark(edge_detection, rgb_image, "canny")


def test_bench_edge_detection_kovalevsky(benchmark, rgb_image):
    benchmark(edge_detection, rgb_image, "kovalevsky")


# --- Flip ---


def test_bench_flip_horizontal(benchmark, rgb_image):
    benchmark(flip_image, rgb_image, "horizontal")


def test_bench_flip_vertical(benchmark, rgb_image):
    benchmark(flip_image, rgb_image, "vertical")


# --- Scale ---


def test_bench_scale_image_factor(benchmark, rgb_image):
    benchmark(scale_image, rgb_image, scale_factor=0.5)


def test_bench_scale_image_lanczos(benchmark, rgb_image):
    benchmark(scale_image, rgb_image, scale_factor=2.0, resample_filter="lanczos")


# --- Remove Background & Trim ---


def test_bench_trim_rgb(benchmark, rgb_image):
    benchmark(trim, rgb_image)


def test_bench_trim_rgba_fast_path(benchmark, rgba_image):
    # Set top-left pixel to transparent to trigger fast path
    transparent_rgba = rgba_image.copy()
    transparent_rgba.putpixel((0, 0), (0, 0, 0, 0))
    benchmark(trim, transparent_rgba)
