import os
import inspect
from types import SimpleNamespace
from PIL import Image
from processing import process_images_and_save

# --- Submenu Functions for Manipulation Options ---

def _prompt_for_int_value(prompt, default, min_val, max_val):
    while True:
        val_str = input(f"{prompt} (default: {default}): ").strip()
        if not val_str: return default
        try:
            val = int(val_str)
            if min_val <= val <= max_val: return val
            else: print(f"Error: Value must be between {min_val} and {max_val}.")
        except ValueError: print("Error: Please enter a valid integer.")

def prompt_for_flip_options():
    print("\n--- Flip Options ---")
    choices = ['horizontal', 'vertical', 'both']
    for i, choice in enumerate(choices): print(f"  {i+1}. {choice.capitalize()}")
    while True:
        choice_str = input(f"Select flip direction (default: 1. {choices[0].capitalize()}): ").strip()
        if not choice_str: return {'dest': 'flip', 'values': [choices[0]]}
        try:
            choice_num = int(choice_str) - 1
            if 0 <= choice_num < len(choices): return {'dest': 'flip', 'values': [choices[choice_num]]}
            else: print(f"Invalid number. Choose between 1 and {len(choices)}.")
        except ValueError: print("Invalid input. Please enter a number.")

def prompt_for_scale_options(extra_args):
    print("\n--- Scale Options ---")
    print("Enter scale factor (e.g., '1.5x') OR new dimensions (e.g., '400px 300px').")
    while True:
        values_str = input("Enter scale value: ").strip().lower()
        if not values_str:
            print("Error: Scale value cannot be empty."); continue
        parts = values_str.split()
        if (len(parts) == 1 and parts[0].endswith('x')) or \
           (len(parts) == 2 and all(p.endswith('px') for p in parts)): break
        print("Invalid format. Use '1.5x' or '400px 300px'.")
    resample_choices = ['nearest', 'bilinear', 'bicubic', 'lanczos']
    default_resample = 'bilinear'
    print("\n--- Resample Filter ---")
    for i, choice in enumerate(resample_choices): print(f"  {i+1}. {choice.capitalize()}")
    while True:
        resample_str = input(f"Select resample filter (default: {default_resample}): ").strip()
        if not resample_str: extra_args['resample'] = default_resample; break
        try:
            choice_num = int(resample_str) - 1
            if 0 <= choice_num < len(resample_choices): extra_args['resample'] = resample_choices[choice_num]; break
            else: print(f"Invalid number. Choose between 1 and {len(resample_choices)}.")
        except ValueError: print("Invalid input. Please enter a number.")
    return {'dest': 'scale', 'values': values_str.split()}

def prompt_for_edge_detection_options(extra_args):
    print("\n--- Edge Detection Options ---")
    methods = ['sobel', 'canny', 'kovalevsky']
    for i, method in enumerate(methods): print(f"  {i+1}. {method.capitalize()}")
    while True:
        method_str = input(f"Select method (default: {methods[0]}): ").strip()
        if not method_str: chosen_method = methods[0]; break
        try:
            choice_num = int(method_str) - 1
            if 0 <= choice_num < len(methods): chosen_method = methods[choice_num]; break
            else: print(f"Invalid number. Choose between 1 and {len(methods)}.")
        except ValueError: print("Invalid input. Please enter a number.")
    if chosen_method == 'kovalevsky':
        print("\n--- Kovalevsky Threshold ---")
        default_threshold = 50
        threshold = _prompt_for_int_value("Enter threshold value (0-255)", default_threshold, 0, 255)
        extra_args['threshold'] = threshold
    return {'dest': 'edge_detection', 'values': [chosen_method]}

def prompt_for_brightness_options():
    val = _prompt_for_int_value("Enter brightness value (-100 to 100)", 0, -100, 100)
    return {'dest': 'brightness', 'values': [val]}
