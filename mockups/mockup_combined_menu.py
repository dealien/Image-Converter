"""
Combined Mockup: Best-of menu layout
- Image table from Concept A (+ dimensions column)
- Category tree from Concept B
- Pipeline panel from Concept A (+ CLI arguments row)

Usage: .venv\Scripts\python.exe mockups\mockup_combined_menu.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.rule import Rule
from rich import box

console = Console()

# ── Header ──────────────────────────────────────────

console.print()
console.print(
    "✨ [bold cyan]Image Converter[/] | [italic white]Interactive Image Processor[/]",
    justify="left",
)
console.rule(style="dim")

# ── Selected Images Table (with dimensions) ────────

console.print()
img_table = Table(
    title="📁 Selected Images",
    box=box.ROUNDED,
    title_style="bold bright_cyan",
    border_style="dim cyan",
    header_style="bold bright_white",

    padding=(0, 1),
)
img_table.add_column("#", style="dim white", justify="right", width=3)
img_table.add_column("Filename", style="bright_white", min_width=26)
img_table.add_column("Dimensions", style="bright_green", justify="center", width=14)
img_table.add_column("Size", style="bright_yellow", justify="right", width=10)
img_table.add_column("Format", style="bright_magenta", width=8)

img_table.add_row("1", "Hill Castle.png", "1920 × 1080", "2.4 MB", "PNG")
img_table.add_row("2", "Spacecraft.png", "1280 × 720", "1.8 MB", "PNG")
img_table.add_row("3", "Tree Clear Sky 1.png", "2560 × 1440", "3.1 MB", "PNG")
img_table.add_row("4", "Tree Clear Sky 2.png", "2560 × 1440", "2.9 MB", "PNG")

console.print(img_table)

# ── Operations Tree (from Concept B) ───────────────

console.print()
console.print(Rule("Available Operations", style="bright_blue"))
console.print()

tree = Tree("[bold bright_white]Operations[/]", guide_style="dim blue")

# Color Operations
color_branch = tree.add("🎨 [bold bright_yellow]Color[/]", guide_style="dim yellow")
color_ops = [
    ("[1]", "Invert Colors", "bright_red"),
    ("[2]", "Grayscale", "white"),
    ("[3]", "Brightness", "bright_yellow"),
    ("[4]", "Contrast", "bright_yellow"),
    ("[5]", "Saturation", "bright_magenta"),
    ("[6]", "Color Balance", "bright_cyan"),
    ("[7]", "Hue Rotation", "bright_green"),
    ("[8]", "Posterize", "bright_magenta"),
]
for num, name, color in color_ops:
    label = Text()
    label.append(f"{num} ", style="dim white")
    label.append(name, style=color)
    color_branch.add(label)

# Transform Operations
transform_branch = tree.add(
    "📐 [bold bright_blue]Transform[/]", guide_style="dim blue"
)
transform_ops = [
    ("[9]", "Flip", "bright_blue"),
    ("[10]", "Scale", "bright_blue"),
    ("[11]", "Rotate", "bright_blue"),
]
for num, name, color in transform_ops:
    label = Text()
    label.append(f"{num} ", style="dim white")
    label.append(name, style=color)
    transform_branch.add(label)

# Effects
effects_branch = tree.add(
    "🖼️  [bold bright_green]Effects[/]", guide_style="dim green"
)
effects_ops = [
    ("[12]", "Edge Detection", "bright_green"),
    ("[13]", "Blur", "bright_green"),
    ("[14]", "Sharpen", "bright_green"),
    ("[15]", "Remove Background", "bright_green"),
    ("[16]", "Border", "bright_green"),
]
for num, name, color in effects_ops:
    label = Text()
    label.append(f"{num} ", style="dim white")
    label.append(name, style=color)
    effects_branch.add(label)

console.print(tree)

# ── Operations Pipeline (from Concept A + CLI args) ─

console.print()

pipeline_content = Text()
pipeline_content.append("  1. ", style="dim white")
pipeline_content.append("Sharpen", style="bold bright_green")
pipeline_content.append(" (intensity: 50)", style="green")
pipeline_content.append("\n")
pipeline_content.append("  2. ", style="dim white")
pipeline_content.append("Add Border", style="bold bright_cyan")
pipeline_content.append(" (10px, red, expand)", style="cyan")
pipeline_content.append("\n")
pipeline_content.append("  3. ", style="dim white")
pipeline_content.append("Scale", style="bold bright_blue")
pipeline_content.append(" (1.5x, bilinear)", style="blue")

# CLI arguments row
pipeline_content.append("\n\n")
pipeline_content.append("  CLI: ", style="bold dim white")
pipeline_content.append(
    '--sharpen 50 --border 10 red expand --scale 1.5x --resample bilinear',
    style="italic bright_white",
)

console.print(
    Panel(
        pipeline_content,
        title="🔧 Operations Pipeline",
        title_align="left",
        border_style="bright_yellow",
        box=box.ROUNDED,
        padding=(0, 1),
    )
)

# ── Action Bar ─────────────────────────────────────

console.print()

actions = Table(box=None, show_header=False, padding=(0, 2))
actions.add_column(width=25)
actions.add_column(width=25)
actions.add_row(
    Text.assemble(("  [A] ", "bold bright_green"), ("Add Operation", "green")),
    Text.assemble(("  [R] ", "bold bright_yellow"), ("Remove Operation", "yellow")),
)
actions.add_row(
    Text.assemble(
        ("  [P] ", "bold bright_magenta"), ("Run Processing", "bold magenta")
    ),
    Text.assemble(("  [Q] ", "bold bright_red"), ("Quit", "red")),
)

console.print(
    Panel(
        actions,
        title="Actions",
        title_align="left",
        border_style="dim white",
        box=box.ROUNDED,
        padding=(0, 1),
    )
)

console.print()
console.print("  [bold bright_white]Select an option:[/] ", end="")
console.print("[dim]▎[/]")
console.print()
