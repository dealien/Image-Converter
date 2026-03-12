import os
from pathlib import Path
import tempfile
import time

from PIL import Image

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich import box
from rich.console import Console

from flip_image import flip_image
from image_filters import (
    adjust_brightness,
    adjust_contrast,
    adjust_saturation,
    edge_detection,
    grayscale,
    invert_colors,
    apply_blur,
    apply_sharpen,
    apply_color_balance,
    rotate_hue,
    apply_posterize,
    apply_border,
    rotate_image,
)
from remove_background import remove_background
from scale_image import scale_image

console = Console()

# --- Operation Handlers ---


def handle_flip(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Flipping {values[0]}...[/]")
    return flip_image(image, values[0])


def handle_scale(image, image_name, values, args):
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
            console.print(f"  [bright_red]✗[/] [red]Invalid scale factor: {scale_params[0]}[/]")
            return image

    elif len(scale_params) == 2:
        try:
            width = int(scale_params[0].lower().replace("px", ""))
            height = int(scale_params[1].lower().replace("px", ""))
            new_size = (width, height)
        except ValueError:
            console.print(f"  [bright_red]✗[/] [red]Invalid size format: {scale_params}[/]")
            return image
    else:
        console.print(
            "  [bright_red]✗[/] [red]Invalid format for --scale argument. Use '1.5', '1.5x' or '400px 300px'.[/]"
        )
        return image
    if scale_factor is not None:
        console.print(f"  [bright_yellow]›[/] [yellow]Scaling by factor: {scale_factor}...[/]")
    elif new_size is not None:
        console.print(f"  [bright_yellow]›[/] [yellow]Scaling to dimensions: {new_size[0]}x{new_size[1]}...[/]")
    else:
        console.print("  [bright_yellow]›[/] [yellow]Scaling...[/]")
    return scale_image(
        image,
        scale_factor=scale_factor,
        new_size=new_size,
        resample_filter=args.resample,
    )


def handle_remove_background(image, image_name, values, args):
    console.print("  [bright_yellow]›[/] [yellow]Removing background...[/]")
    return remove_background(image)


def handle_invert(image, image_name, values, args):
    console.print("  [bright_yellow]›[/] [yellow]Inverting colors...[/]")
    return invert_colors(image)


def handle_grayscale(image, image_name, values, args):
    console.print("  [bright_yellow]›[/] [yellow]Converting to grayscale...[/]")
    return grayscale(image)


def handle_edge_detection(image, image_name, values, args):
    method = values[0]
    if method == "kovalevsky":
        console.print(
            f"  [bright_yellow]›[/] [yellow]Applying {method} edge detection (threshold: {args.threshold})...[/]"
        )
        return edge_detection(image, "kovalevsky", args.threshold)
    else:
        console.print(f"  [bright_yellow]›[/] [yellow]Applying {method} edge detection...[/]")
        return edge_detection(image, method)


def handle_brightness(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Adjusting brightness by {values[0]}...[/]")
    return adjust_brightness(image, values[0])


def handle_contrast(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Adjusting contrast by {values[0]}...[/]")
    return adjust_contrast(image, values[0])


def handle_saturation(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Adjusting saturation by {values[0]}...[/]")
    return adjust_saturation(image, values[0])


def handle_blur(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Applying Gaussian Blur (radius: {values[0]})...[/]")
    return apply_blur(image, values[0])


def handle_sharpen(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Applying Sharpen (intensity: {values[0]})...[/]")
    return apply_sharpen(image, values[0])


def handle_color_balance(image, image_name, values, args):
    console.print(
        f"  [bright_yellow]›[/] [yellow]Applying Color Balance (R:{values[0]}, G:{values[1]}, B:{values[2]})...[/]"
    )
    return apply_color_balance(image, values[0], values[1], values[2])


def handle_hue_rotation(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Rotating Hue by {values[0]} degrees...[/]")
    return rotate_hue(image, values[0])


def handle_posterize(image, image_name, values, args):
    console.print(f"  [bright_yellow]›[/] [yellow]Posterizing to {values[0]} bits...[/]")
    return apply_posterize(image, values[0])


def handle_border(image, image_name, values, args):
    """
    values: [thickness, color, position]
    Expects thickness to be int (or convertible string), color (str), position (str).
    """
    try:
        thickness = int(values[0])
        color = values[1]
        position = values[2]
        console.print(f"  [bright_yellow]›[/] [yellow]Adding border: {thickness}px, {color}, {position}[/]")
        return apply_border(image, thickness, color, position)
    except (ValueError, IndexError) as e:
        console.print(f"  [bright_red]✗[/] [red]Invalid border arguments: {values}. Error: {e}[/]")
        return image


def handle_rotate(image, image_name, values, args):
    """
    values: [angle]
    Expects angle to be int.
    """
    logger_str = f"  [bright_yellow]›[/] [yellow]Rotating image by {values[0]} degrees...[/]"
    console.print(logger_str)
    return rotate_image(image, values[0])


# --- Core Processing Function ---


def process_images_and_save(images_data, ordered_operations, cli_args):
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
    }

    if not images_data:
        console.print("[yellow]No images to process.[/]")
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
    results = [] # Store tuple of (filename, success, output_dims, output_size_bytes, error_msg)
    start_time = time.time()

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
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall = progress.add_task("Total", total=total_images)

        for i, (original_name, image_path) in enumerate(images_data, 1):
            console.print()
            
            header = Text()
            header.append(f"[{i}/{total_images}] ", style="bold bright_yellow")
            header.append(original_name, style="bold bright_white")

            # We don't know success yet, so set border grey initially
            # We'll update after processing.
            console.print(
                Panel(
                    header,
                    border_style="dim white",
                    box=box.HEAVY,
                    padding=(0, 1),
                    expand=True,
                )
            )

            temp_path = None
            success = False
            error_msg = None
            out_dims = "—"
            out_size_bytes = 0

            # Using original_name but .png extension for output
            output_filename = Path(original_name).stem + ".png"

            try:
                with Image.open(image_path) as img:
                    img.load()
                    output_image = img.copy()

                for operation in ordered_operations:
                    op_dest = operation["dest"]
                    op_values = operation.get("values", [])
                    handler = operation_handlers.get(op_dest)
                    if handler:
                        output_image = handler(
                            output_image, original_name, op_values, cli_args
                        )

                if not os.path.exists("Output/"):
                    os.makedirs("Output/")
                    
                output_path = os.path.join("Output", output_filename)

                fd, temp_path = tempfile.mkstemp(
                    dir="Output", prefix=".tmp.", suffix=".png"
                )
                with os.fdopen(fd, "wb") as f:
                    output_image.save(f, format="PNG")
                    f.flush()
                    os.fsync(f.fileno())

                os.replace(temp_path, output_path)
                
                # Fetch output info
                out_size_bytes = os.path.getsize(output_path)
                out_dims = f"{output_image.width} × {output_image.height}"
                
                console.print(f"  [bright_green]✓[/] [green]Saved to: {output_path}[/]")
                success = True

            except Exception as e:
                error_msg = str(e)
                console.print(f"  [bright_red]✗[/] [red]Error processing {original_name}: {e}[/]")
                
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                
                results.append((output_filename, success, out_dims, out_size_bytes, error_msg))
                progress.advance(overall)

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
            
            if op["dest"] == "scale" and hasattr(cli_args, "resample") and cli_args.resample:
                cli_args_list.append(f"--resample {cli_args.resample}")
            if op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
                cli_args_list.append(f"--threshold {getattr(cli_args, 'threshold', 50)}")
                
    cli_str = " ".join(cli_args_list)
    
    if cli_str:
        cli_panel = Panel(
            f"> python main.py {cli_str}",
            title="💻  Equivalent CLI Command",
            title_align="left",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print()
        console.print(cli_panel)

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
