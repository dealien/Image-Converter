# Command Line Interface (CLI)

The CLI provides a powerful way to process images programmatically or in batches.

## Basic Usage

```bash
image-converter [file_path] [options]
```

- `[file_path]`: Path to the input image file. You can use wildcards (`*`) to process multiple files. If no file is specified, the script processes all images in the `Base Images/` directory.

## Core Operations

- `-bg`, `--remove-background`: Remove the background from the image.
- `-s`, `--scale [value]`: Scale the image.
  - By factor: `1.5x`
  - By dimensions: `400px 300px`
- `--resample [filter]`: Resampling filter for scaling. Choices: `nearest`, `bilinear`, `bicubic`, `lanczos` (default: `bilinear`).
- `-i`, `--invert`: Invert the colors of the image.
- `-g`, `--grayscale`: Convert the image to grayscale.
- `--flip [direction]`: Flip the image. Choices: `horizontal`, `vertical`, `both`.
- `--rotate [degrees]`: Rotate image by 90-degree increments (0, 90, 180, 270).
- `--rotate [degrees]`: Rotate image by 90-degree increments (0, 90, 180, 270).
- `--border [thickness] [color] [position]`: Add a border (e.g., `10 black expand`).

## Output Options

- `--format [type]`: Output format (e.g. `png`, `jpg`, `webp`, `heic`, `avif`). Can be used multiple times.
- `--quality [value]`: Output quality (1-100) per format. Evaluated in order of `--format` arguments.

## Filters & Adjustments

- `--brightness [value]`: Adjust brightness (-100 to 100).
- `--contrast [value]`: Adjust contrast (-100 to 100).
- `--saturation [value]`: Adjust saturation (-100 to 100).
- `--blur [radius]`: Apply Gaussian Blur with specified radius.
- `--sharpen [intensity]`: Resulting image sharpness (0-100).
- `--color-balance [R] [G] [B]`: Adjust R, G, B channels (e.g., `1.2 0.8 1.0`).
- `--hue-rotation [degrees]`: Rotate hue by specified degrees (0-360).
- `--posterize [bits]`: Reduce color depth to N bits (1-8).
- `--vignette [intensity]`: Apply vignette effect with specified intensity (0-100).
- `--edge-detection [method]`: Apply edge detection (`sobel`, `canny`, `kovalevsky`).
- `--threshold [value]`: Threshold for the Kovalevsky edge detection method (0-255).

## Examples

### Remove the background of a single image

```bash
image-converter "path/to/your/image.jpg" --remove-background
```

### Scale all PNG images in a directory to 50%

```bash
image-converter "path/to/your/images/*.png" --scale 0.5x
```

### Convert all images to WebP and JPEG at half quality

```bash
image-converter "path/to/your/images/*" --format webp --quality 50 --format jpg --quality 50
```

### Chaining Multiple Operations

The manipulations are applied sequentially in the order you provide them.

For example, to take an image, invert its colors, flip it vertically, convert it to grayscale, remove the background, and then invert the colors *again*, you can run:

```bash
image-converter "image.jpg" --invert --flip vertical --grayscale --remove-background --invert
```

### Process all images in the `Base Images` directory

This will first remove the background and then scale the images to fit within 800x600 pixels:

```bash
image-converter * --remove-background --scale 800px 600px
```