def prompt_for_contrast_options():
    val = _prompt_for_int_value("Enter contrast value (-100 to 100)", 0, -100, 100)
    return {'dest': 'contrast', 'values': [val]}
def prompt_for_saturation_options():
    val = _prompt_for_int_value("Enter saturation value (-100 to 100)", 0, -100, 100)
    return {'dest': 'saturation', 'values': [val]}

# --- Main Menu Logic ---

AVAILABLE_MANIPULATIONS = [
    {'dest': 'flip', 'name': 'Flip Image', 'handler': 'prompt_for_flip_options'},
    {'dest': 'scale', 'name': 'Scale Image', 'handler': 'prompt_for_scale_options'},
    {'dest': 'remove_background', 'name': 'Remove Background', 'handler': None},
    {'dest': 'invert', 'name': 'Invert Colors', 'handler': None},
    {'dest': 'grayscale', 'name': 'Convert to Grayscale', 'handler': None},
    {'dest': 'edge_detection', 'name': 'Apply Edge Detection', 'handler': 'prompt_for_edge_detection_options'},
    {'dest': 'brightness', 'name': 'Adjust Brightness', 'handler': 'prompt_for_brightness_options'},
    {'dest': 'contrast', 'name': 'Adjust Contrast', 'handler': 'prompt_for_contrast_options'},
    {'dest': 'saturation', 'name': 'Adjust Saturation', 'handler': 'prompt_for_saturation_options'},
]

def remove_manipulation(operations, extra_args):
    if not operations:
        print("\nThere are no operations to remove.")
        return operations
    print("\n--- Remove an Operation ---")
    for i, op in enumerate(operations):
        op_name = op['dest'].replace('_', '-')
        op_values = ' '.join(map(str, op.get('values', [])))
        display_string = f"--{op_name}"
        if op_values: display_string += f" {op_values}"
        # This part doesn't need to show extra args, it's just for identification
        print(f"  {i+1}. {display_string}")
    print("---------------------------")
    while True:
        choice_str = input("Select an operation number to remove (or press Enter to cancel): ").strip()
        if not choice_str: return operations
        try:
            choice_num = int(choice_str) - 1
            if 0 <= choice_num < len(operations):
                removed_op = operations.pop(choice_num)
                print(f"\nRemoved '{removed_op['dest']}'.")
                # Clean up extra_args if the removed op was the only one using it
                if removed_op['dest'] == 'scale' and not any(op['dest'] == 'scale' for op in operations):
                    extra_args.pop('resample', None)
                if removed_op['dest'] == 'edge_detection' and not any(op['dest'] == 'edge_detection' and op['values'][0] == 'kovalevsky' for op in operations):
                    extra_args.pop('threshold', None)
                return operations
            else: print(f"Invalid number. Choose between 1 and {len(operations)}.")
        except ValueError: print("Invalid input. Please enter a number.")

