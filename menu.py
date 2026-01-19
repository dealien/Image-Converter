import os
import inspect
from types import SimpleNamespace
from PIL import Image
from processing import process_images_and_save


# --- Helper Functions ---


def _get_input(prompt, validator=None, default=None):
    """Generic input helper with validation and default value."""
    while True:
        prompt_text = f"{prompt}"
        if default is not None:
            # Check if default is an options index (int) or value
            prompt_text += f" (default: {default})"
        prompt_text += ": "

        user_input = input(prompt_text).strip()

        if not user_input:
            if default is not None:
                return default
            continue

        if validator:
            try:
                return validator(user_input)
            except (ValueError, TypeError) as e:
                print(f"Error: {e}")
        else:
            return user_input


def _validate_int(min_val=None, max_val=None):
    def validator(val_str):
        val = int(val_str)
        if min_val is not None and val < min_val:
            raise ValueError(f"Value must be between {min_val} and {max_val}.")
        if max_val is not None and val > max_val:
            raise ValueError(f"Value must be between {min_val} and {max_val}.")
        return val

    return validator


def _validate_float(min_val=None, max_val=None):
    def validator(val_str):
        val = float(val_str)
        if min_val is not None and val < min_val:
            raise ValueError(f"Value must be at least {min_val}.")
        if max_val is not None and val > max_val:
            raise ValueError(f"Value must be at most {max_val}.")
        return val

    return validator


def _prompt_for_int_value(prompt, default, min_val, max_val):
    return _get_input(prompt, _validate_int(min_val, max_val), default)


def _prompt_for_float_value(prompt, default, min_val=0.0):
    return _get_input(prompt, _validate_float(min_val=min_val), default)


def _get_menu_choice(options, default_index=0, title=None):
    if title:
        print(f"\n--- {title} ---")
    for i, option in enumerate(options):
        print(f"  {i + 1}. {option.capitalize()}")

    # We return the actual string option, but the default passed to _get_input should be the display-friendly 1-based index or the value?
    # The original code displayed "default: 1. Horizontal".
    # Let's simplify and just show the value or index.
    # Or just handle the default logic inside the validator wrapper.

    def choice_validator(val_str):
        try:
            idx = int(val_str) - 1
        except ValueError:
            raise ValueError("Please enter a number.")

        if 0 <= idx < len(options):
            return options[idx]
        raise ValueError(f"Choose between 1 and {len(options)}.")

    # We pass the resolved default object to _get_input? No, _get_input returns the raw input if empty.
    # We need to bridge the gap.
    # Actually, simpler:

    resp = _get_input(
        "Select option",
        choice_validator,
        default=options[default_index],  # If user hits enter, we want the option value
    )
    # Wait, if I pass options[default_index] as default, _get_input returns it.
    # But the prompt in _get_input will show "default: horizontal". That's fine.
    return resp


def _format_operation_display(index, op, extra_args):
    op_name = op["dest"].replace("_", "-")
    op_vals = " ".join(map(str, op.get("values", [])))
    display_string = f"  {index + 1}. --{op_name} {op_vals}"

    if op["dest"] == "scale" and "resample" in extra_args:
        display_string += f" --resample {extra_args['resample']}"

    if op["dest"] == "edge_detection" and op.get("values", [""])[0] == "kovalevsky":
        display_string += f" --threshold {extra_args.get('threshold', 50)}"

    return display_string


# --- Submenu Functions ---


def prompt_for_flip_options():
    choice = _get_menu_choice(
        ["horizontal", "vertical", "both"], default_index=0, title="Flip Options"
    )
    return {"dest": "flip", "values": [choice]}


def prompt_for_scale_options(extra_args):
    print("\n--- Scale Options ---")
    print("Enter scale factor (e.g., '1.5x') OR new dimensions (e.g., '400px 300px').")

    def scale_validator(val_str):
        val_str = val_str.lower()
        parts = val_str.split()
        if (
            len(parts) == 1 and parts[0].endswith("x") and not parts[0].endswith("px")
        ) or (len(parts) == 2 and all(p.endswith("px") for p in parts)):
            return parts
        raise ValueError("Invalid format. Use '1.5x' or '400px 300px'.")

    values = _get_input("Enter scale value", scale_validator)

    resample_choice = _get_menu_choice(
        ["nearest", "bilinear", "bicubic", "lanczos"],
        default_index=1,
        title="Resample Filter",
    )
    extra_args["resample"] = resample_choice

    return {"dest": "scale", "values": values}


def prompt_for_edge_detection_options(extra_args):
    method = _get_menu_choice(
        ["sobel", "canny", "kovalevsky"],
        default_index=0,
        title="Edge Detection Options",
    )

    if method == "kovalevsky":
        print("\n--- Kovalevsky Threshold ---")
        extra_args["threshold"] = _prompt_for_int_value(
            "Enter threshold value (0-255)", 50, 0, 255
        )

    return {"dest": "edge_detection", "values": [method]}


def prompt_for_brightness_options():
    val = _prompt_for_int_value("Enter brightness value (-100 to 100)", 0, -100, 100)
    return {"dest": "brightness", "values": [val]}


def prompt_for_contrast_options():
    val = _prompt_for_int_value("Enter contrast value (-100 to 100)", 0, -100, 100)
    return {"dest": "contrast", "values": [val]}


def prompt_for_saturation_options():
    val = _prompt_for_int_value("Enter saturation value (-100 to 100)", 0, -100, 100)
    return {"dest": "saturation", "values": [val]}


