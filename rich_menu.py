import os
import questionary
from PIL import Image

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich import box
from rich.console import Console

console = Console()




def _get_image_metadata(path):
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


def run_image_selector(image_files, image_dir):
    """
    Renders a tabular-style selection menu using questionary.
    """
    if not image_files:
        return []

    images_data = []
    # Pre-fetch metadata to build nicely aligned strings
    for f in image_files:
        path = os.path.join(image_dir, f)
        dims, size_str, fmt = _get_image_metadata(path)
        images_data.append({"name": f, "path": path, "dims": dims, "size": size_str, "fmt": fmt})

    # Header
    console.print()
    console.print("📁 [bold bright_cyan]Select Images to Process[/]")
    console.rule(style="dim cyan")
    console.print("  [dim white]#[/] │ [bright_white]Filename[/]" + " " * 23 + "│ [bright_green]Dimensions[/]   │ [bright_yellow]Size[/]      │ [bright_magenta]Format[/]")
    console.rule(style="dim cyan")
    
    # Build choices
    choices = []
    for i, img in enumerate(images_data, 1):
        # Format string to look like table columns
        # name 30, dims 14, size 10, fmt 8
        name_col = f"{img['name']:<30}"
        dims_col = f"{img['dims']:>12}"
        size_col = f"{img['size']:>9}"
        fmt_col = f"{img['fmt']:>6}"
        
        display_str = f"{i:>2} │ {name_col} │ {dims_col} │ {size_col} │ {fmt_col}"
        choices.append(questionary.Choice(display_str, value=img['path']))

    selected = questionary.checkbox(
        "",
        choices=choices,
        qmark=" ",
        instruction="(Use arrow keys to navigate, Space to select, Enter to confirm, A to toggle all)",
    ).ask()

    return selected or []

def render_combined_menu(images_data, operations, extra_args):
    """
    Renders the combined menu mockup layout to the console.
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
    from menu import _format_operation_display
    
    pipeline_content = Text()
    
    cli_args_list = []

    if not operations:
        pipeline_content.append("  (Empty)\n", style="dim italic")
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
            if op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
                cli_args_list.append(f"--threshold {extra_args.get('threshold', 50)}")

    pipeline_content.append("\n")
    pipeline_content.append("  Equivalent CLI Command:\n", style="dim cyan")
    
    cli_str = " ".join(cli_args_list) if cli_args_list else "None"
    pipeline_content.append(f"  > python main.py \[images] {cli_str}", style="italic bright_cyan")

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
