"""Interactive terminal UI formatting and layout components.

Utilizes the `rich` and `questionary` libraries to render formatted tables,
selection menus, and pipeline summaries for the interactive CLI.
"""

import os
import questionary
import concurrent.futures
from typing import Any
from PIL import Image

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich import box
from rich.console import Console

console = Console()

# Set a safe limit for image size to prevent decompression bomb attacks (100MP)
Image.MAX_IMAGE_PIXELS = 100_000_000


def _get_image_metadata(path: str) -> tuple[str, str, str]:
    """Retrieves basic metadata for an image file.

    Args:
        path (str): The file path to the image.

    Returns:
        tuple: A tuple containing the formatted dimensions string (e.g., '1920 x 1080'),
            the formatted file size string (e.g., '1.5 MB'), and the image format (e.g., 'JPEG').

    """
    try:
        size_bytes = os.path.getsize(path)
        if size_bytes >= 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"
    except Exception:
        size_str = "—"

    try:
        with Image.open(path) as img:
            dims = f"{img.width} × {img.height}"
            fmt = img.format or "UNKNOWN"
    except Exception:
        dims = "—"
        fmt = "UNKNOWN"

    return dims, size_str, fmt


def run_image_selector(image_files: list[str], image_dir: str) -> list[str]:
    """Renders a tabular-style selection menu using questionary.

    Args:
        image_files (list): A list of image filenames.
        image_dir (str): The directory containing the image files.

    Returns:
        list: A list of selected image file paths.

    """
    if not image_files:
        return []

    def _fetch_image_data(f):
        path = os.path.join(image_dir, f)
        dims, size_str, fmt = _get_image_metadata(path)
        return {"name": f, "path": path, "dims": dims, "size": size_str, "fmt": fmt}

    # Pre-fetch metadata in parallel to build nicely aligned strings
    with concurrent.futures.ThreadPoolExecutor() as executor:
        images_data = list(executor.map(_fetch_image_data, image_files))

    # Header
    console.print()
    console.print("📁 [bold bright_cyan]Select Images to Process[/]")
    console.rule(style="dim cyan")
    console.print(
        "  [dim white]#[/] │ [bright_white]Filename[/]"
        + " " * 23
        + "│ [bright_green]Dimensions[/]   │ [bright_yellow]Size[/]      │ [bright_magenta]Format[/]"
    )
    console.rule(style="dim cyan")

    # Build choices
    choices = []
    for i, img in enumerate(images_data, 1):
        # Format string to look like table columns
        # name 30, dims 14, size 10, fmt 8

        display_name = img["name"]
        if len(display_name) > 30:
            display_name = display_name[:29] + "…"

        name_col = f"{display_name:<30}"
        dims_col = f"{img['dims']:>12}"
        size_col = f"{img['size']:>9}"
        fmt_col = f"{img['fmt']:>6}"

        display_str = f"{i:>2} │ {name_col} │ {dims_col} │ {size_col} │ {fmt_col}"
        choices.append(questionary.Choice(display_str, value=img["path"]))

    selected = questionary.checkbox(
        "",
        choices=choices,
        qmark=" ",
        instruction="(Use arrow keys to navigate, Space to select, Enter to confirm, A to toggle all)",
    ).ask()

    return selected or []


def render_combined_menu(
    images_data: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    extra_args: dict[str, Any],
) -> None:
    """Renders the combined menu mockup layout to the console.

    Displays a summary of selected images and the current sequence of operations
    (the pipeline), along with the equivalent CLI command.

    Args:
        images_data (list): A list of dictionaries containing image metadata.
        operations (list): A list of dictionaries detailing the ordered operations.
        extra_args (dict): A dictionary of extra global arguments (like resample filter).

    """
    console.clear()
    console.print()
    console.print(
        "✨ [bold cyan]Image Converter[/] | [italic white]Interactive Image Processor[/]",
        justify="left",
    )
    console.rule(style="dim")
    console.print()

    # ── Image Table ──
    img_table = Table(
        title="🖼️  Selected Images",
        box=box.MINIMAL_HEAVY_HEAD,
        title_style="bold bright_white",
        border_style="dim white",
        header_style="bold bright_cyan",
        title_justify="left",
        padding=(0, 1),
    )
    img_table.add_column("#", style="dim white", width=3, justify="right")
    img_table.add_column("Filename", style="bright_white", min_width=25)
    img_table.add_column("Dimensions", style="bright_green", justify="center")
    img_table.add_column("Size", style="bright_yellow", justify="right")
    img_table.add_column("Format", style="bright_magenta")

    for i, img in enumerate(images_data):
        img_table.add_row(
            str(i + 1),
            img["name"],
            img["dims"],
            img["size"],
            img["fmt"],
        )

    # ── Pipeline & CLI Panel ──
    from .menu import _format_operation_display

    pipeline_content = Text()

    cli_args_list = []

    if not operations:
        pipeline_content.append(
            "  (Empty - Select operations below to build your pipeline)\n",
            style="dim italic",
        )
    else:
        for i, op in enumerate(operations):
            # Formats beautifully with numbers
            pretty_op = _format_operation_display(i, op, extra_args)
            pipeline_content.append(f"  {pretty_op}\n", style="bright_white")

            # Build raw CLI equivalent separately
            arg_name = op["dest"].replace("_", "-")
            arg_vals = " ".join(map(str, op.get("values", [])))
            cli_args_list.append(f"--{arg_name} {arg_vals}".strip())

            if op["dest"] == "scale" and "resample" in extra_args:
                cli_args_list.append(f"--resample {extra_args['resample']}")
            if (
                op["dest"] == "edge_detection"
                and op.get("values", [""])[0] == "kovalevsky"
            ):
                cli_args_list.append(f"--threshold {extra_args.get('threshold', 50)}")

    pipeline_content.append("\n")
    pipeline_content.append("  Equivalent CLI Command:\n", style="dim cyan")

    cli_str = " ".join(cli_args_list) if cli_args_list else "None"
    pipeline_content.append(
        rf"  > image-converter \[images] {cli_str}", style="italic bright_cyan"
    )

    pipeline_panel = Panel(
        pipeline_content,
        title="⚙️  Pipeline",
        title_align="left",
        border_style="bright_blue",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    # ── Combined Layout ──
    # Top row: Image Table
    # Bottom row: Pipeline Panel

    console.print(img_table)
    console.print()
    console.print(pipeline_panel)
    console.print()
