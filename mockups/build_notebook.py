import json

notebook_path = (
    r"c:\Users\drago\Documents\Programming\Image-Converter\mockups\ui-mockups.ipynb"
)

# Combine Setup and Mocks to prevent out-of-order execution issues
init_cell = {
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "source": [
        "import sys\n",
        "import os\n",
        "from unittest.mock import MagicMock\n",
        "import questionary\n",
        "from rich.console import Console\n",
        "try:\n",
        "    from rich.group import Group\n",
        "except ImportError:\n",
        "    # Fallback for certain environments\n",
        "    from rich.console import Group\n",
        "\n",
        "# 1. Ensure project root is in path\n",
        "project_root = os.path.abspath('..')\n",
        "if project_root not in sys.path:\n",
        "    sys.path.insert(0, project_root)\n",
        "\n",
        "import rich_menu  # noqa: E402\n",
        "console = Console()\n",
        "\n",
        "# 2. Define Mocks\n",
        "def mock_metadata(path):\n",
        "    basename = os.path.basename(path)\n",
        "    data = {\n",
        "        'Hill Castle.png': ('1920 × 1080', '2.4 MB', 'PNG'),\n",
        "        'Spacecraft.png': ('1280 × 720', '1.8 MB', 'PNG'),\n",
        "        'Tree Clear Sky 1.png': ('2560 × 1440', '3.1 MB', 'PNG'),\n",
        "        'Tree Clear Sky 2.png': ('2560 × 1440', '2.9 MB', 'PNG'),\n",
        "    }\n",
        "    return data.get(basename, ('1024 × 1024', '1.0 MB', 'JPG'))\n",
        "\n",
        "def mock_checkbox(message, choices, **kwargs):\n",
        "    lines = []\n",
        "    for i, choice in enumerate(choices):\n",
        '        icon = "[bold green]☑[/]" if i < 2 else "[ ]"\n',
        '        lines.append(f"{icon} {choice.title}")\n',
        "    if 'instruction' in kwargs:\n",
        "         lines.append(f\"\\n[dim]{kwargs['instruction']}[/]\")\n",
        "    console.print(Group(*lines))\n",
        "    m = MagicMock()\n",
        "    m.ask.return_value = [c.value for c in choices[:2]]\n",
        "    return m\n",
        "\n",
        "# 3. Apply Mocks\n",
        "rich_menu._get_image_metadata = mock_metadata\n",
        "rich_menu.console.clear = lambda: None # Prevent clearing notebook output\n",
        "questionary.checkbox = mock_checkbox\n",
        "\n",
        'print("✅ Environment initialized, project modules linked, and mocks applied.")',
    ],
}

image_selector_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 1. Image Selection Menu\n",
        "The production `run_image_selector` rendering with non-blocking mocks.",
    ],
}

image_selector_code = {
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "source": [
        "images = ['Hill Castle.png', 'Spacecraft.png', 'Tree Clear Sky 1.png', 'Tree Clear Sky 2.png']\n",
        "rich_menu.run_image_selector(images, 'Base Images')",
    ],
}

combined_menu_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 2. Operations Pipeline Menu\n",
        "The production dashboard showing selected images and the current manipulation pipeline.",
    ],
}

combined_menu_code = {
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "source": [
        "dummy_images = [\n",
        "    {'name': 'Hill Castle.png', 'dims': '1920 × 1080', 'size': '2.4 MB', 'fmt': 'PNG'},\n",
        "    {'name': 'Spacecraft.png', 'dims': '1280 × 720', 'size': '1.8 MB', 'fmt': 'PNG'}\n",
        "]\n",
        "dummy_ops = [\n",
        "    {'dest': 'sharpen', 'values': [50]},\n",
        "    {'dest': 'border', 'values': [10, 'red', 'expand']},\n",
        "    {'dest': 'scale', 'values': ['1.5x']}\n",
        "]\n",
        "dummy_extra = {'resample': 'bilinear'}\n",
        "\n",
        "rich_menu.render_combined_menu(dummy_images, dummy_ops, dummy_extra)",
    ],
}

nb = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Image Converter | UI Mockups\n",
                "### ⚠️ Important: Run the Initialization cell below first!\n",
                "This notebook leverages actual production code (`rich_menu.py`) while bypassing interactive blocking inputs using mocks.",
            ],
        },
        init_cell,
        image_selector_md,
        image_selector_code,
        combined_menu_md,
        combined_menu_code,
    ],
    "metadata": {
        "kernelspec": {
            "display_name": ".venv",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

print("Generated UI mockups notebook.")
