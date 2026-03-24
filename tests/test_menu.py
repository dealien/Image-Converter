import pytest
from unittest.mock import patch, MagicMock
from image_converter import menu

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


def test_prompt_for_edge_detection_kovalevsky(mock_questionary, mock_ask_text):
    # Select method
    mock_questionary.select.return_value.ask.return_value = "Kovalevsky"
    # Select threshold (default case)
    mock_ask_text.return_value = ""

    extra = {}
    res = menu.prompt_for_edge_detection_options(extra)

    assert res == {"dest": "edge_detection", "values": ["kovalevsky"]}
    assert extra["threshold"] == 50


def test_prompt_for_border(mock_questionary, mock_ask_text):
    select_mock = mock_questionary.select.return_value.ask

    # Thickness (empty->default 10), Color (empty->default black)
    mock_ask_text.side_effect = ["", ""]
    select_mock.return_value = "Inside"

    res = menu.prompt_for_border_options()
    assert res == {"dest": "border", "values": [10, "black", "inside"]}


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
        ops, extra = menu.select_manipulations([])
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


def test_interactive_menu_flow(mock_questionary):
    with (
        patch(
            "image_converter.menu.select_images", return_value=["p/img.png"]
        ) as mock_sel_imgs,
        patch(
            "image_converter.menu.select_manipulations",
            return_value=([{"dest": "flip"}], {}),
        ) as mock_sel_manips,
        patch("image_converter.menu.process_images_and_save") as mock_process,
    ):
        menu.interactive_menu()

        mock_sel_imgs.assert_called_once()
        mock_sel_manips.assert_called_once()
        mock_process.assert_called_once()
