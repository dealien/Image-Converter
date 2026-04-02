"""Interactive terminal menu.

Provides a fully interactive UI to select images and build an image processing pipeline.
"""

import os
import concurrent.futures
from types import SimpleNamespace
import questionary
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import Style
from prompt_toolkit.application.current import get_app
from prompt_toolkit.document import Document
from .processing import process_images_and_save
from .rich_menu import run_image_selector, render_combined_menu, _get_image_metadata
from typing import Any, Callable, Optional

from .main import console


# --- Helper Functions ---

_CUSTOM_STYLE = Style.from_dict(
    {
        "qmark": "#5F819D",  # Questionary default blueish
        "question": "bold",  # Questionary default bold
        "answer": "#FF9D00 bold",  # Questionary default Orange
        "default": "fg:cyan",  # Our custom Cyan for default
    }
)


def _ask_text(
    message: str,
    default_val: Optional[Any] = None,
    validate: Optional[Callable[[str], bool | str]] = None,
) -> str:
    """Prompt user using prompt_toolkit with colored defaults.

    Replaces `questionary.text(...).ask()`.

    Args:
        message: The prompt message to display.
        default_val: The default value to show and return if input is empty.
        validate: A validation function for the input that returns True/False or an error message string.

    Returns:
        The user's input, or the default value if no input was provided.

    """

    def get_prompt_text() -> list[tuple[str, str]]:
        """Dynamically generate the prompt text and styling based on current input buffer.

        Returns:
            list[tuple[str, str]]: A list of styled text tuples for the prompt.
        """
        # Dynamic prompt generation based on current input buffer
        try:
            text = get_app().current_buffer.text
        except Exception:
            text = ""

        formatted_msg = [("class:qmark", "? "), ("class:question", message)]

        if default_val is not None:
            formatted_msg.append(("", " [default: "))
            # If input is empty, color default cyan. Otherwise uncolored.
            style_class = "class:default" if not text else ""
            formatted_msg.append((style_class, str(default_val)))
            formatted_msg.append(("", "]"))

        formatted_msg.append(("class:question", ": "))
        return formatted_msg

    # Build Validator
    pt_validator = None
    if validate:

        class CustomValidator(Validator):
            def validate(self, document: Document) -> None:
                """Validate the prompt_toolkit document against the custom logic.

                Args:
                    document: The document to validate.

                Raises:
                    ValidationError: If the validation fails.
                """
                res = validate(document.text)
                if res is not True:
                    raise ValidationError(
                        message=res, cursor_position=len(document.text)
                    )

        pt_validator = CustomValidator()

    # interactive call
    session = PromptSession(
        style=_CUSTOM_STYLE, erase_when_done=True, lexer=SimpleLexer("class:answer")
    )
    result = session.prompt(get_prompt_text, validator=pt_validator)

    # Post-processing for display history
    final_answer = result
    if not result and default_val is not None:
        final_answer = str(default_val)

    final_msg = [("class:qmark", "? "), ("class:question", message)]
    if default_val is not None:
        final_msg.append(
            ("", f" [default: {default_val}]")
        )  # Always uncolored in history
    final_msg.append(("class:question", ": "))
    final_msg.append(("class:answer", final_answer))

    print_formatted_text(FormattedText(final_msg), style=_CUSTOM_STYLE)

    return result


def _format_operation_display(
    index: int, op: dict[str, Any], extra_args: dict[str, Any]
) -> str:
    """Format an operation dictionary into a readable CLI-like string for display.

    Args:
        index (int): The 0-based index of the operation in the pipeline.
        op (dict): The operation dictionary containing 'dest' and 'values'.
        extra_args (dict): Extra arguments (like resample, threshold) that modify the display.

    Returns:
        str: A formatted string representing the operation (e.g., "1. --scale 2.0x --resample bicubic").

    """
    op_name = op["dest"].replace("_", "-")
    op_vals = " ".join(map(str, op.get("values", [])))
    display_string = f"{index + 1}. --{op_name} {op_vals}"

    if op["dest"] == "scale" and "resample" in extra_args:
        display_string += f" --resample {extra_args['resample']}"

    if op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
        display_string += f" --threshold {extra_args.get('threshold', 50)}"

    return display_string


