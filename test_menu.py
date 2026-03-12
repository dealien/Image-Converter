from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import ANSI

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.tree import Tree
from rich import box
from rich.console import Console

console = Console()

# Define the tree structure
interactive_items = [
    {"type": "category", "label": "⚡ Actions", "style": "bold bright_yellow"},
    {"type": "action", "label": "▶ Run Processing", "value": "PROCESS", "style": "bold bright_green"},
    {"type": "action", "label": "❌ Remove an Operation", "value": "REMOVE", "style": "bold bright_red"},
    
    {"type": "category", "label": "🎨 Color", "style": "bold bright_magenta"},
    {"type": "op", "label": "Convert to Grayscale", "value": "grayscale"},
    {"type": "op", "label": "Invert Colors", "value": "invert"},
    {"type": "op", "label": "Adjust Brightness", "value": "brightness"},
    
    {"type": "category", "label": "📐 Transform", "style": "bold bright_blue"},
    {"type": "op", "label": "Scale Image", "value": "scale"},
    {"type": "op", "label": "Flip Image", "value": "flip"},
]

# Only index the selectable items
selectable_indices = [i for i, item in enumerate(interactive_items) if item["type"] in ("action", "op")]

def run_test_menu():
    cursor_idx = 0
    
    bindings = KeyBindings()

    @bindings.add("up")
    def _(event):
        nonlocal cursor_idx
        cursor_idx = max(0, cursor_idx - 1)

    @bindings.add("down")
    def _(event):
        nonlocal cursor_idx
        cursor_idx = min(len(selectable_indices) - 1, cursor_idx + 1)

    @bindings.add("enter")
    @bindings.add("c-m")
    def _(event):
        actual_index = selectable_indices[cursor_idx]
        event.app.exit(result=interactive_items[actual_index]["value"])

    @bindings.add("c-c")
    def _(event):
        event.app.exit(result=None)

    def get_render_text():
        # Dummy Image Table
        img_table = Table(
            title="🖼️  Selected Images",
            box=box.MINIMAL_HEAVY_HEAD,
            title_style="bold bright_white",
            border_style="dim white",
            header_style="bold bright_cyan",
            title_justify="left",
            padding=(0, 1),
        )
        img_table.add_column("Filename", style="bright_white", min_width=20)
        img_table.add_row("test1.png")
        img_table.add_row("test2.png")

        # Build Interactive Tree
        ops_tree = Tree(
            "🛠️  [bold bright_white]Menu[/]", guide_style="dim white"
        )
        
        current_node = ops_tree
        actual_cursor_index = selectable_indices[cursor_idx]

        for i, item in enumerate(interactive_items):
            # Check if this item is selected
            is_cursor = (i == actual_cursor_index)
            
            label_text = item["label"]
            
            if is_cursor:
                # Wrap label with selection style
                rendered_label = Text(label_text, style="bold black on white")
            else:
                # Use default item style or just white
                rendered_label = Text(label_text, style=item.get("style", "bright_white"))

            if item["type"] == "category":
                current_node = ops_tree.add(rendered_label)
            else:
                current_node.add(rendered_label)

        tree_panel = Panel(
            ops_tree, border_style="dim white", box=box.ROUNDED, padding=(1, 2)
        )

        top_layout = Columns([img_table, tree_panel], align="left", expand=True)

        pipeline_panel = Panel(
            "  > python main.py [images] --flip",
            title="⚙️  Pipeline",
            title_align="left",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )

        with console.capture() as capture:
            console.print("✨ [bold cyan]Image Converter[/] | [italic white]Interactive Image Processor[/]\n")
            console.print(top_layout)
            console.print(pipeline_panel)
            console.print("\n[dim]Use Up/Down arrows to navigate, Enter to select, Ctrl-C to quit.[/]")

        return ANSI(capture.get())

    control = FormattedTextControl(get_render_text)
    window = Window(content=control)
    layout = Layout(window)
    
    app = Application(layout=layout, key_bindings=bindings, full_screen=False, erase_when_done=True)
    
    return app.run()

if __name__ == "__main__":
    result = run_test_menu()
    print("Selection:", result)
