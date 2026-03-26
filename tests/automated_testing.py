import os
import subprocess
import sys
import time

from rich import box
from rich.console import Console
from rich.table import Table

# Initialize Rich Console
console = Console()

"""
Normal testing of the program is done using pytest.

This file is for automated testing of all arguments and operations of the 
program by running it as a user would from the command line.

Just run this file and it will run all the commands in the commands list.

This file should be kept up to date when new arguments or operations are 
added to the program.
"""


def run_command(args):
    """Runs a single command with the current python executable and returns elapsed time."""
    cmd = [sys.executable, "-m", "image_converter"] + args
    console.print(f"🚀 [bold cyan]Running:[/] [white]{' '.join(cmd)}[/]")
    start_time = time.time()
    result = subprocess.run(cmd, cwd=os.getcwd())
    end_time = time.time()
    if result.returncode != 0:
        console.print(
            f"❌ [bold red]Command failed with return code {result.returncode}[/]"
        )
        sys.exit(result.returncode)
    return end_time - start_time


def main():
    commands = [
        [
            ".\\tests\\test_images\\*",
            "--invert",
            "--flip",
            "vertical",
            "--grayscale",
            "--invert",
        ],
        [
            ".\\tests\\test_images\\*",
            "--brightness",
            "20",
            "--edge-detection",
            "canny",
            "--flip",
            "horizontal",
        ],
        [".\\tests\\test_images\\*", "--saturation", "-15", "--grayscale", "--invert"],
        [".\\tests\\test_images\\*", "--remove-background"],
        [".\\tests\\test_images\\*", "--scale", "0.5", "--resample", "bicubic"],
        [
            ".\\tests\\test_images\\*",
            "--scale",
            "800px",
            "600px",
            "--resample",
            "lanczos",
        ],
        [".\\tests\\test_images\\*", "--flip", "both"],
        [".\\tests\\test_images\\*", "--edge-detection", "sobel"],
        [
            ".\\tests\\test_images\\*",
            "--edge-detection",
            "kovalevsky",
            "--threshold",
            "60",
        ],
        [".\\tests\\test_images\\*", "--contrast", "50"],
        [".\\tests\\test_images\\*", "--color-balance", "1.2", "0.8", "0.8"],
        [".\\tests\\test_images\\*", "--hue-rotation", "90"],
        [".\\tests\\test_images\\*", "--posterize", "4"],
        [".\\tests\\test_images\\*", "--blur", "10"],
        [".\\tests\\test_images\\*", "--sharpen", "10"],
        [".\\tests\\test_images\\*", "--border", "10", "red", "expand"],
        [".\\tests\\test_images\\*", "--vignette", "60"],
        [".\\tests\\test_images\\*", "--rotate", "90"],
        # Format and Quality tests
        [".\\tests\\test_images\\*"],  # Default original format
        [
            ".\\tests\\test_images\\*",
            "--format",
            "jpg",
            "--quality",
            "50",
            "--format",
            "webp",
            "--quality",
            "85",
        ],
        [".\\tests\\test_images\\*", "--format", "png", "--format", "avif"],
    ]

    console.print("\n[bold bright_magenta]✨ Starting automated testing scenario...[/]")
    results = []

    for args in commands:
        elapsed = run_command(args)
        command_str = " ".join(args[1:])
        results.append((command_str, elapsed))

    console.print(
        "\n[bold bright_green]✅ Automated testing scenario completed successfully![/]"
    )

    table = Table(
        title="📊 Benchmark Results",
        box=box.ROUNDED,
        title_style="bold bright_cyan",
        border_style="dim cyan",
        header_style="bold bright_white",
    )
    table.add_column("Command Target", style="cyan")
    table.add_column("Time (s)", justify="right", style="bright_green")

    total_time = 0
    for cmd, elapsed in results:
        table.add_row(cmd, f"{elapsed:.2f}")
        total_time += elapsed

    table.add_section()
    table.add_row("[bold]Total Time[/bold]", f"[bold]{total_time:.2f}[/bold]")

    console.print()
    console.print(table)


if __name__ == "__main__":
    main()
