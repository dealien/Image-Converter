# Interactive Menu Usage

If you don't like remembering command line flags, you can start the script with no arguments (or `--menu`) to launch a fully interactive UI to build your processing pipeline!

```bash
image-converter
# or
image-converter --menu
```

## How to use the Interactive Menu

The interactive menu will guide you through the process of selecting images and building a pipeline of operations.

1. **Select Images**: First, you'll be prompted to select one or more images from your `Base Images` directory. You can use the arrow keys to navigate the list, Spacebar to toggle a selection, Enter to confirm your selections, or 'A' to toggle all images.
2. **Build Your Pipeline**: Once you've selected your images, you can begin adding operations to your pipeline. Select an operation category, then choose a specific action (e.g., "Scale Image", "Adjust Brightness"). You'll be prompted to enter the necessary parameters. The operations will be executed in the exact order you specify.
3. **Review and Process**: The interactive menu will show you a summary of your selected images, the current pipeline, and an equivalent CLI command that you can copy for future use. When you're ready, select **Run Processing** to execute the pipeline on your selected images.
4. **Remove Operations**: Made a mistake? You can select the **Remove an Operation** option to delete an existing step from your pipeline before running the process.
