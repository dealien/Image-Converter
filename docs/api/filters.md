# Image Filters API Reference

This section provides documentation for all image manipulation and filtering actions.

## Image Mode Support Matrix

The table below outlines native image mode support across LUT-based image processing functions:

| Operation / Function | Supported Image Modes | Details & Band Mapping |
| :--- | :--- | :--- |
| `adjust_brightness` | `1`, `L`, `P`, `PA`, `LA`, `La`, `RGB`, `RGBA`, `RGBX`, `RGBa`, `CMYK`, `YCbCr`, `LAB`, `HSV`, `I;16` | Brightness scaling via flat LUT / point transforms. Preserves alpha & chrominance bands. |
| `adjust_contrast` | `1`, `L`, `P`, `PA`, `LA`, `La`, `RGB`, `RGBA`, `RGBX`, `RGBa`, `CMYK`, `YCbCr`, `LAB`, `HSV`, `I;16` | Contrast expansion anchored to luminance mean across channels. |
| `apply_posterize` | `1`, `L`, `P`, `PA`, `LA`, `La`, `RGB`, `RGBA`, `RGBX`, `RGBa`, `CMYK`, `YCbCr`, `LAB`, `HSV` | Bit-depth reduction across color/luminance bands. |
| `apply_color_balance` | `L`, `P`, `PA`, `LA`, `La`, `RGB`, `RGBA`, `RGBX`, `RGBa`, `CMYK`, `YCbCr`, `LAB`, `HSV` | Per-band channel scaling or palette entry transformation. |
| `invert_colors` | `1`, `L`, `P`, `PA`, `LA`, `La`, `RGB`, `RGBA`, `RGBX`, `RGBa`, `CMYK`, `YCbCr`, `LAB`, `HSV` | Inverts color values while preserving alpha & palette structure. |
| `rotate_hue` | `RGB`, `RGBA`, `RGBa`, `RGBX`, `LA`, `La`, `P`, `PA`, `HSV`, `YCbCr`, `LAB` | HSV hue wheel shifting ($0-360^\circ$). |

## image_filters

::: image_converter.image_filters

## flip_image

::: image_converter.flip_image

## scale_image

::: image_converter.scale_image

## remove_background

::: image_converter.remove_background
