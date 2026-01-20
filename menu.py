import os
import inspect
from types import SimpleNamespace
from PIL import Image
import questionary
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.styles import Style
from prompt_toolkit.application.current import get_app
from processing import process_images_and_save


# --- Helper Functions ---

_CUSTOM_STYLE = Style.from_dict(
    {
        "qmark": "#5F819D",  # Questionary default blueish
        "question": "bold",  # Questionary default bold
        "answer": "#FF9D00 bold",  # Questionary default Orange
        "default": "fg:cyan",  # Our custom Cyan for default
    }
)


def _ask_text(message, default_val=None, validate=None):
    """
    Custom text prompt helper using prompt_toolkit to support colored defaults.
    Replaces questionary.text(...).ask()
    """

    def get_prompt_text():
        # Dynamic prompt generation based on current input buffer
        try:
            # text = get_app().current_buffer.text  # This works in full app
            # For prompt() shortcut, we might need a safer access if app not ready
            # But prompt() initializes app before rendering.
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
            def validate(self, document):
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


def _format_operation_display(index, op, extra_args):
    op_name = op["dest"].replace("_", "-")
    op_vals = " ".join(map(str, op.get("values", [])))
    display_string = f"{index + 1}. --{op_name} {op_vals}"

    if op["dest"] == "scale" and "resample" in extra_args:
        display_string += f" --resample {extra_args['resample']}"

    if op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
        display_string += f" --threshold {extra_args.get('threshold', 50)}"

    return display_string


def _validate_number(min_val=None, max_val=None, value_type=int, allow_empty=False):
    def validator(val_str):
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


def prompt_for_flip_options():
    choice = questionary.select(
        "Select flip direction:", choices=["Horizontal", "Vertical", "Both"]
    ).ask()
    if not choice:
        return None
    return {"dest": "flip", "values": [choice.lower()]}


def prompt_for_scale_options(extra_args):
    print("\n--- Scale Options ---")

    def scale_validator(val_str):
        if not val_str:
            return "Scale value cannot be empty."
        val_str = val_str.lower()
        parts = val_str.split()
        if (
            len(parts) == 1 and parts[0].endswith("x") and not parts[0].endswith("px")
        ) or (len(parts) == 2 and all(p.endswith("px") for p in parts)):
            return True
        return "Invalid format. Use '1.5x' or '400px 300px'."

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
    ).ask()

    if not resample_choice:
        return None

    extra_args["resample"] = resample_choice.lower()

    return {"dest": "scale", "values": values}


