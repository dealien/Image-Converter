"""
Mockup: Rich Processing Output Log
Run this script to preview how processing output could look with Rich.

Usage: .venv\Scripts\python.exe mockups\mockup_output.py
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()

# ── Processing Header ──────────────────────────────

console.print()
console.print(
    Panel(
        "[bold bright_white]Processing[/] [bright_cyan]4[/] [bold bright_white]images...[/]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(0, 2),
        expand=False,
    )
)
console.print()

# ── Simulated Processing Output ────────────────────

images = [
    {
        "name": "Hill Castle.png",
        "ops": [("Applying Sharpen", "intensity: 50")],
        "success": True,
    },
    {
        "name": "Spacecraft.png",
        "ops": [("Removing background", None), ("Scaling by factor", "1.5x")],
        "success": True,
    },
    {
        "name": "Tree Clear Sky 1.png",
        "ops": [("Applying Edge Detection", "sobel")],
        "success": False,
        "error": "Unsupported color mode for this operation",
    },
    {
        "name": "Tree Clear Sky 2.png",
        "ops": [("Inverting colors", None), ("Adding border", "10px, red, expand")],
        "success": True,
    },
]

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
    overall = progress.add_task("Overall Progress", total=len(images))

    for i, img in enumerate(images, 1):
        console.print()
        # Image header
        header = Text()
        header.append(f"[{i}/{len(images)}] ", style="bold bright_yellow")
        header.append(img["name"], style="bold bright_white")

        console.print(
            Panel(
                header,
                border_style="bright_magenta" if img["success"] else "bright_red",
                box=box.HEAVY,
                padding=(0, 1),
                expand=True,
            )
        )

        # Operations
        for op_name, op_detail in img["ops"]:
            detail_str = f" ({op_detail})" if op_detail else ""
            console.print(f"  [bright_yellow]›[/] [yellow]{op_name}{detail_str}...[/]")
            time.sleep(0.3)  # Simulate work

        # Result
        if img["success"]:
            console.print(
                f"  [bright_green]✓[/] [green]Saved to: Output/{img['name'].replace('.png', '.png')}[/]"
            )
        else:
            console.print(f"  [bright_red]✗[/] [red]Error: {img['error']}[/]")

        progress.advance(overall)
        time.sleep(0.2)

# ── Summary ────────────────────────────────────────

console.print()
console.print(Rule("Results", style="bright_cyan"))
console.print()

summary_table = Table(box=box.SIMPLE_HEAVY, border_style="dim", padding=(0, 2))
summary_table.add_column("Metric", style="bold bright_white")
summary_table.add_column("Value", justify="right")

succeeded = sum(1 for img in images if img["success"])
failed = sum(1 for img in images if not img["success"])

summary_table.add_row("✓ Succeeded", f"[bold bright_green]{succeeded}[/]")
summary_table.add_row("✗ Failed", f"[bold bright_red]{failed}[/]")
summary_table.add_row("Total", f"[bold bright_white]{len(images)}[/]")
summary_table.add_row("Time Elapsed", "[bright_cyan]2.4s[/]")

console.print(summary_table)
console.print()