def select_images():
    image_dir = 'Base Images'
    if not os.path.isdir(image_dir):
        print(f"Error: Directory '{image_dir}' not found.")
        return []
    try:
        image_files = sorted([f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'))])
    except Exception as e:
        print(f"An error occurred while reading the directory: {e}")
        return []
    if not image_files:
        print(f"No images found in the '{image_dir}' directory.")
        return []
    selected_indices = set()
    while True:
        print("\n--- Select Images ---")
        for i, filename in enumerate(image_files):
            marker = "[x]" if i in selected_indices else "[ ]"
            print(f"{marker} {i+1: >2}. {filename}")
        print("---------------------")
        try:
            choice = input("Type number to toggle, or press Enter to confirm selection: ")
            if not choice:
                if not selected_indices:
                    print("\nWarning: No images were selected.")
                    if input("Continue without selecting images? (y/N): ").lower() != 'y':
                        continue
                break
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(image_files):
                if choice_num in selected_indices: selected_indices.remove(choice_num)
                else: selected_indices.add(choice_num)
            else:
                print(f"\nInvalid number. Please enter a number between 1 and {len(image_files)}.")
                input("Press Enter to continue...")
        except ValueError:
            print("\nInvalid input. Please enter a number.")
            input("Press Enter to continue...")
    return [os.path.join(image_dir, image_files[i]) for i in sorted(list(selected_indices))]


def select_manipulations():
    selected_operations = []
    extra_args = {}
    while True:
        print("\n--- Select Manipulations ---")
        print("Current sequence of operations:")
        if not selected_operations: print("  (No operations added yet)")
        else:
            for i, op in enumerate(selected_operations):
                op_name = op['dest'].replace('_', '-')
                op_values = ' '.join(map(str, op.get('values', [])))
                display_string = f"--{op_name}"
                if op_values: display_string += f" {op_values}"
                if op['dest'] == 'scale' and 'resample' in extra_args: display_string += f" --resample {extra_args['resample']}"
                if op['dest'] == 'edge_detection' and op['values'] and op['values'][0] == 'kovalevsky' and 'threshold' in extra_args: display_string += f" --threshold {extra_args['threshold']}"
                print(f"  {i+1}. {display_string}")
        print("\nAvailable manipulations:")
        for i, manip in enumerate(AVAILABLE_MANIPULATIONS): print(f"  {i+1}. {manip['name']}")
        print("----------------------------")
        print("Enter a number to add a manipulation.\nEnter '-' to remove an operation.\nEnter 'd' when done to process the images.")
        print("----------------------------")
        choice = input("Your choice: ").lower().strip()
        if not choice: continue
        if choice == 'd':
            if not selected_operations and input("Process without any changes? (y/N): ").lower() != 'y': continue
            break
        if choice == '-':
            selected_operations = remove_manipulation(selected_operations, extra_args)
            input("Press Enter to continue...")
            continue
        try:
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(AVAILABLE_MANIPULATIONS):
                manip_to_add = AVAILABLE_MANIPULATIONS[choice_num]
                handler_name = manip_to_add.get('handler')
                op_details = None
                if handler_name:
                    handler_func = globals().get(handler_name)
                    if handler_func:
                        sig = inspect.signature(handler_func)
                        if 'extra_args' in sig.parameters: op_details = handler_func(extra_args)
                        else: op_details = handler_func()
                    else: print(f"Error: Handler function '{handler_name}' not found.")
                else: op_details = {'dest': manip_to_add['dest'], 'values': []}
                if op_details:
                    selected_operations.append(op_details)
                    print(f"\nSuccessfully added '{manip_to_add['name']}'.")
                else: print("\nOperation cancelled.")
                input("Press Enter to continue...")
            else:
                print(f"\nInvalid number. Please enter a number between 1 and {len(AVAILABLE_MANIPULATIONS)}.")
                input("Press Enter to continue...")
        except ValueError:
            print("\nInvalid input. Please enter a number, '-', or 'd'.")
            input("Press Enter to continue...")
    return selected_operations, extra_args

def interactive_menu():
    print("--- Welcome to the Interactive Image Processor ---")
    selected_image_paths = select_images()
    if not selected_image_paths:
        print("\nNo images to process. Exiting.")
        return
    operations, extra_args = select_manipulations()
    mock_args = SimpleNamespace(
        resample=extra_args.get('resample', 'bilinear'),
        threshold=extra_args.get('threshold', 50)
    )
    images_data = []
    print("\nLoading selected images...")
    try:
        for filepath in selected_image_paths:
            with Image.open(filepath) as input_image:
                input_image.load()
                filename = os.path.basename(filepath)
                images_data.append([filename, input_image.copy()])
        print("Images loaded successfully.")
    except Exception as e:
        print(f"\nError: Could not load one or more images. Details: {e}")
        return
    process_images_and_save(images_data, operations, mock_args)
    print("\n--- Processing Complete ---")
