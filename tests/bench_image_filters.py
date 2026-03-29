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
)
from image_converter.flip_image import flip_image
from image_converter.scale_image import scale_image


@pytest.fixture
def rgb_image():
    """Create a 512x512 RGB test image with a gradient pattern."""
    arr = np.zeros((512, 512, 3), dtype=np.uint8)
    x = np.arange(512)
    y = np.arange(512)
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


# --- Invert Colors ---


def test_bench_invert_colors_rgb(benchmark, rgb_image):
    benchmark(invert_colors, rgb_image)


def test_bench_invert_colors_rgba(benchmark, rgba_image):
    benchmark(invert_colors, rgba_image)


# --- Grayscale ---


def test_bench_grayscale(benchmark, rgb_image):
    benchmark(grayscale, rgb_image)


# --- Brightness ---


def test_bench_adjust_brightness(benchmark, rgb_image):
    benchmark(adjust_brightness, rgb_image, 50)


# --- Contrast ---


def test_bench_adjust_contrast(benchmark, rgb_image):
    benchmark(adjust_contrast, rgb_image, 50)


# --- Saturation ---


def test_bench_adjust_saturation(benchmark, rgb_image):
    benchmark(adjust_saturation, rgb_image, 50)


# --- Blur ---


def test_bench_apply_blur(benchmark, rgb_image):
    benchmark(apply_blur, rgb_image, 5)


# --- Sharpen ---


def test_bench_apply_sharpen(benchmark, rgb_image):
    benchmark(apply_sharpen, rgb_image, 50)


# --- Color Balance ---


def test_bench_apply_color_balance(benchmark, rgb_image):
    benchmark(apply_color_balance, rgb_image, 1.5, 0.8, 1.2)


# --- Hue Rotation ---


def test_bench_rotate_hue(benchmark, rgb_image):
    benchmark(rotate_hue, rgb_image, 120)


# --- Posterize ---


def test_bench_apply_posterize(benchmark, rgb_image):
    benchmark(apply_posterize, rgb_image, 4)


# --- Border ---


def test_bench_apply_border_expand(benchmark, rgb_image):
    benchmark(apply_border, rgb_image, 20, "red", "expand")


def test_bench_apply_border_inside(benchmark, rgb_image):
    benchmark(apply_border, rgb_image, 20, "#0000FF", "inside")


# --- Rotation ---


def test_bench_rotate_image_90(benchmark, rgb_image):
    benchmark(rotate_image, rgb_image, 90)


# --- Vignette ---


def test_bench_apply_vignette(benchmark, rgb_image):
    benchmark(apply_vignette, rgb_image, 75)


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
