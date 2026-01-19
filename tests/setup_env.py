import os
import shutil
import glob


def setup_test_images():
    # Define paths relative to the project root (assuming script runs from root)
    # If run from tests/, adjustments needed. We'll make it robust.

    # Check if we are in 'tests' dir or root
    cwd = os.getcwd()
    if os.path.basename(cwd) == "tests":
        source_dir = "test_images"
        base_dir = "../Base Images"
    else:
        source_dir = os.path.join("tests", "test_images")
        base_dir = "Base Images"

    print(f"Setting up images from '{source_dir}' to '{base_dir}'...")

    if os.path.exists(base_dir):
        if os.path.isfile(base_dir):
            print(f"Removing file '{base_dir}' to replace with directory.")
            os.remove(base_dir)
            os.makedirs(base_dir, exist_ok=True)
    else:
        os.makedirs(base_dir)
        print(f"Created directory: {base_dir}")

    # Copy files
    files = glob.glob(os.path.join(source_dir, "*"))
    if not files:
        print(f"Warning: No files found in {source_dir}")
        return

    for file_path in files:
        if os.path.isfile(file_path):
            try:
                shutil.copy(file_path, base_dir)
                print(f"Copied {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Failed to copy {file_path}: {e}")


if __name__ == "__main__":
    setup_test_images()
