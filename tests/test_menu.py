from unittest.mock import MagicMock, patch

import pytest
from prompt_toolkit.validation import ValidationError

from image_converter import menu
from image_converter.menu import _ask_text, prompt_for_scale_options, select_images

# --- Fixtures ---


@pytest.fixture
def mock_questionary():
    with patch("image_converter.menu.questionary") as q:
        # Defaults for common methods to return a valid chainable object
        q.select.return_value.ask.return_value = None
        q.text.return_value.ask.return_value = None  # Still used? No, verifying removal
        q.checkbox.return_value.ask.return_value = []
        q.confirm.return_value.ask.return_value = False
        yield q


@pytest.fixture
def mock_ask_text():
    with patch("image_converter.menu._ask_text") as m:
        m.return_value = None
        yield m


# --- Validator Tests ---


def test_validate_number():
    validator = menu._validate_number(min_val=0, max_val=10, value_type=int)

    # Valid
    assert validator("5") is True

    # Empty (default False)
    assert validator("") == "Value cannot be empty."

    # Empty (allow True)
    validator_empty = menu._validate_number(
        min_val=0, max_val=10, value_type=int, allow_empty=True
    )
    assert validator_empty("") is True

    # Type error
    assert validator("abc") == "Please enter a valid integer."

    # Out of bounds
    assert "at least 0" in validator("-1")
    assert "at most 10" in validator("11")


def test_validate_number_float():
    """Test number validation for floats including bounds and empty strings."""
    validator = menu._validate_number(
        min_val=0.0, max_val=10.0, value_type=float, allow_empty=True
    )
    assert validator("0.5") is True
    assert validator("") is True
    assert "at least 0.0" in validator("-0.1")
    assert "at most 10.0" in validator("10.1")

    # Type error for float
    assert validator("abc") == "Please enter a valid number."

    # Empty (allow False)
    validator_no_empty = menu._validate_number(
        min_val=0.0, max_val=10.0, value_type=float, allow_empty=False
    )
    assert validator_no_empty("") == "Value cannot be empty."


# --- Submenu Tests ---


def test_prompt_for_flip(mock_questionary):
    mock_questionary.select.return_value.ask.return_value = "Horizontal"
    res = menu.prompt_for_flip_options()
    assert res == {"dest": "flip", "values": ["horizontal"]}


def test_prompt_for_flip_cancel(mock_questionary):
    mock_questionary.select.return_value.ask.return_value = None
    assert menu.prompt_for_flip_options() is None


def test_prompt_for_scale(mock_questionary, mock_ask_text):
    # Mock text prompt for scale value
    mock_ask_text.return_value = "1.5x"
    # Mock select prompt for resample
    mock_questionary.select.return_value.ask.return_value = "Bicubic"

    extra = {}
    res = menu.prompt_for_scale_options(extra)

    assert res == {"dest": "scale", "values": ["1.5x"]}
    assert extra["resample"] == "bicubic"


def test_prompt_for_scale_cancel(mock_questionary, mock_ask_text):
    mock_ask_text.return_value = None
    res = menu.prompt_for_scale_options({})
    assert res is None


def test_prompt_for_scale_cancel_resample(mock_questionary, mock_ask_text):
    mock_ask_text.return_value = "1.5x"
    mock_questionary.select.return_value.ask.return_value = None
    res = menu.prompt_for_scale_options({})
    assert res is None


def test_prompt_for_edge_detection_kovalevsky(mock_questionary, mock_ask_text):
    # Select method
    mock_questionary.select.return_value.ask.return_value = "Kovalevsky"
    # Select threshold (default case)
    mock_ask_text.return_value = ""

    extra = {}
    res = menu.prompt_for_edge_detection_options(extra)

    assert res == {"dest": "edge_detection", "values": ["kovalevsky"]}
    assert extra["threshold"] == 50


def test_prompt_for_edge_detection_cancel_method(mock_questionary):
    mock_questionary.select.return_value.ask.return_value = None
    res = menu.prompt_for_edge_detection_options({})
    assert res is None


