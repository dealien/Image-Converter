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


def test_combined_brightness_lut_unsupported_mode():
    """Verifies _get_combined_brightness_lut raises ValueError for unsupported mode."""
    from image_converter.image_filters import _get_combined_brightness_lut

    with pytest.raises(ValueError, match="Unsupported mode: CMYK"):
        _get_combined_brightness_lut(50, "CMYK")


def test_combined_brightness_lut_rgb_la():
    """Verifies _get_combined_brightness_lut supports RGB and LA."""
    from image_converter.image_filters import _get_combined_brightness_lut

    _get_combined_brightness_lut(50, "RGB")
    _get_combined_brightness_lut(50, "LA")


def test_combined_brightness_lut_l():
    """Verifies _get_combined_brightness_lut supports L."""
    from image_converter.image_filters import _get_combined_brightness_lut

    _get_combined_brightness_lut(50, "L")


def test_rotate_image_non_orthogonal():
    """Verifies rotate_image clamps non-orthogonal inputs to the nearest 90 degrees."""
    from image_converter.image_filters import rotate_image

    img = Image.new("RGB", (10, 20))
    res = rotate_image(img, 45)
    # 45 is closer to 90 than 0 since round(45 / 90.0) -> round(0.5) is typically 0 in Python 3 for ties to even, wait
    # round(0.5) is 0, wait! Let's check int(round(45 / 90.0)) -> 0!
    # So 45 degrees rounds to 0. It should return the original image!
    # Let's assert output size is 10x20
    assert res.size == (10, 20)

    # What about 46 degrees? 46 / 90 = 0.511 -> round(0.511) -> 1 -> 90 degrees
    res2 = rotate_image(img, 46)
    assert res2.size == (20, 10)
