import argparse
from file_management import *
from remove_background import *
import glob
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Process command line arguments.")
    parser.add_argument('file', type=str, nargs='?', default=None, help='the image file path')
    parser.add_argument('-bg', '--remove-background', action='store_true', help='remove image background')
    args = parser.parse_args()

    # TODO: If no arguments are passed, switch to a menu

    # Move images to the Base Images directory
    move_images_to_subdirectory('Base Images')

    # Parse arguments
    # print(args)
    # print(f"File: {args.file}")
    # print(f"Remove background: {args.remove_background}")

    if not args.file or args.file == '*':  # For all files in "Base Images" directory
        images = []
        for root, dirs, files in os.walk('Base Images/'):
            for file in files:
                input_image = Image.open('Base Images/' + file)
                images.append([file, input_image])
                # print([file, input_image])
    else:  # For specified file(s)
        try:
            images = []
            # Use glob to handle wildcards in the file path
            for filepath in glob.glob(args.file):
                input_image = Image.open(filepath)
                # Extract just the filename for display/saving purposes
                filename = Path(filepath).name
                images.append([filename, input_image])
        except Exception as e:
            # If no files are found or an error occurs, print an error and exit
            print(f'Error while loading file: {e}')
            exit()

    for image in images:
        # print(image)
        # Execute selected commands
        if args.remove_background:
            print(f'Removing background of "{image[0]}"...')
            output_image = remove_background(image[1])
        else:
            print('No actions specified. Exiting...')
            exit()

        # Saves final output image
        if not os.path.exists('Output/'):
            os.makedirs('Output/')
        output_image.save("Output/.tmp.png")
        filename = Path(image[0]).stem
        os.replace("Output/.tmp.png", 'Output/' + filename + '.png')
        print("Image saved successfully:", 'Output/' + filename + '.png')

if __name__ == "__main__":
    main()