def prompt_for_blur_options():
    val = _prompt_for_float_value("Enter blur radius", 2.0, 0.0)
    return {"dest": "blur", "values": [val]}


def prompt_for_sharpen_options():
    val = _prompt_for_int_value("Enter sharpness intensity (0-100)", 50, 0, 100)
    return {"dest": "sharpen", "values": [val]}


def prompt_for_color_balance_options():
    print(
        "Enter multipliers for Red, Green, and Blue channels (e.g., 1.0 for no change)."
    )
    r = _prompt_for_float_value("Red factor", 1.0)
    g = _prompt_for_float_value("Green factor", 1.0)
    b = _prompt_for_float_value("Blue factor", 1.0)
    return {"dest": "color_balance", "values": [r, g, b]}


def prompt_for_hue_rotation_options():
    val = _prompt_for_int_value("Enter hue rotation degrees (0-360)", 90, 0, 360)
    return {"dest": "hue_rotation", "values": [val]}


def prompt_for_posterize_options():
    val = _prompt_for_int_value("Enter number of bits (1-8)", 4, 1, 8)
    return {"dest": "posterize", "values": [val]}


def prompt_for_border_options():
    thickness = _prompt_for_int_value("Enter border thickness", 10, 0, 500)

    # Simple input for color
    color_str = _get_input("Enter border color (Name or Hex)", default="black")

    position = _get_menu_choice(
        ["expand", "inside"], default_index=0, title="Border Position"
    )

    return {"dest": "border", "values": [thickness, color_str, position]}


def prompt_for_rotation_options():
    angle = _prompt_for_int_value(
        "Enter rotation angle (will clamp to nearest 90)", 90, -3600, 3600
    )
    return {"dest": "rotate", "values": [angle]}


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

    # Show current ops
    print("\n--- Remove an Operation ---")
    for i, op in enumerate(operations):
        print(_format_operation_display(i, op, extra_args))

    def removal_validator(val_str):
        idx = int(val_str) - 1
        if 0 <= idx < len(operations):
            return idx
        raise ValueError(f"Choose between 1 and {len(operations)}.")

    try:
        choice_idx = _get_input("Select operation number", removal_validator)
    except Exception:  # Handle cancellation logic if needed, but here simple input
        return operations

    removed_op = operations.pop(choice_idx)
    print(f"\nRemoved '{removed_op['dest']}'.")

    # Cleanup extra args logic
    if removed_op["dest"] == "scale" and not any(
        op["dest"] == "scale" for op in operations
    ):
        extra_args.pop("resample", None)
    if removed_op["dest"] == "edge_detection":
        # Check if any other op is using kovalevsky? Unlikely since we just popped it, but good to be safe if multiple
        pass  # Logic from original was specific to kovalevsky.
        # Original:
        # if removed_op["dest"] == "edge_detection" and not any(
        #           op["dest"] == "edge_detection" and op["values"][0] == "kovalevsky"
        #           for op in operations
        #       ):
        #           extra_args.pop("threshold", None)

        # Re-implementing original cleanup logic completely:

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

    selected_indices = set()

    while True:
        print("\n--- Select Images ---")
        for i, filename in enumerate(image_files):
            marker = "[x]" if i in selected_indices else "[ ]"
            print(f"{marker} {i + 1: >2}. {filename}")
        print("---------------------")

        choice = input("Type number to toggle, or Enter to confirm: ").strip()

        if not choice:
            if not selected_indices:
                if input("No images selected. Continue? (y/N): ").lower() != "y":
                    continue
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(image_files):
                if idx in selected_indices:
                    selected_indices.remove(idx)
                else:
                    selected_indices.add(idx)
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input.")

    return [
        os.path.join(image_dir, image_files[i]) for i in sorted(list(selected_indices))
    ]


def select_manipulations():
    selected_operations = []
    extra_args = {}

    def _action_add_manipulation(idx_str):
        try:
            idx = int(idx_str) - 1
            if 0 <= idx < len(AVAILABLE_MANIPULATIONS):
                manip = AVAILABLE_MANIPULATIONS[idx]
                handler = manip.get("handler")

                op_details = None
                if handler:
                    # Check signature to see if it needs extra_args
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
            else:
                print("Invalid selection number.")
        except ValueError:
            print("Invalid input.")

    def _action_remove(arg=None):  # arg for compatibility
        remove_manipulation(selected_operations, extra_args)

    def _action_done(arg=None):
        return "DONE"  # Signal to break loop

    # Dictionary dispatch for non-numeric commands
    command_dispatch = {"-": _action_remove, "d": _action_done}

    while True:
        print("\n--- Select Manipulations ---")
        if not selected_operations:
            print("  (No operations added yet)")
        else:
            for i, op in enumerate(selected_operations):
                print(_format_operation_display(i, op, extra_args))

        print("\nAvailable:")
        for i, m in enumerate(AVAILABLE_MANIPULATIONS):
            print(f"  {i + 1}. {m['name']}")

        print("----------------------------")
        print("Enter number to add, '-' to remove, 'd' to process.")

        choice = input("Your choice: ").strip().lower()
        if not choice:
            continue

        if choice in command_dispatch:
            result = command_dispatch[choice]()
            if result == "DONE":
                if (
                    not selected_operations
                    and input("Process empty? (y/N): ").lower() != "y"
                ):
                    continue
                break
        else:
            # Assume numeric for addition
            _action_add_manipulation(choice)

    return selected_operations, extra_args


def interactive_menu():
    try:
        print("--- Welcome to the Interactive Image Processor ---")
        paths = select_images()
        if not paths:
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
