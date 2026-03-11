"""
Mockup: Image Selection Menu
Shows how the image picker would look with Rich formatting,
including selection indicators, dimensions, and file sizes.

Usage: .venv\Scripts\python.exe mockups\mockup_image_select.py
"""

from rich.console import Console
from rich.table import Table
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

# ── Image Selection Table ──────────────────────────

console.print()
console.print(
    "[dim]Use [bright_white]Space[/] to select, "
    "[bright_white]Enter[/] to confirm, "
    "[bright_white]A[/] to toggle all[/]"
)
console.print()

select_table = Table(
    title="📁 Select Images to Process",
    box=box.ROUNDED,
    title_style="bold bright_cyan",
    border_style="dim cyan",
    header_style="bold bright_white",
    padding=(0, 1),
)
select_table.add_column("", width=3, justify="center")  # checkbox
select_table.add_column("#", style="dim white", justify="right", width=3)
select_table.add_column("Filename", style="bright_white", min_width=28)
select_table.add_column("Dimensions", style="bright_green", justify="center", width=14)
select_table.add_column("Size", style="bright_yellow", justify="right", width=10)
select_table.add_column("Format", style="bright_magenta", width=8)

# Simulated selection state
images = [
    ("Desert Wasteland.webp", "3840 × 2160", "4.7 MB", "WEBP", True),
    ("Hill Castle.png", "1920 × 1080", "2.4 MB", "PNG", True),
    ("Horizon.png", "2560 × 1440", "3.5 MB", "PNG", False),
    ("Rainbow Garden.png", "1280 × 960", "1.2 MB", "PNG", False),
    ("Spacecraft.png", "1280 × 720", "1.8 MB", "PNG", True),
    ("Tree Clear Sky 1.png", "2560 × 1440", "3.1 MB", "PNG", False),
    ("Tree Clear Sky 2.png", "2560 × 1440", "2.9 MB", "PNG", False),
]

# Currently highlighted row (simulating arrow key position)
cursor_row = 3

for i, (name, dims, size, fmt, selected) in enumerate(images):
    is_cursor = i == cursor_row

    checkbox = Text("●" if selected else "○")
    checkbox.stylize("bright_green" if selected else "dim white")

    row_num = str(i + 1)

    if is_cursor:
        fname = Text(name, style="bold black on white")
    elif selected:
        fname = Text(name, style="bold bright_white")
    else:
        fname = Text(name, style="bright_white")

    select_table.add_row(
        checkbox,
        row_num,
        fname,
        Text(dims, style="bright_green"),
        Text(size, style="bright_yellow"),
        Text(fmt, style="bright_magenta"),
    )

console.print(select_table)

# ── Footer ─────────────────────────────────────────

console.print()
selected_count = sum(1 for *_, s in images if s)
total_count = len(images)
console.print(
    f"  [bright_green]{selected_count}[/] [dim]of[/] "
    f"[bright_white]{total_count}[/] [dim]images selected[/]"
)
console.print()