def _validate_number(
    min_val: float | None = None,
    max_val: float | None = None,
    value_type: type = int,
    allow_empty: bool = False,
) -> Callable[[str], bool | str]:
    """Create a validation function for numeric input within a specified range.

    Args:
        min_val (number, optional): The minimum allowed value. Defaults to None.
        max_val (number, optional): The maximum allowed value. Defaults to None.
        value_type (type, optional): The numeric type to cast to (e.g., int, float). Defaults to int.
        allow_empty (bool, optional): Whether an empty string is considered valid. Defaults to False.

    Returns:
        callable: A validation function that takes a string and returns True if valid, or an error message string otherwise.

    """

    def validator(val_str: str) -> "bool | str":
        """Validate the string input against the specified numeric constraints.

        Args:
            val_str (str): The string value to validate.

        Returns:
            bool | str: True if valid, or an error message string otherwise.
        """
        if not val_str:
            if allow_empty:
                return True
            return "Value cannot be empty."
        try:
            val = value_type(val_str)
            if min_val is not None and val < min_val:
                return f"Value must be at least {min_val}."
            if max_val is not None and val > max_val:
                return f"Value must be at most {max_val}."
            return True
        except ValueError:
            return (
                f"Please enter a valid {'integer' if value_type is int else 'number'}."
            )

    return validator


# --- Submenu Functions ---


def prompt_for_flip_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for image flipping options.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'flip', or None if canceled.

    """
    choice = questionary.select(
        "Select flip direction:",
        choices=["Horizontal", "Vertical", "Both"],
        instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
    ).ask()
    if not choice:
        return None
    return {"dest": "flip", "values": [choice.lower()]}


def prompt_for_scale_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for image scaling options and resampling filter.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary, modified in-place to store 'resample'. Defaults to None.

    Returns:
        dict: The operation dictionary for 'scale', or None if canceled.

    """
    console.print("\n[dim cyan]--- Scale Options ---[/]")

    def scale_validator(val_str: str) -> "bool | str":
        """Validate the string input for scaling factors or specific pixel dimensions.

        Args:
            val_str (str): The string value to validate.

        Returns:
            bool | str: True if valid, or an error message string otherwise.
        """
        if not val_str:
            return "Scale value cannot be empty."
        val_str = val_str.lower().strip()
        parts = val_str.split()

        # Accept:
        #   - scale factor: "1.5" or "1.5x"
        #   - dimensions: "400px 300px"
        if len(parts) == 1:
            token = parts[0]
            if token.endswith("x") and not token.endswith("px"):
                token = token[:-1]
            try:
                float(token)
                return True
            except ValueError:
                return "Invalid format. Use '1.5', '1.5x' or '400px 300px'."

        if len(parts) == 2 and all(p.endswith("px") for p in parts):
            return True

        return "Invalid format. Use '1.5', '1.5x' or '400px 300px'."

    values_str = _ask_text(
        "Enter scale value (e.g., '1.5x' OR '400px 300px')", validate=scale_validator
    )

    if not values_str:
        return None

    values = values_str.lower().split()

    resample_choice = questionary.select(
        "Select Resample Filter:",
        choices=["Nearest", "Bilinear", "Bicubic", "Lanczos"],
        default="Bilinear",
        instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
    ).ask()

    if not resample_choice:
        return None

    extra_args["resample"] = resample_choice.lower()

    return {"dest": "scale", "values": values}


