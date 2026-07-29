import os
import subprocess
import sys
import time

from rich import box
from rich.console import Console
from rich.table import Table

# Add project root src directory to sys.path if not present
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from image_converter.main import create_parser  # noqa: E402

# Initialize Rich Console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()

"""
Normal testing of the program is done using pytest.

This file is for automated testing of all arguments and operations of the 
program by running it as a user would from the command line.

Just run this file and it will run all the commands in the commands list.

This file should be kept up to date when new arguments or operations are 
added to the program.
"""


class ValidationError(Exception):
    """Raised when a command argument list fails validation against the CLI parser."""


def validate_command(args: list[str]) -> None:
    """Validates a single list of CLI arguments using the core argument parser.

    Args:
        args (list[str]): The list of command-line argument tokens.

    Raises:
        ValidationError: If the arguments contain unknown flags, invalid values, or wrong counts.

    """
    parser = create_parser()
    error_msgs = []

    def error_override(message):
        error_msgs.append(message)
        raise ValidationError(message)

    parser.error = error_override
    try:
        parser.parse_args(args)
    except (ValidationError, SystemExit) as e:
        msg = error_msgs[0] if error_msgs else str(e)
        raise ValidationError(msg) from e


def validate_commands(commands: list[list[str]]) -> None:
    """Validates all input commands prior to running benchmark execution.

    Args:
        commands (list[list[str]]): List of CLI argument lists to validate.

    Raises:
        SystemExit: If any command fails validation.

    """
    console.print("\n[bold bright_cyan]✨ Validating command formatting...[/]")
    invalid_commands = []

    for idx, args in enumerate(commands, start=1):
        try:
            validate_command(args)
        except ValidationError as err:
            invalid_commands.append((idx, " ".join(args), str(err)))

    if invalid_commands:
        console.print(
            f"\n❌ [bold red]Found {len(invalid_commands)} command formatting error(s):[/]"
        )
        for idx, cmd_str, err_msg in invalid_commands:
            console.print(f"  [bold yellow]Command #{idx}:[/] [white]{cmd_str}[/]")
            console.print(f"    [red]Error:[/] {err_msg}")
        console.print(
            "\n[bold red]Validation failed! Aborting test execution before running operations.[/]"
        )
        sys.exit(1)

    console.print(
        f"✓ [bold green]All {len(commands)} commands validated successfully![/]\n"
    )


def run_command(args: list[str]) -> float:
    """Runs a single command with the current python executable and returns elapsed time.

    Args:
        args (list[str]): The argument list to pass to the image_converter module.

    Returns:
        float: Elapsed execution time in seconds.

    """
    cmd = [sys.executable, "-m", "image_converter"] + args
    console.print(f"🚀 [bold cyan]Running:[/] [white]{' '.join(cmd)}[/]")
    start_time = time.time()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(cmd, cwd=os.getcwd(), env=env)
    end_time = time.time()
    if result.returncode != 0:
        console.print(
            f"❌ [bold red]Command failed with return code {result.returncode}[/]"
        )
        sys.exit(result.returncode)
    return end_time - start_time


def main():
    """Execute pre-run command validation and run the automated benchmark scenario."""
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
        [".\\tests\\test_images\\*", "--oil-painting", "50"],
        [".\\tests\\test_images\\*", "--cartoonify", "50"],
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

    validate_commands(commands)

    console.print("[bold bright_magenta]✨ Starting automated testing scenario...[/]")
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
