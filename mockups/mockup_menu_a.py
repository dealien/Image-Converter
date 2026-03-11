"""
Mockup A: Full-featured Rich Menu Layout
Run this script to preview how the menu could look with Rich.

Usage: .venv\Scripts\python.exe mockups\mockup_menu_a.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console()

# ── Header ──────────────────────────────────────────

header_text = Text()
header_text.append("✨ Image Converter", style="bold white")
header_text.append("\n")
header_text.append("Interactive Image Processor", style="dim italic cyan")

console.print()
console.print(
    Panel(
        header_text,
        border_style="bright_blue",
        box=box.DOUBLE_EDGE,
        padding=(1, 4),
        expand=False,
    )
)

# ── Selected Images Table ──────────────────────────

console.print()
img_table = Table(
    title="📁 Selected Images",
    box=box.ROUNDED,
    title_style="bold bright_cyan",
    border_style="dim cyan",
    header_style="bold bright_white",
    row_styles=["", "dim"],
    padding=(0, 1),
)
img_table.add_column("#", style="dim white", justify="right", width=3)
img_table.add_column("Filename", style="bright_white", min_width=28)
img_table.add_column("Size", style="bright_yellow", justify="right", width=10)
img_table.add_column("Format", style="bright_magenta", width=8)

img_table.add_row("1", "Hill Castle.png", "2.4 MB", "PNG")
img_table.add_row("2", "Spacecraft.png", "1.8 MB", "PNG")
img_table.add_row("3", "Tree Clear Sky 1.png", "3.1 MB", "PNG")
img_table.add_row("4", "Tree Clear Sky 2.png", "2.9 MB", "PNG")

console.print(img_table)

# ── Operations Pipeline ────────────────────────────

console.print()
pipeline_content = Text()
pipeline_content.append("  1. ", style="dim white")
pipeline_content.append("Sharpen", style="bold bright_green")
pipeline_content.append(" (intensity: 50)", style="green")
pipeline_content.append("\n")
pipeline_content.append("  2. ", style="dim white")
pipeline_content.append("Add Border", style="bold bright_cyan")
pipeline_content.append(" (10px, red, expand)", style="cyan")

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

# ── Action Menu ────────────────────────────────────

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
