"""
Mockup: Rich Processing Output + Detailed Results Table
Shows the full processing flow with a results table listing
output file sizes and dimensions.

Usage: .venv\Scripts\python.exe mockups\mockup_results.py
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
    "✨ [bold cyan]Image Converter[/] | [italic white]Interactive Image Processor[/]",
    justify="left",
)
console.rule(style="dim")
console.print()
console.print(
    "[bold bright_white]Processing[/] [bright_cyan]4[/] [bold bright_white]images...[/]"
)
console.print()

# ── Simulated Processing Output ────────────────────

images = [
    {
        "name": "Hill Castle.png",
        "ops": [
            ("Applying Sharpen", "intensity: 50"),
            ("Adding border", "10px, red, expand"),
        ],
        "success": True,
        "out_dims": "1940 × 1100",
        "out_size": "2.6 MB",
    },
    {
        "name": "Spacecraft.png",
        "ops": [
            ("Applying Sharpen", "intensity: 50"),
            ("Adding border", "10px, red, expand"),
        ],
        "success": True,
        "out_dims": "1300 × 740",
        "out_size": "1.9 MB",
    },
    {
        "name": "Tree Clear Sky 1.png",
        "ops": [
            ("Applying Sharpen", "intensity: 50"),
            ("Adding border", "10px, red, expand"),
        ],
        "success": False,
        "error": "Unsupported color mode for border operation",
        "out_dims": "—",
        "out_size": "—",
    },
    {
        "name": "Tree Clear Sky 2.png",
        "ops": [
            ("Applying Sharpen", "intensity: 50"),
            ("Adding border", "10px, red, expand"),
        ],
        "success": True,
        "out_dims": "2580 × 1460",
        "out_size": "3.2 MB",
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
            time.sleep(0.2)

        # Result
        if img["success"]:
            output_name = img["name"].rsplit(".", 1)[0] + ".png"
            console.print(
                f"  [bright_green]✓[/] [green]Saved to: Output/{output_name}[/]"
            )
        else:
            console.print(f"  [bright_red]✗[/] [red]Error: {img['error']}[/]")

        progress.advance(overall)
        time.sleep(0.15)

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

for i, img in enumerate(images, 1):
    output_name = img["name"].rsplit(".", 1)[0] + ".png"
    if img["success"]:
        status = Text("✓ OK", style="bold bright_green")
        fname_style = "bright_white"
        dims = Text(img["out_dims"], style="bright_green")
        size = Text(img["out_size"], style="bright_yellow")
    else:
        status = Text("✗ FAIL", style="bold bright_red")
        fname_style = "dim red"
        dims = Text("—", style="dim red")
        size = Text("—", style="dim red")

    results_table.add_row(
        str(i),
        Text(output_name, style=fname_style),
        status,
        dims,
        size,
    )

console.print(results_table)

# ── Summary Stats ──────────────────────────────────

console.print()

succeeded = sum(1 for img in images if img["success"])
failed = sum(1 for img in images if not img["success"])

summary = Text("  ")
summary.append(f"✓ {succeeded} succeeded", style="bold bright_green")
summary.append("  │  ", style="dim")
summary.append(f"✗ {failed} failed", style="bold bright_red")
summary.append("  │  ", style="dim")
summary.append(f"{len(images)} total", style="bold bright_white")
summary.append("  │  ", style="dim")
summary.append("⏱ 2.4s", style="bright_cyan")

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
