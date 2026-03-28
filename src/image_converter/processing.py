"""Core image processing pipeline and handlers.

Applies chained operations in sequence to a list of images and handles
the saving of the processed outputs, managing UI progress reporting.
"""

import os
import tempfile
import time
from pathlib import Path

from PIL import Image

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .flip_image import flip_image
from .image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    apply_blur,
    apply_border,
    apply_color_balance,
    apply_posterize,
    apply_sharpen,
    edge_detection,
    grayscale,
    invert_colors,
    rotate_hue,
    rotate_image,
    apply_vignette,
)
from .remove_background import remove_background
from .scale_image import scale_image


class StyledTimeElapsedColumn(TimeElapsedColumn):
    """A TimeElapsedColumn that supports custom styling.

    Attributes:
        style (str): The Rich style string to apply to the time elapsed text.

    """

    def __init__(self, style="none"):
        """Initialize the StyledTimeElapsedColumn.

        Args:
            style (str, optional): The Rich style string to apply. Defaults to "none".

        """
        super().__init__()
        self.style = style

    def render(self, task):
        """Render the time elapsed for a given task with the configured style.

        Args:
            task (Task): The progress task.

        Returns:
            Text: A Rich Text object representing the styled time elapsed.

        """
        from rich.text import Text

        text = super().render(task)
        return Text(str(text), style=self.style)


console = Console()

# Set a safe limit for image size to prevent decompression bomb attacks (100MP)
Image.MAX_IMAGE_PIXELS = 100_000_000

# --- Operation Handlers ---


