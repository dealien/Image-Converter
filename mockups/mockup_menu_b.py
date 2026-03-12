"""
Mockup B: Category-tree Rich Menu Layout
Run this script to preview how the menu could look with Rich Tree grouping.

Usage: .venv\Scripts\python.exe mockups\mockup_menu_b.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.rule import Rule
from rich import box

console = Console()

# ── Header ──────────────────────────────────────────

console.print()
console.print(
    Panel(
        "[bold bright_white]Image Converter[/]",
        border_style="blue",
        box=box.DOUBLE_EDGE,
        padding=(0, 3),
        expand=False,
        subtitle="[dim italic]v1.0[/]",
        subtitle_align="right",
    )
)

# ── Selected Images (compact) ──────────────────────

console.print()
console.print("[bold bright_cyan]Selected:[/] ", end="")
files = [
    "Hill Castle.png",
    "Spacecraft.png",
    "Tree Clear Sky 1.png",
    "Tree Clear Sky 2.png",
]
for i, f in enumerate(files):
    console.print(f"[bright_white]{f}[/]", end="")
    if i < len(files) - 1:
        console.print("[dim] · [/]", end="")
console.print()

# ── Operations Tree ────────────────────────────────

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
transform_branch = tree.add("📐 [bold bright_blue]Transform[/]", guide_style="dim blue")
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
effects_branch = tree.add("🖼️  [bold bright_green]Effects[/]", guide_style="dim green")
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

# ── Current Pipeline (tag style) ──────────────────

console.print()
console.print(Rule("Pipeline", style="bright_yellow"))
console.print()

tags = [
    ("Sharpen", "50", "bright_green", "green"),
    ("Border", "10px, red", "bright_cyan", "cyan"),
    ("Grayscale", "", "white", "dim white"),
]

pipeline_text = Text("  ")
for name, params, name_style, param_style in tags:
    pipeline_text.append("┃", style="dim")
    pipeline_text.append(f" {name}", style=f"bold {name_style}")
    if params:
        pipeline_text.append(f"({params})", style=param_style)
    pipeline_text.append(" ", style="")
    pipeline_text.append("┃", style="dim")
    pipeline_text.append("  ", style="")

console.print(pipeline_text)

# ── Bottom Actions ─────────────────────────────────

console.print()
console.print(
    "  [bold bright_magenta][P][/] [magenta]Process[/]"
    "  [bold bright_red][R][/] [red]Remove[/]"
    "  [bold bright_yellow][Q][/] [yellow]Quit[/]"
)
console.print()
console.print("  [bold bright_white]Enter number or command:[/] ", end="")
console.print("[dim]▎[/]")
console.print()