def test_prompt_for_border(mock_questionary, mock_ask_text):
    select_mock = mock_questionary.select.return_value.ask

    # Thickness (empty->default 10), Color (empty->default black)
    mock_ask_text.side_effect = ["", ""]
    select_mock.return_value = "Inside"

    res = menu.prompt_for_border_options()
    assert res == {"dest": "border", "values": [10, "black", "inside"]}


def test_prompt_for_border_cancel_position(mock_questionary, mock_ask_text):
    mock_ask_text.side_effect = ["15", "red"]
    mock_questionary.select.return_value.ask.return_value = None
    res = menu.prompt_for_border_options()
    assert res is None


# Since we switched to structured messages (list of tuples), strict string matching
# in call assertions (if we had them) would fail.
# But we are mocking return values mainly.
# Let's ensure prompts are called.


def test_prompt_for_brightness(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_brightness_options()
    # verify call args regarding default if we want, but mocking return value is simpler
    assert res["values"] == [0]


def test_prompt_for_contrast(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_contrast_options()
    assert res["values"] == [0]


def test_prompt_for_saturation(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_saturation_options()
    assert res["values"] == [0]


def test_prompt_for_blur(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_blur_options()
    assert res["values"] == [2.0]


def test_prompt_for_sharpen(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_sharpen_options()
    assert res["values"] == [50]


def test_prompt_for_color_balance(mock_ask_text):
    mock_ask_text.side_effect = [
        "",
        "0.5",
        "",
    ]  # r(def), g(0.5), b(def)
    res = menu.prompt_for_color_balance_options()
    assert res["values"] == [1.0, 0.5, 1.0]


def test_prompt_for_hue_rotation(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_hue_rotation_options()
    assert res["values"] == [90]


def test_prompt_for_posterize(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_posterize_options()
    assert res["values"] == [4]


def test_prompt_for_rotation(mock_ask_text):
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_rotation_options()
    assert res["values"] == [90]


# --- Main Logic Tests ---


@patch("image_converter.menu.run_image_selector")
@patch("image_converter.menu.os.listdir")
@patch("image_converter.menu.os.path.isdir")
@patch("image_converter.menu.os.path.isfile")
def test_select_images(mock_isfile, mock_isdir, mock_listdir, mock_run_image_selector):
    mock_isdir.return_value = True
    mock_listdir.return_value = ["img1.png", "img2.jpg"]
    mock_isfile.return_value = True

    # Select both
    mock_run_image_selector.return_value = ["img1.png", "img2.jpg"]

    paths = menu.select_images()
    assert len(paths) == 2
    assert paths[0].endswith("img1.png")


@patch("image_converter.menu.run_image_selector")
def test_select_images_none_selected_confirm_cancel(
    mock_run_image_selector, mock_questionary
):
    with (
        patch("image_converter.menu.os.path.isdir", return_value=True),
        patch("image_converter.menu.os.listdir", return_value=["i.png"]),
        patch("image_converter.menu.os.path.isfile", return_value=True),
    ):
        mock_run_image_selector.return_value = []  # None selected
        mock_questionary.confirm.return_value.ask.return_value = False  # Cancel

        paths = menu.select_images()
        assert paths == []


@patch("image_converter.menu.run_image_selector")
def test_select_images_ctrl_c(mock_run_image_selector):
    with (
        patch("image_converter.menu.os.path.isdir", return_value=True),
        patch("image_converter.menu.os.listdir", return_value=["i.png"]),
        patch("image_converter.menu.os.path.isfile", return_value=True),
    ):
        mock_run_image_selector.return_value = None  # Ctrl-C
        with pytest.raises(KeyboardInterrupt):
            menu.select_images()


def test_select_manipulations_process_empty_pipeline_cancel(mock_questionary):
    mock_questionary.select.return_value.ask.side_effect = ["PROCESS", "PROCESS"]
    mock_questionary.confirm.return_value.ask.side_effect = [False, True, False]
    ops, extra, out_formats, out_qualities = menu.select_manipulations([])
    assert ops == []


@patch("image_converter.menu._ask_text")
def test_select_manipulations_output_formats_and_flatten(
    mock_ask_text, mock_questionary
):
    mock_questionary.select.return_value.ask.side_effect = ["PROCESS"]
    mock_questionary.confirm.return_value.ask.return_value = True  # flattening
    mock_questionary.checkbox.return_value.ask.return_value = ["PNG", "JPEG"]

    mock_ask_text.side_effect = ["85", "red"]

    images_data = [{"name": "test.png", "dims": "10x10", "size": "1KB", "fmt": "PNG"}]
    with patch("image_converter.menu.render_combined_menu"):
        new_ops, extra, out_formats, out_qualities = menu.select_manipulations(
            images_data
        )

    assert new_ops == []
    assert out_formats == ["png", "jpeg"]
    assert out_qualities == [100, 85]
    assert extra["flatten"] == "red"


@patch("image_converter.menu.remove_manipulation")
def test_select_manipulations_remove(mock_remove_manipulation, mock_questionary):
    mock_questionary.select.return_value.ask.side_effect = ["REMOVE", "PROCESS"]
    mock_questionary.confirm.return_value.ask.side_effect = [
        True,
        False,
    ]  # empty pipeline confirm, then flatten confirm
    mock_questionary.checkbox.return_value.ask.return_value = None

    ops, extra, out_formats, out_qualities = menu.select_manipulations([])
    mock_remove_manipulation.assert_called_once()


def test_select_manipulations_no_handler(mock_questionary):
    no_handler_idx = next(
        i
        for i, m in enumerate(menu.AVAILABLE_MANIPULATIONS)
        if m.get("handler") is None
    )

    mock_questionary.select.return_value.ask.side_effect = [no_handler_idx, "PROCESS"]
    mock_questionary.confirm.return_value.ask.side_effect = [False]  # flatten confirm
    mock_questionary.checkbox.return_value.ask.return_value = None

    ops, extra, out_formats, out_qualities = menu.select_manipulations([])

    assert len(ops) == 1
    assert ops[0]["dest"] == menu.AVAILABLE_MANIPULATIONS[no_handler_idx]["dest"]


def test_select_manipulations_basic_flow(mock_questionary):
    # Flow:
    # 1. Select 'Add Flip' (index in AVAILABLE_MANIPULATIONS)
    #    - Call prompt_for_flip_options (simulated mock)
    # 2. Select 'PROCESS'

    # We need to mock the AVAILABLE_MANIPULATIONS handler return values
    # Or mock the questionary flow.

    # Let's find index of Flip
    flip_idx = next(
        i for i, m in enumerate(menu.AVAILABLE_MANIPULATIONS) if m["dest"] == "flip"
    )

    # Mock sequence for main loop select:
    # 1. Flip Index
    # 2. "PROCESS"
    mock_questionary.select.return_value.ask.side_effect = [flip_idx, "PROCESS"]

    # Mock flip handler
    # We patch the handler in the list to avoid complex mocking of prompts inside usage
    original_handler = menu.AVAILABLE_MANIPULATIONS[flip_idx]["handler"]
    mock_handler = MagicMock(return_value={"dest": "flip", "values": ["horizontal"]})
    menu.AVAILABLE_MANIPULATIONS[flip_idx]["handler"] = mock_handler

    try:
        ops, extra, out_formats, out_qualities = menu.select_manipulations([])
        assert len(ops) == 1
        assert ops[0]["dest"] == "flip"
    finally:
        # Restore
        menu.AVAILABLE_MANIPULATIONS[flip_idx]["handler"] = original_handler


def test_remove_manipulation_flow(mock_questionary):
    ops = [
        {"dest": "flip", "values": ["horizontal"]},
        {"dest": "scale", "values": ["2x"]},
    ]
    extra = {"resample": "bicubic"}

    # remove_manipulation calls select.
    # Choices will be objects, but return value is index.
    # Let's say we remove index 1 (scale)
    mock_questionary.select.return_value.ask.return_value = 1

    new_ops = menu.remove_manipulation(ops, extra)

    assert len(new_ops) == 1
    assert new_ops[0]["dest"] == "flip"
    assert "resample" not in extra  # Cleaned up


def test_remove_manipulation_kovalevsky_cleanup(mock_questionary):
    ops = [
        {"dest": "flip", "values": ["horizontal"]},
        {"dest": "edge_detection", "values": ["kovalevsky"]},
    ]
    extra = {"threshold": 50}

    # Remove flip, kovalevsky remains
    mock_questionary.select.return_value.ask.return_value = 0
    new_ops = menu.remove_manipulation(ops, extra)
    assert len(new_ops) == 1
    assert "threshold" in extra

    # Remove kovalevsky, threshold should be cleaned up
    mock_questionary.select.return_value.ask.return_value = 0
    new_ops = menu.remove_manipulation(new_ops, extra)
    assert len(new_ops) == 0
    assert "threshold" not in extra


def test_interactive_menu_flow(mock_questionary):
    with (
        patch(
            "image_converter.menu.select_images", return_value=["p/img.png"]
        ) as mock_sel_imgs,
        patch(
            "image_converter.menu.select_manipulations",
            return_value=([{"dest": "flip"}], {}, [], []),
        ) as mock_sel_manips,
        patch("image_converter.menu.process_images_and_save") as mock_process,
    ):
        menu.interactive_menu()

        mock_sel_imgs.assert_called_once()
        mock_sel_manips.assert_called_once()
        mock_process.assert_called_once()


@patch("image_converter.menu.select_images")
@patch("image_converter.menu.console.print")
def test_interactive_menu_empty_paths(mock_print, mock_select_images):
    mock_select_images.return_value = []

    menu.interactive_menu()

    mock_select_images.assert_called_once()
    mock_print.assert_any_call("[yellow]No images selected.[/]")
    mock_print.assert_any_call(
        "[dim white]Please run the command again and select at least one image to process.[/]"
    )


def test_prompt_for_vignette_options(mock_ask_text):
    """Verifies that the vignette prompt returns default intensity for empty input."""
    mock_ask_text.return_value = ""  # default
    res = menu.prompt_for_vignette_options()
    assert res == {"dest": "vignette", "values": [50]}


def test_prompt_for_vignette_options_custom(mock_ask_text):
    """Verifies that the vignette prompt returns correct integer for valid custom input."""
    mock_ask_text.return_value = "75"
    res = menu.prompt_for_vignette_options()
    assert res == {"dest": "vignette", "values": [75]}


def test_scale_validator(mock_questionary):

    validator = None

    def mock_ask_text(*args, **kwargs):
        nonlocal validator
        validator = kwargs.get("validate")
        return None

    with patch("image_converter.menu._ask_text", side_effect=mock_ask_text):
        prompt_for_scale_options({})

    assert validator is not None
    assert validator("") == "Scale value cannot be empty."
    assert validator("1.5") is True
    assert validator("1.5x") is True
    assert validator("400px 300px") is True

    assert "Invalid format" in validator("abc")
    assert "Invalid format" in validator("400 300")
    assert "Invalid format" in validator("400px")
    assert "Invalid format" in validator("400px 300")


def test_ask_text_helper():
    """Tests the _ask_text helper directly to verify formatted prompt behavior."""
    # Mock PromptSession and prompt
    mock_session_instance = MagicMock()
    mock_session_instance.prompt.return_value = "user_input"

    with (
        patch(
            "image_converter.menu.PromptSession", return_value=mock_session_instance
        ) as mock_session_class,
        patch("image_converter.menu.print_formatted_text") as mock_print,
        patch("image_converter.menu.get_app") as mock_get_app,
    ):
        # Test basic prompt without default or validation
        res = _ask_text("Test question")
        assert res == "user_input"
        mock_session_class.assert_called_once()
        mock_print.assert_called_once()

        # Test get_prompt_text callback behavior
        prompt_args = mock_session_instance.prompt.call_args
        get_prompt_text = prompt_args.args[0]

        # Mock buffer text
        mock_buffer = MagicMock()
        mock_buffer.text = "typing"
        mock_get_app.return_value.current_buffer = mock_buffer

        formatted_prompt = get_prompt_text()
        assert any(msg == "Test question" for style, msg in formatted_prompt)

        # Reset and test with default value and validation
        mock_session_instance.reset_mock()
        mock_print.reset_mock()

        # Validation that fails then succeeds
        def validate(text):
            return True if text == "valid" else "Invalid text"

        _ask_text("Test validation", default_val="default_ans", validate=validate)

        # Test validator behavior
        prompt_kwargs = mock_session_instance.prompt.call_args.kwargs
        validator = prompt_kwargs.get("validator")

        assert validator is not None

        doc_valid = MagicMock()
        doc_valid.text = "valid"
        validator.validate(doc_valid)  # Should not raise

        doc_invalid = MagicMock()
        doc_invalid.text = "invalid"
        doc_invalid.cursor_position = 7
        with pytest.raises(ValidationError, match="Invalid text"):
            validator.validate(doc_invalid)

        # Test empty result uses default
        mock_session_instance.prompt.return_value = ""
        res3 = _ask_text("Test default", default_val="default_ans")
        assert res3 == ""  # Result is empty string, but final display uses default


def test_ask_text_helper_get_prompt_text_exception():
    """Tests the _ask_text helper exception handling in get_prompt_text."""
    with (
        patch("image_converter.menu.PromptSession") as mock_session_class,
        patch("image_converter.menu.print_formatted_text"),
        patch("image_converter.menu.get_app", side_effect=Exception("mocked error")),
    ):
        mock_session_instance = MagicMock()
        mock_session_instance.prompt.return_value = "ans"
        mock_session_class.return_value = mock_session_instance

        _ask_text("Test", default_val="def")

        # Test get_prompt_text execution
        prompt_args = mock_session_instance.prompt.call_args
        get_prompt_text = prompt_args.args[0]

        formatted = get_prompt_text()
        assert len(formatted) > 0


def test_select_images_error_handling(mock_questionary):

    with (
        patch("os.path.isdir", return_value=False),
        patch("image_converter.menu.console.print") as mock_print,
    ):
        res = select_images()
        assert res == []
        mock_print.assert_any_call("[red]Error: Directory 'Base Images' not found.[/]")

    with (
        patch("os.path.isdir", return_value=True),
        patch("os.listdir", side_effect=Exception("mocked error")),
        patch("image_converter.menu.console.print") as mock_print,
    ):
        res = select_images()
        assert res == []
        mock_print.assert_called_with(
            "[red]Read error while accessing the directory.[/]"
        )


def test_select_images_no_images(mock_questionary):

    with (
        patch("os.path.isdir", return_value=True),
        patch("os.listdir", return_value=[]),
        patch("image_converter.menu.console.print") as mock_print,
    ):
        res = select_images()
        assert res == []
        mock_print.assert_any_call("\n[yellow]No images found in 'Base Images'.[/]")


def test_remove_manipulation_empty_ops():
    from image_converter.menu import remove_manipulation

    with patch("image_converter.menu.console.print") as mock_print:
        res = remove_manipulation([], {})
        assert res == []
        mock_print.assert_any_call("\n[yellow]There are no operations to remove.[/]")
        mock_print.assert_any_call(
            "[dim white]Please select some operations from the menu to build your pipeline first.[/]"
        )
        assert mock_print.call_count == 2


def test_remove_manipulation_cancel(mock_questionary):
    from image_converter.menu import remove_manipulation

    mock_questionary.select.return_value.ask.return_value = -1
    ops = [{"dest": "flip"}]
    res = remove_manipulation(ops, {})
    assert res == ops


@patch("image_converter.menu.select_images")
@patch("image_converter.menu.console.print")
def test_interactive_menu_keyboard_interrupt(mock_print, mock_select_images):
    """Verifies that interactive_menu handles KeyboardInterrupt gracefully."""
    mock_select_images.side_effect = KeyboardInterrupt()

    menu.interactive_menu()

    mock_print.assert_called_with("\n[yellow]Cancelled.[/]")


@patch("image_converter.menu.select_images")
@patch("image_converter.menu.console.print")
def test_interactive_menu_general_exception(mock_print, mock_select_images):
    """Verifies that interactive_menu handles a general Exception gracefully."""
    mock_select_images.side_effect = Exception("mocked error")

    menu.interactive_menu()

    mock_print.assert_called_with("[red]An unexpected error occurred.[/]")


def test_select_manipulations_cancel_selection(mock_questionary):
    """Verifies KeyboardInterrupt is raised when Ctrl-C is pressed during manipulation selection."""
    mock_questionary.select.return_value.ask.return_value = None
    with pytest.raises(KeyboardInterrupt):
        menu.select_manipulations([])


def test_select_manipulations_process_empty_pipeline_confirm_cancel(mock_questionary):
    """Verifies KeyboardInterrupt is raised when Ctrl-C is pressed during empty pipeline confirmation."""
    mock_questionary.select.return_value.ask.side_effect = ["PROCESS"]
    mock_questionary.confirm.return_value.ask.return_value = None
    with pytest.raises(KeyboardInterrupt):
        menu.select_manipulations([])


def test_select_manipulations_flatten_confirm_cancel(mock_questionary):
    """Verifies KeyboardInterrupt is raised when Ctrl-C is pressed during flatten confirmation."""
    mock_questionary.select.return_value.ask.side_effect = ["PROCESS"]
    mock_questionary.confirm.return_value.ask.side_effect = [True, None]
    with pytest.raises(KeyboardInterrupt):
        menu.select_manipulations([])


@patch("image_converter.menu.questionary.confirm")
@patch("image_converter.menu.questionary.checkbox")
@patch("image_converter.menu.os.path.isdir", return_value=True)
def test_select_images_no_images_reselect_cancel(
    mock_isdir, mock_checkbox, mock_confirm
):
    """Verifies KeyboardInterrupt is raised when Ctrl-C is pressed during re-select confirmation."""
    with (
        patch("image_converter.menu.os.listdir", return_value=["img1.png"]),
        patch("image_converter.menu.os.path.isfile", return_value=True),
        patch("image_converter.rich_menu.Image.open") as mock_open,
        patch("image_converter.menu.os.path.getsize", return_value=1024),
    ):
        mock_open.return_value.__enter__.return_value.size = (100, 100)
        mock_open.return_value.__enter__.return_value.format = "PNG"
        mock_checkbox.return_value.ask.return_value = []
        mock_confirm.return_value.ask.return_value = None
        with pytest.raises(KeyboardInterrupt):
            menu.select_images()


def test_select_manipulations_exit_selection(mock_questionary):
    """Verifies KeyboardInterrupt is raised when 'EXIT' is selected."""
    mock_questionary.select.return_value.ask.return_value = "EXIT"
    with pytest.raises(KeyboardInterrupt):
        menu.select_manipulations([])


@patch("image_converter.menu._ask_text")
def test_prompt_for_oil_painting_options_valid_input_returns_dict(mock_ask_text):
    """Verifies that providing valid input returns the correct operation dictionary."""
    mock_ask_text.return_value = "75"
    res = menu.prompt_for_oil_painting_options()
    assert res == {"dest": "oil_painting", "values": [75]}


@patch("image_converter.menu._ask_text")
def test_prompt_for_oil_painting_options_empty_input_returns_default(mock_ask_text):
    """Verifies that empty input returns the default value of 50."""
    mock_ask_text.return_value = ""
    res = menu.prompt_for_oil_painting_options()
    assert res == {"dest": "oil_painting", "values": [50]}


@patch("image_converter.menu._ask_text")
def test_prompt_for_cartoonify_options_valid_input_returns_dict(mock_ask_text):
    """Verifies that providing valid input returns the correct operation dictionary."""
    mock_ask_text.return_value = "80"
    res = menu.prompt_for_cartoonify_options()
    assert res == {"dest": "cartoonify", "values": [80]}


@patch("image_converter.menu._ask_text")
def test_prompt_for_cartoonify_options_empty_input_returns_default(mock_ask_text):
    """Verifies that empty input returns the default value of 50."""
    mock_ask_text.return_value = ""
    res = menu.prompt_for_cartoonify_options()
    assert res == {"dest": "cartoonify", "values": [50]}