def prompt_for_edge_detection_options(extra_args):
    method = questionary.select(
        "Select Edge Detection Method:", choices=["Sobel", "Canny", "Kovalevsky"]
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


def prompt_for_brightness_options():
    val_str = _ask_text(
        "Enter brightness value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "brightness", "values": [int(val_str) if val_str else 0]}


def prompt_for_contrast_options():
    val_str = _ask_text(
        "Enter contrast value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "contrast", "values": [int(val_str) if val_str else 0]}


def prompt_for_saturation_options():
    val_str = _ask_text(
        "Enter saturation value (-100 to 100)",
        default_val=0,
        validate=_validate_number(-100, 100, allow_empty=True),
    )
    return {"dest": "saturation", "values": [int(val_str) if val_str else 0]}


def prompt_for_blur_options():
    val_str = _ask_text(
        "Enter blur radius (min 0.0)",
        default_val=2.0,
        validate=_validate_number(min_val=0.0, value_type=float, allow_empty=True),
    )
    return {"dest": "blur", "values": [float(val_str) if val_str else 2.0]}


def prompt_for_sharpen_options():
    val_str = _ask_text(
        "Enter sharpness intensity (0-100)",
        default_val=50,
        validate=_validate_number(0, 100, allow_empty=True),
    )
    return {"dest": "sharpen", "values": [int(val_str) if val_str else 50]}


def prompt_for_color_balance_options():
    print(
        "Enter multipliers for Red, Green, and Blue channels (e.g., 1.0 for no change)."
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


def prompt_for_hue_rotation_options():
    val_str = _ask_text(
        "Enter hue rotation degrees (0-360)",
        default_val=90,
        validate=_validate_number(0, 360, allow_empty=True),
    )
    return {"dest": "hue_rotation", "values": [int(val_str) if val_str else 90]}


def prompt_for_posterize_options():
    val_str = _ask_text(
        "Enter number of bits (1-8)",
        default_val=4,
        validate=_validate_number(1, 8, allow_empty=True),
    )
    return {"dest": "posterize", "values": [int(val_str) if val_str else 4]}


def prompt_for_border_options():
    thickness_str = _ask_text(
        "Enter border thickness (0-500)",
        default_val=10,
        validate=_validate_number(0, 500, allow_empty=True),
    )

    color_str = _ask_text("Enter border color (Name or Hex)", default_val="black")

    position = questionary.select(
        "Border Position:", choices=["Expand", "Inside"]
    ).ask()

    return {
        "dest": "border",
        "values": [
            int(thickness_str) if thickness_str else 10,
            color_str if color_str else "black",
            position.lower(),
        ],
    }


def prompt_for_rotation_options():
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
    {"dest": "rotate", "name": "Rotate Image", "handler": prompt_for_rotation_options},
]

# --- Menu Logic ---


def remove_manipulation(operations, extra_args):
    if not operations:
        print("\nThere are no operations to remove.")
        return operations

    choices = [
        questionary.Choice(title=_format_operation_display(i, op, extra_args), value=i)
        for i, op in enumerate(operations)
    ]
    choices.append(questionary.Choice(title="Cancel", value=-1))

    choice_idx = questionary.select(
        "Select operation to remove:", choices=choices
    ).ask()

    if choice_idx == -1 or choice_idx is None:
        return operations

    removed_op = operations.pop(choice_idx)
    print(f"\nRemoved '{removed_op['dest']}'.")

    # Cleanup extra args logic
    if removed_op["dest"] == "scale" and not any(
        op["dest"] == "scale" for op in operations
    ):
        extra_args.pop("resample", None)

    has_kovalevsky = any(
        op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky"
        for op in operations
    )
    if not has_kovalevsky:
        extra_args.pop("threshold", None)

    return operations


def select_images():
    image_dir = "Base Images"
    if not os.path.isdir(image_dir):
        print(f"Error: Directory '{image_dir}' not found.")
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
        print(f"Read error: {e}")
        return []

    if not image_files:
        print(f"No images found in '{image_dir}'.")
        return []

    selected = questionary.checkbox(
        "Select images to process (Space to select, Enter to confirm):",
        choices=image_files,
    ).ask()

    if not selected:
        confirm = questionary.confirm(
            "No images selected. Continue anyway?", default=False
        ).ask()
        if not confirm:
            # Maybe allow re-selection? Or just return empty
            return []

    return [os.path.join(image_dir, f) for f in selected]


def select_manipulations():
    selected_operations = []
    extra_args = {}

    while True:
        # Build main menu based on current state
        choices = []

        # Action Groups
        choices.append(questionary.Separator(line="--- Actions ---"))
        choices.append(questionary.Choice("Run Processing", value="PROCESS"))
        if selected_operations:
            choices.append(questionary.Choice("Remove an Operation", value="REMOVE"))

        choices.append(questionary.Separator(line="--- Add Operation ---"))
        for i, manip in enumerate(AVAILABLE_MANIPULATIONS):
            choices.append(questionary.Choice(manip["name"], value=i))

        # Show current ops summary
        print("\nCurrent Pipeline:")
        if not selected_operations:
            print("  (Empty)")
        else:
            for i, op in enumerate(selected_operations):
                print(f"  {_format_operation_display(i, op, extra_args)}")
        print("")

        selection = questionary.select(
            "What would you like to do?", choices=choices
        ).ask()

        if selection is None:  # C-c
            break

        if selection == "PROCESS":
            if not selected_operations:
                confirm = questionary.confirm(
                    "Pipeline is empty. Process anyway?", default=False
                ).ask()
                if not confirm:
                    continue
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
                sig = inspect.signature(handler)
                if "extra_args" in sig.parameters:
                    op_details = handler(extra_args)
                else:
                    op_details = handler()
            else:
                op_details = {"dest": manip["dest"], "values": []}

            if op_details:
                selected_operations.append(op_details)
                print(f"Added '{manip['name']}'.")

    return selected_operations, extra_args


def interactive_menu():
    try:
        print("--- Welcome to the Interactive Image Processor ---")
        paths = select_images()
        if not paths:
            print("No images selected. Exiting.")
            return

        ops, extra_args = select_manipulations()

        # Prepare args
        mock_args = SimpleNamespace(
            resample=extra_args.get("resample", "bilinear"),
            threshold=extra_args.get("threshold", 50),
        )

        print(f"\nProcessing {len(paths)} images...")
        images_data = []
        for p in paths:
            with Image.open(p) as img:
                img.load()
                images_data.append([os.path.basename(p), img.copy()])

        process_images_and_save(images_data, ops, mock_args)
        print("\n--- Processing Complete ---")

    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"Error: {e}")