def handle_flip(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'flip' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (direction).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The flipped image.

    """
    console.print(f"  [bright_yellow]›[/] [yellow]Flipping {values[0]}...[/]")
    return flip_image(image, values[0])


def handle_scale(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'scale' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (scale factor or dimensions).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The scaled image, or the original image if scaling fails.

    """
    scale_params = values
    scale_factor = None
    new_size = None

    if len(scale_params) == 1:
        # Handle single argument as scale factor (e.g., "1.5", "0.5x")
        try:
            # Remove 'x' if present, then parse float
            clean_param = scale_params[0].lower().replace("x", "")
            scale_factor = float(clean_param)
        except ValueError:
            console.print(
                f"  [bright_red]✗[/] [red]Invalid scale factor: {scale_params[0]}[/]"
            )
            return image

    elif len(scale_params) == 2:
        try:
            width = int(scale_params[0].lower().replace("px", ""))
            height = int(scale_params[1].lower().replace("px", ""))
            new_size = (width, height)
        except ValueError:
            console.print(
                f"  [bright_red]✗[/] [red]Invalid size format: {scale_params}[/]"
            )
            return image
    else:
        console.print(
            "  [bright_red]✗[/] [red]Invalid format for --scale argument. Use '1.5', '1.5x' or '400px 300px'.[/]"
        )
        return image
    if scale_factor is not None:
        console.print(
            f"  [bright_yellow]›[/] [yellow]Scaling by factor: {scale_factor}...[/]"
        )
    elif new_size is not None:
        console.print(
            f"  [bright_yellow]›[/] [yellow]Scaling to dimensions: {new_size[0]}x{new_size[1]}...[/]"
        )
    else:
        console.print("  [bright_yellow]›[/] [yellow]Scaling...[/]")
    return scale_image(
        image,
        scale_factor=scale_factor,
        new_size=new_size,
        resample_filter=args.resample,
    )


def handle_remove_background(
    image: Image.Image, image_name, values, args
) -> Image.Image:
    """Handle the 'remove_background' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation.
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with the background removed.

    """
    console.print("  [bright_yellow]›[/] [yellow]Removing background...[/]")
    return remove_background(image)


def handle_invert(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'invert' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation.
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with inverted colors.

    """
    console.print("  [bright_yellow]›[/] [yellow]Inverting colors...[/]")
    return invert_colors(image)


def handle_grayscale(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'grayscale' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation.
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The grayscale image.

    """
    console.print("  [bright_yellow]›[/] [yellow]Converting to grayscale...[/]")
    return grayscale(image)


def handle_edge_detection(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'edge_detection' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (method).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with edge detection applied.

    """
    method = values[0]
    if method == "kovalevsky":
        console.print(
            f"  [bright_yellow]›[/] [yellow]Applying {method} edge detection (threshold: {args.threshold})...[/]"
        )
        return edge_detection(image, "kovalevsky", args.threshold)
    else:
        console.print(
            f"  [bright_yellow]›[/] [yellow]Applying {method} edge detection...[/]"
        )
        return edge_detection(image, method)


def handle_brightness(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'brightness' adjustment operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (brightness level).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with adjusted brightness.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Adjusting brightness by {values[0]}...[/]"
    )
    return adjust_brightness(image, values[0])


def handle_contrast(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'contrast' adjustment operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (contrast level).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with adjusted contrast.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Adjusting contrast by {values[0]}...[/]"
    )
    return adjust_contrast(image, values[0])


def handle_saturation(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'saturation' adjustment operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (saturation level).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with adjusted saturation.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Adjusting saturation by {values[0]}...[/]"
    )
    return adjust_saturation(image, values[0])


def handle_blur(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'blur' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (blur radius).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The blurred image.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Applying Gaussian Blur (radius: {values[0]})...[/]"
    )
    return apply_blur(image, values[0])


def handle_sharpen(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'sharpen' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (sharpness intensity).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The sharpened image.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Applying Sharpen (intensity: {values[0]})...[/]"
    )
    return apply_sharpen(image, values[0])


def handle_color_balance(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'color_balance' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (R, G, B factors).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The color-balanced image.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Applying Color Balance (R:{values[0]}, G:{values[1]}, B:{values[2]})...[/]"
    )
    return apply_color_balance(image, values[0], values[1], values[2])


def handle_hue_rotation(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'hue_rotation' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (degrees).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with rotated hue.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Rotating Hue by {values[0]} degrees...[/]"
    )
    return rotate_hue(image, values[0])


def handle_posterize(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'posterize' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): The arguments for the operation (bits).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The posterized image.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Posterizing to {values[0]} bits...[/]"
    )
    return apply_posterize(image, values[0])


def handle_border(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'border' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): A list containing [thickness, color, position].
            Expects thickness to be int (or convertible string), color (str), position (str).
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with the border added, or the original image if arguments are invalid.

    """
    try:
        thickness = int(values[0])
        color = values[1]
        position = values[2]
        console.print(
            f"  [bright_yellow]›[/] [yellow]Adding border: {thickness}px, {color}, {position}[/]"
        )
        return apply_border(image, thickness, color, position)
    except (ValueError, IndexError) as e:
        console.print(
            f"  [bright_red]✗[/] [red]Invalid border arguments: {values}. Error: {e}[/]"
        )
        return image


def handle_rotate(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'rotate' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): A list containing [angle]. Expects angle to be int.
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The rotated image.

    """
    logger_str = (
        f"  [bright_yellow]›[/] [yellow]Rotating image by {values[0]} degrees...[/]"
    )
    console.print(logger_str)
    return rotate_image(image, values[0])


def handle_vignette(image: Image.Image, image_name, values, args) -> Image.Image:
    """Handle the 'vignette' operation.

    Args:
        image (Image.Image): The input image.
        image_name (str): The name of the image file.
        values (list): A list containing [intensity]. Expects intensity to be int.
        args (argparse.Namespace): The parsed CLI arguments.

    Returns:
        Image.Image: The image with the vignette effect applied.

    """
    console.print(
        f"  [bright_yellow]›[/] [yellow]Applying vignette with intensity {values[0]}...[/]"
    )
    return apply_vignette(image, values[0])


# --- Core Processing Function ---


def _process_single_image(
    original_name: str,
    image_path: str,
    prepared_operations: list,
    cli_args,
    progress: Progress,
    image_task,
    start_time: float,
    i: int,
    total_images: int,
    image_total: int,
    overall,
) -> list:
    """Process a single image, apply operations, and save the results in specified formats.

    Args:
        original_name (str): The original filename.
        image_path (str): The path to the image file.
        prepared_operations (list): The sequence of operations and their handlers.
        cli_args (argparse.Namespace): The parsed command-line arguments.
        progress (Progress): The Rich progress bar instance.
        image_task (TaskID): The progress bar task ID for this specific image.
        start_time (float): The overall processing start time.
        i (int): The index of the current image being processed (1-based).
        total_images (int): The total number of images being processed.
        image_total (int): The total steps required for this image's task.
        overall (TaskID): The progress bar task ID for the overall progress.

    Returns:
        list: A list of result tuples (filename, success, dimensions, size_bytes, error_msg).

    """
    results = []
    progress.start_task(image_task)
    progress.update(image_task, visible=True)

    # Calculate elapsed time for log marker
    elapsed_now = time.time() - start_time

    # Print a separator above each image's log
    progress.console.print()
    progress.console.print(
        f"  [bold bright_yellow]▸ [{i}/{total_images}][/]  "
        f"[bold bright_white]{original_name}[/]  "
        f"[bright_cyan][{elapsed_now:>5.1f}s ][/]"
    )
    progress.console.print(
        Rule(style="dim white"),
    )

    temp_path = None
    error_msg = None
    out_dims = "—"
    out_size_bytes = 0

    # Using original_name but .png extension for output
    # Extract specified formats and qualities from args
    target_formats = []
    target_qualities = []
    has_explicit_format = False

    if hasattr(cli_args, "format") and cli_args.format:
        target_formats = [f.lower().strip(".") for f in cli_args.format]
        has_explicit_format = True

        # Align qualities with formats if possible
        if hasattr(cli_args, "quality") and cli_args.quality:
            for j in range(len(target_formats)):
                if j < len(cli_args.quality):
                    target_qualities.append(cli_args.quality[j])
                else:
                    # Use the last specified quality or default 90
                    target_qualities.append(
                        cli_args.quality[-1] if cli_args.quality else 90
                    )
        else:
            target_qualities = [90] * len(target_formats)
    else:
        # Default to original extension
        ext = Path(original_name).suffix.lower().strip(".")
        target_formats = [ext if ext else "png"]
        target_qualities = [90]

    try:
        # Step 1: Open
        progress.update(image_task, description=f"{original_name} [dim](Opening...)[/]")
        Image.MAX_IMAGE_PIXELS = 100_000_000
        img = Image.open(image_path)
        try:
            img.load()
            output_image = img
            progress.advance(image_task)

            # Step 2: Operations
            for op_dest, op_values, handler in prepared_operations:
                if handler:
                    progress.update(
                        image_task,
                        description=f"{original_name} [dim]({op_dest.replace('_', ' ')}...)[/]",
                    )
                    output_image = handler(
                        output_image, original_name, op_values, cli_args
                    )
                progress.advance(image_task)

            if output_image is img:
                output_image = img.copy()
        finally:
            img.close()

        # Step 3: Save loop for each format
        progress.update(image_task, description=f"{original_name} [dim](Saving...)[/]")
        if not os.path.exists("Output/"):
            os.makedirs("Output/")

        # ⚡ Bolt: Cache expensive format conversions when exporting to multiple formats.
        # Repeating `.convert("RGB")` or creating a solid flattened background inside the loop
        # is computationally expensive and allocates redundant memory for each format like JPEG or BMP.
        cached_flattened_image = None
        cached_rgb_image = None

        for fmt, quality in zip(target_formats, target_qualities):
            output_filename = f"{Path(original_name).stem}.{fmt}"
            output_path = os.path.join("Output", output_filename)

            fd, temp_path = tempfile.mkstemp(
                dir="Output", prefix=".tmp.", suffix=f".{fmt}"
            )

            try:
                save_image = output_image

                # Flatten transparency if flag is set, and format might drop alpha
                if getattr(cli_args, "flatten", None) is not None:
                    if fmt in ("jpg", "jpeg", "bmp", "webp") and (
                        save_image.mode in ("RGBA", "LA", "PA")
                        or save_image.info.get("transparency", None) is not None
                    ):
                        if cached_flattened_image is None:
                            # Ensure we have an RGBA image to extract the alpha channel
                            temp_rgba = save_image.convert("RGBA")
                            background = Image.new(
                                "RGB", temp_rgba.size, cli_args.flatten
                            )
                            background.paste(temp_rgba, mask=temp_rgba.split()[3])
                            cached_flattened_image = background
                        save_image = cached_flattened_image

                # Convert to RGB if saving to JPEG/BMP to prevent OSError
                if fmt in ("jpg", "jpeg", "bmp") and save_image.mode in (
                    "RGBA",
                    "LA",
                    "P",
                ):
                    if cached_rgb_image is None:
                        cached_rgb_image = save_image.convert("RGB")
                    save_image = cached_rgb_image

                with os.fdopen(fd, "wb") as f:
                    save_kwargs = {}
                    if "exif" in save_image.info:
                        save_kwargs["exif"] = save_image.info["exif"]
                    if "dpi" in save_image.info:
                        save_kwargs["dpi"] = save_image.info["dpi"]

                    # Standardize format string for Pillow
                    pil_format = fmt.upper()
                    if pil_format == "JPG":
                        pil_format = "JPEG"
                    elif pil_format == "TIF":
                        pil_format = "TIFF"

                    # Only these formats support the 'quality' parameter in Pillow/Plugins
                    if pil_format in ("JPEG", "WEBP", "AVIF", "HEIF", "HEIC"):
                        save_kwargs["quality"] = quality

                    save_image.save(f, format=pil_format, **save_kwargs)
                    f.flush()
                    os.fsync(f.fileno())

                os.replace(temp_path, output_path)
                temp_path = None  # Clear assigned temp_path after a successful move

                # Accumulate results for each output format
                out_size_bytes = os.path.getsize(output_path)
                out_dims = f"{save_image.width} × {save_image.height}"
                results.append((output_filename, True, out_dims, out_size_bytes, None))

                # Log individual implicit/explicit conversion status
                action_str = "Exported as" if has_explicit_format else "Saved as"
                qual_str = (
                    f" [dim](Quality: [/][cyan]{quality}%[/][dim])[/]"
                    if pil_format in ("JPEG", "WEBP", "AVIF", "HEIF", "HEIC")
                    else ""
                )
                progress.console.print(
                    f"      [dim white]↳[/] [bold green]{action_str}[/] [cyan]{fmt.upper()}{qual_str}[/]"
                )
            except Exception as loop_err:
                # Close and remove specific failed format files
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.close(fd)
                    except Exception:
                        pass
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                results.append((output_filename, False, "—", 0, str(loop_err)))
                progress.console.print(
                    f"      [bright_red]✗ Failed to save {fmt.upper()}: {loop_err}[/]"
                )

        progress.advance(image_task)

        progress.update(
            image_task, description=f"{original_name} [bright_green]✓ Done[/]"
        )

    except Exception as e:
        error_msg = str(e)
        progress.update(
            image_task,
            description=f"{original_name} [bright_red]✗ Error: {e}[/]",
        )
        # Advance to total to show it finished even with error
        progress.update(image_task, completed=image_total)

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.close(fd)
            except Exception:
                pass
            try:
                os.remove(temp_path)
            except OSError:
                pass

        # If the overall failure occurred before format loop loop finished
        if error_msg:
            results.append((original_name, False, "—", 0, error_msg))
        progress.advance(overall)

    return results


def process_images_and_save(images_data, ordered_operations, cli_args):
    """Process a list of images by applying a sequence of operations and saves the results.

    Args:
        images_data (list): A list of tuples, where each tuple contains (filename, filepath).
        ordered_operations (list): A list of dictionaries detailing the operations to apply.
            Each dict should have 'dest' (operation name) and 'values' (operation arguments).
        cli_args (argparse.Namespace): The parsed command-line arguments.

    """
    operation_handlers = {
        "flip": handle_flip,
        "scale": handle_scale,
        "remove_background": handle_remove_background,
        "invert": handle_invert,
        "grayscale": handle_grayscale,
        "edge_detection": handle_edge_detection,
        "brightness": handle_brightness,
        "contrast": handle_contrast,
        "saturation": handle_saturation,
        "blur": handle_blur,
        "sharpen": handle_sharpen,
        "color_balance": handle_color_balance,
        "hue_rotation": handle_hue_rotation,
        "posterize": handle_posterize,
        "border": handle_border,
        "rotate": handle_rotate,
        "vignette": handle_vignette,
    }

    if not images_data:
        console.print("[yellow]No images to process.[/]")
        console.print(
            "[dim white]Please specify valid image files or ensure images exist in your input directory.[/]"
        )
        return

    # Processing Header
    console.print()
    console.print(
        "✨ [bold cyan]Image Converter[/] | [italic white]Interactive Image Processor[/]",
        justify="left",
    )
    console.rule(style="dim")
    console.print()
    console.print(
        f"[bold bright_white]Processing[/] [bright_cyan]{len(images_data)}[/] [bold bright_white]images...[/]"
    )
    console.print()

    total_images = len(images_data)
    results = []  # Store tuple of (filename, success, output_dims, output_size_bytes, error_msg)
    start_time = time.time()

    # Pre-compute operations and their handlers
    prepared_operations = [
        (op["dest"], op.get("values", []), operation_handlers.get(op["dest"]))
        for op in ordered_operations
    ]

    # Steps per image: Open(1) + Ops(N) + Save(1)
    image_total = 1 + len(ordered_operations) + 1

    with Progress(
        SpinnerColumn("dots", style="bright_cyan"),
        TextColumn("[bold bright_white]{task.description}"),
        BarColumn(
            bar_width=30,
            style="dim white",
            complete_style="bright_cyan",
            finished_style="bright_green",
        ),
        TaskProgressColumn(),
        StyledTimeElapsedColumn(style="bright_cyan"),
        console=console,
        transient=False,
    ) as progress:
        # Pre-add all image tasks (hidden) so they appear above Total
        image_tasks = []
        for original_name, _ in images_data:
            task_id = progress.add_task(
                original_name, total=image_total, visible=False, start=False
            )
            image_tasks.append(task_id)

        # Add Total last so it stays at the bottom
        overall = progress.add_task("Total", total=total_images)

        for i, (original_name, image_path) in enumerate(images_data, 1):
            image_task = image_tasks[i - 1]
            image_results = _process_single_image(
                original_name,
                image_path,
                prepared_operations,
                cli_args,
                progress,
                image_task,
                start_time,
                i,
                total_images,
                image_total,
                overall,
            )
            results.extend(image_results)

    elapsed = time.time() - start_time

    # ── Equivalent CLI Command ────────────────────────
    cli_args_list = []

    # 1. Add formatted file paths
    for img_name, img_path in images_data:
        # Wrap paths in quotes if they contain spaces
        safe_path = f'"{img_path}"' if " " in img_path else img_path
        cli_args_list.append(safe_path)

    # 2. Add the operations
    if ordered_operations:
        for op in ordered_operations:
            arg_name = op["dest"].replace("_", "-")
            arg_vals = " ".join(map(str, op.get("values", [])))
            cli_args_list.append(f"--{arg_name} {arg_vals}".strip())

            if (
                op["dest"] == "scale"
                and hasattr(cli_args, "resample")
                and cli_args.resample
            ):
                cli_args_list.append(f"--resample {cli_args.resample}")
            if (
                op["dest"] == "edge_detection"
                and op.get("values", [""])[0] == "kovalevsky"
            ):
                cli_args_list.append(
                    f"--threshold {getattr(cli_args, 'threshold', 50)}"
                )

    # 3. Add formatting options
    if hasattr(cli_args, "format") and cli_args.format:
        for fmt in cli_args.format:
            cli_args_list.append(f"--format {fmt}")
    if hasattr(cli_args, "quality") and cli_args.quality:
        for q in cli_args.quality:
            cli_args_list.append(f"--quality {q}")

    if hasattr(cli_args, "flatten") and cli_args.flatten:
        cli_args_list.append(f"--flatten {cli_args.flatten}")

    cli_str = " ".join(cli_args_list)

    if cli_str:
        console.print()
        console.print("💻  [bold bright_cyan]Equivalent CLI Command[/]")
        console.print(f"[bright_yellow]> image-converter {cli_str}[/]")

    # ── Results Table ──────────────────────────────────
    console.print()
    console.print(Rule("Results", style="bright_cyan"))
    console.print()

    results_table = Table(
        title="📋 Output Files",
        box=box.ROUNDED,
        title_style="bold bright_cyan",
        border_style="dim cyan",
        header_style="bold bright_white",
        padding=(0, 1),
    )
    results_table.add_column("#", style="dim white", justify="right", width=3)
    results_table.add_column("Filename", min_width=26)
    results_table.add_column("Status", justify="center", width=8)
    results_table.add_column("Dimensions", justify="center", width=14)
    results_table.add_column("File Size", justify="right", width=10)

    for i, (fname, success, dims, size_bytes, err) in enumerate(results, 1):
        if success:
            status = Text("✓ OK", style="bold bright_green")
            fname_style = "bright_white"
            dims = Text(dims, style="bright_green")

            # Format file size nicely
            if size_bytes >= 1024 * 1024:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            elif size_bytes >= 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes} B"

            size = Text(size_str, style="bright_yellow")
        else:
            status = Text("✗ FAIL", style="bold bright_red")
            fname_style = "dim red"
            dims = Text("—", style="dim red")
            size = Text("—", style="dim red")

        results_table.add_row(
            str(i),
            Text(fname, style=fname_style),
            status,
            dims,
            size,
        )

    console.print(results_table)

    # ── Summary Stats ──────────────────────────────────
    console.print()

    succeeded = sum(1 for _, success, *_ in results if success)
    failed = sum(1 for _, success, *_ in results if not success)

    summary = Text("  ")
    summary.append(f"✓ {succeeded} succeeded", style="bold bright_green")
    summary.append("  │  ", style="dim")
    summary.append(f"✗ {failed} failed", style="bold bright_red")
    summary.append("  │  ", style="dim")
    summary.append(f"{total_images} total", style="bold bright_white")
    summary.append("  │  ", style="dim")
    summary.append(f"⏱ {elapsed:.1f}s", style="bright_cyan")

    console.print(
        Panel(
            summary,
            border_style="dim white",
            box=box.ROUNDED,
            padding=(0, 1),
            expand=False,
        )
    )
    console.print()
