import pytest
from PIL import Image
from image_converter.image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_blur,
    apply_sharpen,
    rotate_hue,
    apply_posterize,
)


def test_adjust_brightness_mode_conversion():
    """Verifies adjust_brightness handles non-RGB/L mode image conversion properly."""
    img = Image.new("HSV", (10, 10))
    res = adjust_brightness(img, 50)
    assert res.mode == "RGB"


def test_adjust_contrast_mode_conversion():
    """Verifies adjust_contrast handles non-RGB/L mode image conversion properly."""
    img = Image.new("HSV", (10, 10))
    res = adjust_contrast(img, 50)
    assert res.mode == "RGB"


def test_adjust_saturation_mode_conversion():
    """Verifies adjust_saturation handles non-RGB/L mode image conversion properly."""
    img = Image.new("HSV", (10, 10))
    res = adjust_saturation(img, 50)
    assert res.mode == "RGB"


def test_adjust_saturation_grayscale_noop():
    """Verifies adjust_saturation is a no-op for grayscale 'L' mode images."""
    img = Image.new("L", (10, 10), 128)
    res = adjust_saturation(img, 50)
    assert res.mode == "L"


def test_apply_blur_invalid_radius():
    """Verifies apply_blur raises ValueError for negative radius."""
    img = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError, match="Radius must be non-negative."):
        apply_blur(img, -1.0)


def test_apply_sharpen_invalid_sharpness():
    """Verifies apply_sharpen raises ValueError for out of bounds sharpness."""
    img = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError, match="Sharpness must be between 0 and 100."):
        apply_sharpen(img, 150)


def test_apply_sharpen_mode_conversion():
    """Verifies apply_sharpen handles non-RGB/L mode image conversion properly."""
    img = Image.new("HSV", (10, 10))
    res = apply_sharpen(img, 50)
    assert res.mode == "RGB"


def test_rotate_hue_invalid_degrees():
    """Verifies rotate_hue raises TypeError for non-numeric degrees."""
    img = Image.new("RGB", (10, 10))
    with pytest.raises(TypeError, match="Degrees must be a number."):
        rotate_hue(img, "90")


def test_rotate_hue_zero_degrees():
    """Verifies rotate_hue does nothing when degrees is 0."""
    img = Image.new("RGB", (10, 10), color="red")
    res = rotate_hue(img, 0)
    assert res == img


def test_apply_posterize_invalid_bits_type():
    """Verifies apply_posterize raises TypeError for non-integer bits."""
    img = Image.new("RGB", (10, 10))
    with pytest.raises(TypeError, match="Bits must be an integer."):
        apply_posterize(img, "4")


def test_apply_posterize_invalid_bits_value():
    """Verifies apply_posterize raises ValueError for bits out of bounds."""
    img = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError, match="Bits must be between 1 and 8."):
        apply_posterize(img, 10)


def test_rotate_hue_rgba():
    """Verifies rotate_hue handles RGBA image properly without losing alpha."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    res = rotate_hue(img, 90)
    assert res.mode == "RGBA"
    assert res.getpixel((0, 0))[3] == 128


def test_apply_posterize_rgba():
    """Verifies apply_posterize handles RGBA image properly without losing alpha."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    res = apply_posterize(img, 4)
    assert res.mode == "RGBA"
    assert res.getpixel((0, 0))[3] == 128
