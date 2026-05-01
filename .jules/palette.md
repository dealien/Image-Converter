## 2024-05-24 - Consistent UI Text Styling in Rich Consoles
**Learning:** Even when a project adopts a comprehensive terminal UI library like `rich`, straggling raw `print()` statements can easily break immersion and create an inconsistent user experience. In interactive CLI flows, unstyled text stands out poorly against styled elements (like panels or colored prompts).
**Action:** When auditing CLI applications for UX, explicitly search for raw `print()` statements and replace them with the adopted styling library's output methods (e.g., `console.print()` in Rich) with appropriate semantic markup (e.g., `[dim cyan]`, `[yellow]`) to ensure a unified visual design language.

## 2024-05-25 - Prevent Layout Breakage with Long Filenames
**Learning:** In terminal UIs using `rich` or `questionary` formatted strings, dynamic data like filenames can exceed expected column widths and completely break tabular alignments or wrap unpleasantly, making the UI look broken or amateurish.
**Action:** Always defensively slice or truncate dynamic string data intended for fixed-width CLI columns (e.g., using an ellipsis `…` for filenames > 30 characters) to ensure layout stability.

## 2024-05-25 - Improve Empty States with Actionable Guidance
**Learning:** Abruptly exiting a CLI tool when a default directory is empty (e.g., "No images found. Exiting.") leaves the user stranded without context on how to proceed, creating a dead-end experience.
**Action:** Replace abrupt exits in empty states with helpful, actionable guidance explaining exactly what the user needs to do next (e.g., "Please place some images (e.g., .jpg, .png) in this directory and try again.").

## 2024-05-19 - Add Ctrl+C Keyboard Shortcut Hint to Interactive Menus
**Learning:** Terminal users often don't know they can use Ctrl+C to safely exit an interactive prompt without causing errors or saving unwanted changes. Making this explicit reduces anxiety.
**Action:** When using `questionary` or similar CLI prompt libraries, always include `Ctrl+C to cancel` in the `instruction` string if the application handles `KeyboardInterrupt` gracefully.

## 2024-03-31 - Ctrl+C Cancel Handling in Interactive Terminal Menu
**Learning:** Terminal UIs using `questionary` return `None` when the user presses `Ctrl+C`. Simply `break`ing out of a selection loop on `None` can cause unintended side-effects if the parent caller continues execution assuming the selection phase simply ended normally (like proceeding to process an empty task queue).
**Action:** When `questionary.ask()` returns `None`, explicitly raise a `KeyboardInterrupt` to correctly signal to upstream callers that the entire operation is being aborted, matching the expected behavior of standard python CLI apps.

## 2025-04-01 - Added loading spinner during parallel metadata fetching in rich menu
**Learning:** During parallel metadata fetching of image files using `ThreadPoolExecutor` within the `run_image_selector` function, the UI could appear to hang for large images or large directories, offering a poor UX for the user.
**Action:** Always consider the UX impact of blocking IO-bound operations when starting interactive prompts. Wrap these operations in a visual loading indicator such as the `rich` `console.status` spinner, to signal to users that work is occurring in the background.

## 2025-04-06 - Explicit Instruction Strings for questionary.confirm
**Learning:** By default, `questionary.confirm` prompts do not display any keyboard shortcut instructions, leaving users unaware of options like `Ctrl+C` to cancel or `y/n` for explicit choices.
**Action:** Explicitly provide an `instruction` string constant (e.g., `(y/n, Enter to confirm, Ctrl+C to cancel)`) to all `questionary.confirm` calls to surface hidden interaction paths.

## 2024-04-23 - Full Keyboard Navigation Hints for Multi-Select Prompts
**Learning:** `questionary.checkbox` prompts support advanced keyboard shortcuts like 'A to toggle all' and standard arrow key navigation. If these aren't explicitly mentioned in the `instruction` string, users may rely solely on Space and Enter, leading to slower interaction when managing many items.
**Action:** Always include complete accessibility hints for multi-select prompts (e.g., `(Use arrow keys to navigate, Space to select, Enter to confirm, A to toggle all, Ctrl+C to cancel)`) to maximize feature discoverability and improve power-user efficiency.

## 2025-05-18 - Missing Keyboard Instructions in Prompt Toolkit Input
**Learning:** When migrating from `questionary.text().ask()` to custom `prompt_toolkit` implementations (like `_ask_text`) for advanced styling, default instruction texts are often lost. Users might not know they can use Ctrl+C to safely exit or Enter to accept default inputs without explicit guidance.
**Action:** When using `prompt_toolkit`'s `PromptSession` (e.g., in `_ask_text`), explicitly append a styled instruction string (e.g., `(Enter to confirm, Ctrl+C to cancel)`) to the formatted message buffer to maintain UX consistency and keyboard shortcut discoverability.
