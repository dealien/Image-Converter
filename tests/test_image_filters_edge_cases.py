import unittest.mock as mock

from PIL import Image

from image_converter.image_filters import (
    _get_combined_brightness_lut,
    _get_combined_contrast_lut,
)


def test_combined_luts_edge_cases():
    """Verifies that dynamically combined LUTs are generated correctly for all edge-case color modes."""
    assert len(_get_combined_contrast_lut(50, 128, "L")) == 256
    assert len(_get_combined_contrast_lut(50, 128, "1")) == 256
    assert len(_get_combined_contrast_lut(50, 128, "LA")) == 256 * 2
    assert len(_get_combined_contrast_lut(50, 128, "La")) == 256 * 2
    assert len(_get_combined_contrast_lut(50, 128, "RGB")) == 256 * 3
    assert len(_get_combined_contrast_lut(50, 128, "RGBA")) == 256 * 4
    assert len(_get_combined_contrast_lut(50, 128, "RGBa")) == 256 * 4
    assert len(_get_combined_contrast_lut(50, 128, "RGBX")) == 256 * 4
    assert len(_get_combined_contrast_lut(50, 128, "CMYK")) == 256 * 4
    assert len(_get_combined_contrast_lut(50, 128, "YCbCr")) == 256 * 3
    assert len(_get_combined_contrast_lut(50, 128, "LAB")) == 256 * 3
    assert len(_get_combined_contrast_lut(50, 128, "HSV")) == 256 * 3
    assert len(_get_combined_contrast_lut(50, 128, "PA", num_bands=2)) == 256 * 2
    assert len(_get_combined_contrast_lut(50, 128, "Pa", num_bands=2)) == 256 * 2
    assert len(_get_combined_contrast_lut(50, 128, "XYZ", num_bands=3)) == 256 * 3

    assert len(_get_combined_brightness_lut(50, "L")) == 256
    assert len(_get_combined_brightness_lut(50, "1")) == 256
    assert len(_get_combined_brightness_lut(50, "LA")) == 256 * 2
    assert len(_get_combined_brightness_lut(50, "La")) == 256 * 2
    assert len(_get_combined_brightness_lut(50, "RGB")) == 256 * 3
    assert len(_get_combined_brightness_lut(50, "RGBA")) == 256 * 4
    assert len(_get_combined_brightness_lut(50, "RGBa")) == 256 * 4
    assert len(_get_combined_brightness_lut(50, "RGBX")) == 256 * 4
    assert len(_get_combined_brightness_lut(50, "CMYK")) == 256 * 4
    assert len(_get_combined_brightness_lut(50, "YCbCr")) == 256 * 3
    assert len(_get_combined_brightness_lut(50, "LAB")) == 256 * 3
    assert len(_get_combined_brightness_lut(50, "HSV")) == 256 * 3
    assert len(_get_combined_brightness_lut(50, "PA", num_bands=2)) == 256 * 2
    assert len(_get_combined_brightness_lut(50, "Pa", num_bands=2)) == 256 * 2
    assert len(_get_combined_brightness_lut(50, "XYZ", num_bands=3)) == 256 * 3


def test_16bit_LUTs_and_mean_fallback():
    """Verifies fallback and generated lengths for 16-bit LUTs and exception paths."""
    from image_converter.image_filters import (
        _apply_palette_lut,
        _get_brightness_lut_16,
        _get_contrast_lut_16,
        _get_image_mean_luminance,
        apply_border,
        edge_detection,
    )

    lut_b16 = _get_brightness_lut_16(50)
    assert len(lut_b16) == 65536

    lut_c16 = _get_contrast_lut_16(50, 32768)
    assert len(lut_c16) == 65536

    img_rgb = Image.new("RGB", (10, 10))
    with mock.patch.object(
        img_rgb, "convert", side_effect=ValueError("convert failed")
    ):
        mean = _get_image_mean_luminance(img_rgb)
        assert mean == 0  # Default black image

    img_p = Image.new("P", (10, 10))
    img_p.palette = None
    res_p = _apply_palette_lut(img_p, list(range(256)))
    assert res_p.mode == "RGB"

    img_pa = Image.new("PA", (10, 10))
    img_pa.palette = None
    res_pa = _apply_palette_lut(img_pa, list(range(256)))
    assert res_pa.mode == "RGBA"

    img_w = Image.new("RGB", (100, 100), "white")
    res_w = apply_border(img_w, thickness=10, color_str="red", position="inside")
    assert res_w.size == (100, 100)

    img_s = Image.new("RGB", (5, 5))
    res_s = edge_detection(img_s, method="kovalevsky")
    assert res_s.size == (5, 5)
