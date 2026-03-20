"""Utilities for managing files and directories.

Provides functions to manage images, such as moving images from the
current directory to a designated subdirectory.
"""

import os
import shutil


# Example usages:
# move_images_to_subdirectory()  # Uses the default "images" subdirectory

# Or, to use a different subdirectory name:
# move_images_to_subdirectory("my_picture_folder")


def move_images_to_subdirectory(subdirectory_name: str):
    """Moves all image files from the current directory to a specified subdirectory.

    Typically used to move images into the 'Base Images' directory, which is the
    default search path for image processing operations.

    Args:
        subdirectory_name (str): The name of the subdirectory to create and move
            the images into.

    Raises:
        Exception: If an error occurs during directory creation or file moving.
    """

    try:
        # 1. Create the subdirectory if it doesn't exist
        if not os.path.exists(subdirectory_name):
            os.makedirs(
                subdirectory_name
            )  # Create with intermediate directories if needed

        # 2. Get a list of all files in the current directory
        files = os.listdir(".")  # "." represents the current directory

        # 3. Iterate through the files and move image files
        for filename in files:
            # Check if it's a file (and not a directory) - Important!
            if os.path.isfile(filename):
                # 4. Check if the file is an image (using common extensions)
                #   You can customize this list for other image types
                if filename.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp")
                ):
                    source_path = filename
                    destination_path = os.path.join(
                        subdirectory_name, filename
                    )  # Join for correct path
                    shutil.move(source_path, destination_path)  # Move the file
                    print(
                        f"Moved: {filename} to {subdirectory_name}"
                    )  # Informative message
                # else: # Optional: if you want to see which files were SKIPPED
                #    print(f"Skipped (not an image): {filename}")

    except Exception as e:  # Handle potential errors
        print(f"An error occurred: {e}")
