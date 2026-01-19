import os
import shutil
import glob


def setup_test_images():
    # Determine paths relative to this script's location for robustness.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Assumes tests/ is in root

    source_dir = os.path.join(script_dir, "test_images")
    base_dir = os.path.join(project_root, "Base Images")

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