def prompt_for_edge_detection_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for edge detection method and threshold (if applicable).

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary, modified in-place to store 'threshold'. Defaults to None.

    Returns:
        dict: The operation dictionary for 'edge_detection', or None if canceled.

    """
    method = questionary.select(
        "Select Edge Detection Method:",
        choices=["Sobel", "Canny", "Kovalevsky"],
        instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
    ).ask()

    if not method:
        return None

    method = method.lower()

    if method == "kovalevsky":
        val_str = _ask_text(
            "Enter threshold value (0-255)",
            default_val=50,
            validate=_validate_number(0, 255, allow_empty=True),
        )
        extra_args["threshold"] = int(val_str) if val_str else 50

    return {"dest": "edge_detection", "values": [method]}


def prompt_for_brightness_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a brightness adjustment value.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'brightness'.

    """
    val_str = _ask_text(
        "Enter brightness value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "brightness", "values": [int(val_str) if val_str else 0]}


def prompt_for_contrast_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a contrast adjustment value.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'contrast'.

    """
    val_str = _ask_text(
        "Enter contrast value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "contrast", "values": [int(val_str) if val_str else 0]}


def prompt_for_saturation_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a saturation adjustment value.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'saturation'.

    """
    val_str = _ask_text(
        "Enter saturation value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "saturation", "values": [int(val_str) if val_str else 0]}


def prompt_for_blur_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a blur radius.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'blur'.

    """
    val_str = _ask_text(
        "Enter blur radius (min 0.0)",
        default_val=2.0,
        validate=_validate_number(min_val=0.0, value_type=float, allow_empty=True),
    )
    return {"dest": "blur", "values": [float(val_str) if val_str else 2.0]}


def prompt_for_sharpen_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a sharpness intensity.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'sharpen'.

    """
    val_str = _ask_text(
        "Enter sharpness intensity (0-100)",
        default_val=50,
        validate=_validate_number(0, 100, allow_empty=True),
    )
    return {"dest": "sharpen", "values": [int(val_str) if val_str else 50]}


def prompt_for_color_balance_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for RGB color balance multipliers.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'color_balance'.

    """
    console.print(
        "[dim white]Enter multipliers for Red, Green, and Blue channels (e.g., 1.0 for no change).[/]"
    )

    r_str = _ask_text(
        "Red factor",
        default_val=1.0,
        validate=_validate_number(value_type=float, allow_empty=True),
    )
    g_str = _ask_text(
        "Green factor",
        default_val=1.0,
        validate=_validate_number(value_type=float, allow_empty=True),
    )
    b_str = _ask_text(
        "Blue factor",
        default_val=1.0,
        validate=_validate_number(value_type=float, allow_empty=True),
    )

    return {
        "dest": "color_balance",
        "values": [
            float(r_str) if r_str else 1.0,
            float(g_str) if g_str else 1.0,
            float(b_str) if b_str else 1.0,
        ],
    }


def prompt_for_hue_rotation_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for hue rotation degrees.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'hue_rotation'.

    """
    val_str = _ask_text(
        "Enter hue rotation degrees (0-360)",
        default_val=90,
        validate=_validate_number(0, 360, allow_empty=True),
    )
    return {"dest": "hue_rotation", "values": [int(val_str) if val_str else 90]}


def prompt_for_posterize_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for the number of bits for posterization.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'posterize'.

    """
    val_str = _ask_text(
        "Enter number of bits (1-8)",
        default_val=4,
        validate=_validate_number(1, 8, allow_empty=True),
    )
    return {"dest": "posterize", "values": [int(val_str) if val_str else 4]}


def prompt_for_border_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for border thickness, color, and position.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'border', or None if canceled.

    """
    thickness_str = _ask_text(
        "Enter border thickness (0-500)",
        default_val=10,
        validate=_validate_number(0, 500, allow_empty=True),
    )

    color_str = _ask_text("Enter border color (Name or Hex)", default_val="black")

    position = questionary.select(
        "Border Position:",
        choices=["Expand", "Inside"],
        instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
    ).ask()

    if not position:
        return None

    return {
        "dest": "border",
        "values": [
            int(thickness_str) if thickness_str else 10,
            color_str if color_str else "black",
            position.lower(),
        ],
    }


def prompt_for_vignette_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for a vignette intensity.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'vignette'.

    """
    val_str = _ask_text(
        "Enter vignette intensity (0-100)",
        default_val=50,
        validate=_validate_number(0, 100, allow_empty=True),
    )
    return {"dest": "vignette", "values": [int(val_str) if val_str else 50]}


def prompt_for_rotation_options(
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Prompts the user for an image rotation angle.

    Args:
        extra_args (dict, optional): Shared extra arguments dictionary. Defaults to None.

    Returns:
        dict: The operation dictionary for 'rotate'.

    """
    angle_str = _ask_text(
        "Enter rotation angle (will clamp to nearest 90)",
        default_val=90,
        validate=_validate_number(-3600, 3600, allow_empty=True),
    )
    return {"dest": "rotate", "values": [int(angle_str) if angle_str else 90]}


# --- Main Menu Configuration ---

AVAILABLE_MANIPULATIONS = [
    {"dest": "flip", "name": "Flip Image", "handler": prompt_for_flip_options},
    {"dest": "scale", "name": "Scale Image", "handler": prompt_for_scale_options},
    {"dest": "remove_background", "name": "Remove Background", "handler": None},
    {"dest": "invert", "name": "Invert Colors", "handler": None},
    {"dest": "grayscale", "name": "Convert to Grayscale", "handler": None},
    {
        "dest": "edge_detection",
        "name": "Apply Edge Detection",
        "handler": prompt_for_edge_detection_options,
    },
    {
        "dest": "brightness",
        "name": "Adjust Brightness",
        "handler": prompt_for_brightness_options,
    },
    {
        "dest": "contrast",
        "name": "Adjust Contrast",
        "handler": prompt_for_contrast_options,
    },
    {
        "dest": "saturation",
        "name": "Adjust Saturation",
        "handler": prompt_for_saturation_options,
    },
    {"dest": "blur", "name": "Apply Gaussian Blur", "handler": prompt_for_blur_options},
    {"dest": "sharpen", "name": "Apply Sharpen", "handler": prompt_for_sharpen_options},
    {
        "dest": "color_balance",
        "name": "Adjust Color Balance",
        "handler": prompt_for_color_balance_options,
    },
    {
        "dest": "hue_rotation",
        "name": "Rotate Hue",
        "handler": prompt_for_hue_rotation_options,
    },
    {
        "dest": "posterize",
        "name": "Apply Posterize",
        "handler": prompt_for_posterize_options,
    },
    {"dest": "border", "name": "Add Border", "handler": prompt_for_border_options},
    {
        "dest": "vignette",
        "name": "Apply Vignette",
        "handler": prompt_for_vignette_options,
    },
    {"dest": "rotate", "name": "Rotate Image", "handler": prompt_for_rotation_options},
]

# --- Menu Logic ---


def remove_manipulation(
    operations: list[dict[str, Any]], extra_args: dict[str, Any]
) -> list[dict[str, Any]]:
    """Presents a menu to remove a previously added manipulation from the pipeline.

    Args:
        operations (list): The list of current operation dictionaries. Modified in-place.
        extra_args (dict): The extra arguments dictionary. Modified in-place to clean up orphaned arguments.

    Returns:
        list: The updated list of operations.

    """
    if not operations:
        console.print("\n[yellow]There are no operations to remove.[/]")
        console.print(
            "[dim white]Please select some operations from the menu to build your pipeline first.[/]"
        )
        return operations

    choices = [
        questionary.Choice(title=_format_operation_display(i, op, extra_args), value=i)
        for i, op in enumerate(operations)
    ]
    choices.append(questionary.Choice(title="Cancel", value=-1))

    choice_idx = questionary.select(
        "Select operation to remove:",
        choices=choices,
        instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
    ).ask()

    if choice_idx == -1 or choice_idx is None:
        return operations

    removed_op = operations.pop(choice_idx)
    console.print(f"\n[yellow]Removed '{removed_op['dest']}'.[/]")

    # Cleanup extra args logic
    remaining_dests = set()
    has_kovalevsky = False
    for op in operations:
        dest = op["dest"]
        remaining_dests.add(dest)
        if dest == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
            has_kovalevsky = True

    if removed_op["dest"] == "scale" and "scale" not in remaining_dests:
        extra_args.pop("resample", None)

    if not has_kovalevsky:
        extra_args.pop("threshold", None)

    return operations


def select_images() -> list[str]:
    """Find images in the 'Base Images' directory and prompts the user to select them.

    Returns:
        list: A list of selected image file paths.

    """
    image_dir = "Base Images"
    if not os.path.isdir(image_dir):
        console.print(f"[red]Error: Directory '{image_dir}' not found.[/]")
        console.print(
            "[dim white]Please create the directory, place some images in it, and try again, or specify a path via CLI.[/]\n"
        )
        return []

    try:
        all_files = os.listdir(image_dir)
        image_files = sorted(
            [
                f
                for f in all_files
                if os.path.isfile(os.path.join(image_dir, f))
                and f.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp")
                )
            ]
        )
    except Exception as e:
        console.print(f"[red]Read error: {e}[/]")
        return []

    if not image_files:
        console.print(f"\n[yellow]No images found in '{image_dir}'.[/]")
        console.print(
            "[dim white]Please place some images (e.g., .jpg, .png) in this directory and try again, or specify a path via CLI.[/]\n"
        )
        return []

    while True:
        selected_paths = run_image_selector(image_files, image_dir)

        if selected_paths is None:  # User pressed Ctrl-C
            return []

        if selected_paths:
            return selected_paths

        confirm = questionary.confirm(
            "No images selected. Re-select images?", default=True
        ).ask()
        if not confirm:
            return []


def select_manipulations(
    images_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str], list[int]]:
    """Presents the main interactive menu for building the image processing pipeline.

    Args:
        images_data (list): A list of dictionaries containing metadata for the selected images.

    Returns:
        tuple: A tuple containing the list of selected operations and the extra arguments dictionary.

    """
    selected_operations = []
    extra_args = {}
    output_formats = []
    output_qualities = []

    # Define Categories mapping to format the interactive tree
    CATEGORIES = {
        "Color": (
            "🎨 Color",
            [
                "Convert to Grayscale",
                "Invert Colors",
                "Adjust Brightness",
                "Adjust Contrast",
                "Adjust Saturation",
                "Adjust Color Balance",
                "Rotate Hue",
            ],
        ),
        "Transform": ("📐 Transform", ["Scale Image", "Flip Image", "Rotate Image"]),
        "Effects": (
            "✨ Effects & Filters",
            [
                "Remove Background",
                "Apply Gaussian Blur",
                "Apply Sharpen",
                "Apply Edge Detection",
                "Apply Posterize",
                "Add Border",
                "Apply Vignette",
            ],
        ),
    }

    # Map name back to original list index so handlers can be triggered correctly
    name_to_idx = {m["name"]: i for i, m in enumerate(AVAILABLE_MANIPULATIONS)}

    while True:
        # Render the beautiful combined layout first
        render_combined_menu(images_data, selected_operations, extra_args)

        # Build interactive tree as questionary choices
        choices = []

        # Action Groups
        choices.append(questionary.Separator(line="⚡ Actions"))
        choices.append(questionary.Choice("   ▶ Run Processing", value="PROCESS"))
        if selected_operations:
            choices.append(
                questionary.Choice("   ❌ Remove an Operation", value="REMOVE")
            )
        choices.append(questionary.Separator(line=""))

        # Operations Tree Root
        choices.append(questionary.Separator(line="🛠️  Available Operations"))

        cats = list(CATEGORIES.items())
        for c_idx, (cat_key, (cat_label, op_names)) in enumerate(cats):
            is_last_cat = c_idx == len(cats) - 1
            cat_prefix = "└── " if is_last_cat else "├── "

            choices.append(questionary.Separator(line=f"{cat_prefix}{cat_label}"))

            for o_idx, op_name in enumerate(op_names):
                is_last_op = o_idx == len(op_names) - 1

                # Determine proper indentation based on parent branch
                indent = "    " if is_last_cat else "│   "
                op_prefix = "└── " if is_last_op else "├── "

                idx = name_to_idx.get(op_name, -1)
                display_str = f"{indent}{op_prefix}{op_name}"

                # We skip missing operations robustly
                if idx != -1:
                    choices.append(questionary.Choice(display_str, value=idx))

        selection = questionary.select(
            "",
            choices=choices,
            pointer="▶",
            use_indicator=False,
            instruction="(Use arrow keys to navigate, Enter to select, Ctrl+C to cancel)",
        ).ask()

        if selection is None:  # C-c
            raise KeyboardInterrupt

        if selection == "PROCESS":
            if not selected_operations:
                confirm = questionary.confirm(
                    "Pipeline is empty. Process anyway?", default=False
                ).ask()
                if not confirm:
                    continue

            # --- Output Format Prompts ---
            console.print("\n[dim cyan]--- Output Format ---[/]")
            available_formats = [
                "PNG",
                "JPG",
                "JPEG",
                "WEBP",
                "BMP",
                "TIFF",
                "GIF",
                "HEIC",
                "AVIF",
            ]

            selected_formats = questionary.checkbox(
                "Select Output Formats (Leave empty for original format):",
                choices=available_formats,
                instruction="(Use Space to select/deselect, Enter to confirm, Ctrl+C to cancel)",
            ).ask()

            if selected_formats:
                output_formats = [f.lower() for f in selected_formats]
                for fmt in output_formats:
                    # Formats that don't support quality setting natively or usually
                    if fmt in ["png", "bmp", "gif", "tiff"]:
                        output_qualities.append(100)
                        continue

                    q_str = _ask_text(
                        f"Enter quality for {fmt.upper()} (1-100)",
                        default_val=90,
                        validate=_validate_number(1, 100, allow_empty=True),
                    )
                    output_qualities.append(int(q_str) if q_str else 90)

            flatten_confirm = questionary.confirm(
                "Flatten transparent backgrounds?", default=False
            ).ask()
            if flatten_confirm:
                flatten_color = _ask_text(
                    "Background color for flattening (Name or Hex)", default_val="white"
                )
                extra_args["flatten"] = flatten_color if flatten_color else "white"

            break
        elif selection == "REMOVE":
            remove_manipulation(selected_operations, extra_args)
        else:
            # It's an index for a manipulation
            idx = selection
            manip = AVAILABLE_MANIPULATIONS[idx]
            handler = manip.get("handler")

            op_details = None
            if handler:
                op_details = handler(extra_args)
            else:
                op_details = {"dest": manip["dest"], "values": []}

            if op_details:
                selected_operations.append(op_details)

    return selected_operations, extra_args, output_formats, output_qualities


