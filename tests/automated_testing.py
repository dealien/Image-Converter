import subprocess
import sys
import os

def run_command(args):
    """Runs a single command with the current python executable."""
    cmd = [sys.executable, 'main.py'] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.getcwd())
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

def main():
    commands = [
        ['.\\tests\\test_images\\*', '--invert', '--flip', 'vertical', '--grayscale', '--invert'],
        ['.\\tests\\test_images\\*', '--brightness', '20', '--edge-detection', 'canny', '--flip', 'horizontal'],
        ['.\\tests\\test_images\\*', '--saturation', '-15', '--grayscale', '--invert'],
        ['.\\tests\\test_images\\*', '--remove-background'],
        ['.\\tests\\test_images\\*', '--scale', '0.5', '--resample', 'bicubic'],
        ['.\\tests\\test_images\\*', '--scale', '800px', '600px', '--resample', 'lanczos'],
        ['.\\tests\\test_images\\*', '--flip', 'both'],
        ['.\\tests\\test_images\\*', '--edge-detection', 'sobel'],
        ['.\\tests\\test_images\\*', '--contrast', '50'],
        ['.\\tests\\test_images\\*', '--color-balance', '1.2', '0.8', '0.8'],
        ['.\\tests\\test_images\\*', '--hue-rotation', '90'],
        ['.\\tests\\test_images\\*', '--posterize', '4'],
        ['.\\tests\\test_images\\*', '--blur', '10'],
        ['.\\tests\\test_images\\*', '--sharpen', '10'],
        ['.\\tests\\test_images\\*', '--border', '10', 'red', 'expand'],
        ['.\\tests\\test_images\\*', '--rotate', '90']
    ]

    print("Starting automated scenario...")
    for args in commands:
        run_command(args)
    print("Automated scenario completed successfully.")

if __name__ == "__main__":
    main()
