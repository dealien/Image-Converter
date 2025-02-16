import argparse
from file_management import *
from remove_background import *
from pathlib import Path

parser = argparse.ArgumentParser(description="Process command line arguments.")
parser.add_argument('file', type=str, nargs='?', default=None, help='the image file path')
parser.add_argument('-bg', '--remove-background', action='store_true', help='remove image background')
args = parser.parse_args()

# TODO: If no arguments are passed, switch to a menu
# TODO: File path accepts wildcards

# Move images to the Base Images directory
move_images_to_subdirectory('Base Images')

# Parse arguments
print(args)
print(f"File: {args.file}")
print(f"Remove background: {args.remove_background}")

if not args.file:
    print('No file specified. Exiting...')
    exit()
try:
    # TODO: If '*' passed, execute for every file
    input_image = Image.open(args.file)
except Exception as e:
    print(f'Error while loading file: {e}')
    exit()

# Execute selected commands
if args.remove_background:
    output_image = remove_background(input_image)
else:
    print('No actions specified. Exiting...')
    exit()

# Saves final output image
if not os.path.exists('Output/'):
    os.makedirs('Output/')
output_image.save("Output/.tmp.png")
filename = Path(args.file).stem
os.replace("Output/.tmp.png", 'Output/' + filename + '.png')
print("Image saved successfully:", 'Output/' + filename + '.png')
