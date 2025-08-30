import argparse
from file_management import *
from remove_background import *
from scale_image import *
from image_filters import *
import glob
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Process command line arguments.")
    parser.add_argument('file', type=str, nargs='?', default=None, help='the image file path')
    parser.add_argument('-bg', '--remove-background', action='store_true', help='remove image background')
    parser.add_argument('-s', '--scale', nargs='+', help='scale image by factor (e.g., 1.5x) or to fit within a bounding box (e.g., 400px 300px)')
    parser.add_argument('--resample', type=str, default='bilinear', choices=['nearest', 'bilinear', 'bicubic', 'lanczos'], help='resampling filter to use for scaling')
    parser.add_argument('-i', '--invert', action='store_true', help='inverts the colors of an image')
    parser.add_argument('-g', '--grayscale', action='store_true', help='converts an image to grayscale')
    args = parser.parse_args()

    # TODO: If no arguments are passed, switch to a menu

    if not args.remove_background and not args.scale and not args.invert and not args.grayscale:
        print('No actions specified. Exiting...')
        exit()

    # Move images to the Base Images directory
    move_images_to_subdirectory('Base Images')

    if not args.file or args.file == '*':  # For all files in "Base Images" directory
        images = []
        for root, dirs, files in os.walk('Base Images/'):
            for file in files:
                filepath = os.path.join(root, file)
                with Image.open(filepath) as input_image:
                    input_image.load()
                    images.append([file, input_image.copy()])
                # print([file, input_image])
    else:  # For specified file(s)
        try:
            images = []
            # Use glob to handle wildcards in the file path
            for filepath in glob.glob(args.file):
                with Image.open(filepath) as input_image:
                    input_image.load()
                    # Extract just the filename for display/saving purposes
                    filename = Path(filepath).name
                    images.append([filename, input_image.copy()])
        except Exception as e:
            # If no files are found or an error occurs, print an error and exit
            print(f'Error while loading file: {e}')
            exit()

    for image in images:
        output_image = image[1]

        # Execute selected commands
        if args.scale:
            scale_params = args.scale
            scale_factor = None
            new_size = None
            if len(scale_params) == 1 and scale_params[0].lower().endswith('x'):
                try:
                    scale_factor = float(scale_params[0][:-1])
                except ValueError:
                    print(f"Invalid scale factor: {scale_params[0]}")
                    continue
            elif len(scale_params) == 2:
                try:
                    width = int(scale_params[0].lower().replace('px', ''))
                    height = int(scale_params[1].lower().replace('px', ''))
                    new_size = (width, height)
                except ValueError:
                    print(f"Invalid size format: {scale_params}")
                    continue
            else:
                print("Invalid format for --scale argument. Use '1.5x' or '400px 300px'.")
                continue

            print(f'Scaling "{image[0]}"...')
            output_image = scale_image(output_image, scale_factor=scale_factor, new_size=new_size, resample_filter=args.resample)

        if args.remove_background:
            print(f'Removing background of "{image[0]}"...')
            output_image = remove_background(output_image)

        if args.invert:
            print(f'Inverting the colors of "{image[0]}"...')
            output_image = invert_colors(output_image)

        if args.grayscale:
            print(f'Converting "{image[0]}" to grayscale...')
            output_image = grayscale(output_image)

        # Saves final output image
        if not os.path.exists('Output/'):
            os.makedirs('Output/')
        output_image.save("Output/.tmp.png")
        filename = Path(image[0]).stem
        os.replace("Output/.tmp.png", 'Output/' + filename + '.png')
        print("Image saved successfully:", 'Output/' + filename + '.png')

if __name__ == "__main__":
    main()