def interactive_menu():
    """Run the main entry point for the interactive terminal UI.

    Handles image selection, pipeline construction, and executes the processing.
    """
    try:
        # We don't need the basic print anymore, the menu handles it.
        paths = select_images()
        if not paths:
            console.print("[yellow]No images selected.[/]")
            console.print(
                "[dim white]Please run the command again and select at least one image to process.[/]"
            )
            return

        def _fetch_selected_image_data(p: str) -> dict:
            """Fetch metadata for a selected image file path.

            Args:
                p (str): The path to the image file.

            Returns:
                dict: A dictionary containing image metadata.
            """
            dims, size_str, fmt = _get_image_metadata(p)
            return {
                "name": os.path.basename(p),
                "dims": dims,
                "size": size_str,
                "fmt": fmt,
                "path": p,
            }

        with concurrent.futures.ThreadPoolExecutor() as executor:
            images_data = list(executor.map(_fetch_selected_image_data, paths))

        ops, extra_args, out_formats, out_qualities = select_manipulations(images_data)

        # Prepare args
        mock_args = SimpleNamespace(
            resample=extra_args.get("resample", "bilinear"),
            threshold=extra_args.get("threshold", 50),
            format=out_formats if out_formats else None,
            quality=out_qualities if out_qualities else None,
            flatten=extra_args.get("flatten", None),
        )

        # Process expects a list of [name, path] lists as per existing logic
        process_images_data = [[img["name"], img["path"]] for img in images_data]
        process_images_and_save(process_images_data, ops, mock_args)

        console.print("\n[bright_green]✨ Processing Complete ✨[/]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
