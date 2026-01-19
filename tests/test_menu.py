import pytest

from unittest.mock import patch, MagicMock
import menu

# --- Fixtures ---


@pytest.fixture
def mock_input():
    with patch("builtins.input") as p:
        yield p


@pytest.fixture
def suppress_print():
    with patch("builtins.print"):
        yield


# --- Helper Tests ---


class TestHelpers:
    def test_get_input_basic(self, mock_input):
        mock_input.side_effect = ["test_val"]
        assert menu._get_input("Prompt") == "test_val"

    def test_get_input_default(self, mock_input):
        mock_input.side_effect = [""]
        assert menu._get_input("Prompt", default="def") == "def"

    def test_get_input_validator_success(self, mock_input):
        mock_input.side_effect = ["123"]
        assert menu._get_input("Prompt", validator=int) == 123

    def test_get_input_validator_retry(self, mock_input, suppress_print):
        # First input 'abc' raises ValueError in int(), second '123' works
        mock_input.side_effect = ["abc", "123"]
        assert menu._get_input("Prompt", validator=int) == 123

    def test_validate_int(self):
        # Case 1: Both bounds
        validator_both = menu._validate_int(min_val=0, max_val=10)
        assert validator_both("5") == 5
        with pytest.raises(ValueError, match="between"):
            validator_both("11")

        # Case 2: Min only
        validator_min = menu._validate_int(min_val=10)
        assert validator_min("10") == 10
        assert validator_min("100") == 100
        with pytest.raises(ValueError, match="at least"):
            validator_min("9")

        # Case 3: Max only
        validator_max = menu._validate_int(max_val=10)
        assert validator_max("10") == 10
        assert validator_max("-100") == -100
        with pytest.raises(ValueError, match="at most"):
            validator_max("11")

    def test_validate_float(self):
        validator = menu._validate_float(min_val=1.0)
        assert validator("1.5") == 1.5
        with pytest.raises(ValueError):
            validator("0.9")

    def test_get_menu_choice(self, mock_input, suppress_print):
        options = ["opt1", "opt2", "opt3"]
        # input '2' -> index 1 -> 'opt2'
        mock_input.side_effect = ["2"]
        assert menu._get_menu_choice(options) == "opt2"

    def test_get_menu_choice_default(self, mock_input, suppress_print):
        options = ["opt1", "opt2"]
        # input '' -> default index 0 -> 'opt1'
        mock_input.side_effect = [""]
        assert menu._get_menu_choice(options, default_index=0) == "opt1"

    def test_get_menu_choice_invalid_then_valid(self, mock_input, suppress_print):
        options = ["a", "b"]
        # '3' (out of range), 'x' (nan), '2' (ok)
        mock_input.side_effect = ["3", "x", "2"]
        assert menu._get_menu_choice(options) == "b"


# --- Submenu Tests ---


class TestSubMenus:
    def test_prompt_for_flip(self, mock_input, suppress_print):
        mock_input.side_effect = ["1"]  # horizontal
        assert menu.prompt_for_flip_options() == {
            "dest": "flip",
            "values": ["horizontal"],
        }

    def test_prompt_for_scale(self, mock_input, suppress_print):
        # scale val, resample choice
        # 1.5x, default (bilinear)
        mock_input.side_effect = ["1.5x", ""]
        extra = {}
        res = menu.prompt_for_scale_options(extra)
        assert res == {"dest": "scale", "values": ["1.5x"]}
        assert extra["resample"] == "bilinear"

    def test_prompt_for_scale_invalid(self, mock_input, suppress_print):
        # invalid format, valid format, resample
        mock_input.side_effect = ["invalid", "1.5x", "1"]  # nearest
        extra = {}
        res = menu.prompt_for_scale_options(extra)
        assert res["values"] == ["1.5x"]
        assert extra["resample"] == "nearest"

    def test_prompt_for_edge_detection_kovalevsky(self, mock_input, suppress_print):
        # 3 (kovalevsky), threshold (20)
        mock_input.side_effect = ["3", "20"]
        extra = {}
        res = menu.prompt_for_edge_detection_options(extra)
        assert res["values"] == ["kovalevsky"]
        assert extra["threshold"] == 20

    def test_prompt_for_border(self, mock_input, suppress_print):
        # thickness, color, position
        mock_input.side_effect = ["5", "red", "2"]  # 5px, red, inside
        res = menu.prompt_for_border_options()
        assert res == {"dest": "border", "values": [5, "red", "inside"]}

    def test_prompt_for_scale_invalid_formats(self, mock_input, suppress_print):
        # Invalid inputs: 400px (single), 400 (no unit), 1.5 (no unit), abc
        # Followed by valid inputs to break loop: 1.5x
        # We test that it retries until valid
        mock_input.side_effect = ["400px", "400", "1.5", "abc", "1.5x", ""]
        extra = {}
        res = menu.prompt_for_scale_options(extra)
        assert res["values"] == ["1.5x"]

    def test_prompt_for_edge_detection_defaults(self, mock_input, suppress_print):
        mock_input.side_effect = [""]  # default (sobel)
        extra = {}
        res = menu.prompt_for_edge_detection_options(extra)
        assert res["values"] == ["sobel"]

    def test_prompt_for_brightness(self, mock_input, suppress_print):
        mock_input.side_effect = ["10"]
        assert menu.prompt_for_brightness_options() == {
            "dest": "brightness",
            "values": [10],
        }

    def test_prompt_for_contrast(self, mock_input, suppress_print):
        mock_input.side_effect = ["-10"]
        assert menu.prompt_for_contrast_options() == {
            "dest": "contrast",
            "values": [-10],
        }

    def test_prompt_for_saturation(self, mock_input, suppress_print):
        mock_input.side_effect = ["50"]
        assert menu.prompt_for_saturation_options() == {
            "dest": "saturation",
            "values": [50],
        }

    def test_prompt_for_blur(self, mock_input, suppress_print):
        mock_input.side_effect = ["1.5"]
        assert menu.prompt_for_blur_options() == {
            "dest": "blur",
            "values": [1.5],
        }

    def test_prompt_for_sharpen(self, mock_input, suppress_print):
        mock_input.side_effect = ["100"]
        assert menu.prompt_for_sharpen_options() == {
            "dest": "sharpen",
            "values": [100],
        }

    def test_prompt_for_color_balance(self, mock_input, suppress_print):
        mock_input.side_effect = ["0.9", "1.1", "1.0"]  # r, g, b
        assert menu.prompt_for_color_balance_options() == {
            "dest": "color_balance",
            "values": [0.9, 1.1, 1.0],
        }

    def test_prompt_for_hue_rotation(self, mock_input, suppress_print):
        mock_input.side_effect = ["180"]
        assert menu.prompt_for_hue_rotation_options() == {
            "dest": "hue_rotation",
            "values": [180],
        }

    def test_prompt_for_posterize(self, mock_input, suppress_print):
        mock_input.side_effect = ["2"]
        assert menu.prompt_for_posterize_options() == {
            "dest": "posterize",
            "values": [2],
        }

    def test_prompt_for_rotation(self, mock_input, suppress_print):
        mock_input.side_effect = ["90"]
        assert menu.prompt_for_rotation_options() == {
            "dest": "rotate",
            "values": [90],
        }


# --- Main Logic Tests ---


class TestAppLogic:
    @patch("menu.os.listdir")
    @patch("menu.os.path.isdir")
    @patch("menu.os.path.isfile")
    def test_select_images(
        self, mock_isfile, mock_isdir, mock_listdir, mock_input, suppress_print
    ):
        mock_isdir.return_value = True
        mock_listdir.return_value = ["img1.png", "img2.jpg", "ignore.txt"]
        mock_isfile.return_value = True

        # 1 (select img1), 2 (select img2), 1 (deselect img1), Enter (confirm)
        mock_input.side_effect = ["1", "2", "1", ""]

        paths = menu.select_images()
        # Expected: base/img2.jpg
        # Since 'ignore.txt' is filtered out, list is [img1.png, img2.jpg] (sorted)
        assert len(paths) == 1
        assert paths[0].endswith("img2.jpg")

    @patch("menu.os.path.isdir")
    def test_select_images_no_dir(self, mock_isdir, suppress_print):
        mock_isdir.return_value = False
        assert menu.select_images() == []

    def test_remove_manipulation(self, mock_input, suppress_print):
        ops = [{"dest": "flip", "values": ["h"]}, {"dest": "scale", "values": ["2x"]}]
        extra = {"resample": "bicubic"}

        # Select 2 (scale) to remove
        mock_input.side_effect = ["2"]

        ops = menu.remove_manipulation(ops, extra)
        assert len(ops) == 1
        assert ops[0]["dest"] == "flip"
        # Since scale removed, extra args cleaned?
        assert "resample" not in extra

    # IMPORTANT: Use the actual menu.AVAILABLE_MANIPULATIONS for integration style test
    # or patch it. Let's rely on the actual one to ensure keys correct.
    def test_select_manipulations_add_and_done(self, mock_input, suppress_print):
        # Find index of 'Flip'
        flip_idx = -1
        for i, m in enumerate(menu.AVAILABLE_MANIPULATIONS):
            if m["dest"] == "flip":
                flip_idx = i + 1
                break
        assert flip_idx != -1

        # Inputs:
        # str(flip_idx) -> Add Flip
        # '1' -> Submenu (Horizontal)
        # 'd' -> Done

        mock_input.side_effect = [str(flip_idx), "1", "d"]

        ops, extra = menu.select_manipulations()
        assert len(ops) == 1
        assert ops[0]["dest"] == "flip"
        assert ops[0]["values"] == ["horizontal"]

    def test_select_manipulations_add_invalid(self, mock_input, suppress_print):
        # Inputs:
        # '999' -> Invalid selection
        # 'abc' -> Invalid input
        # 'd' -> Done
        # 'y' -> Process empty
        mock_input.side_effect = ["999", "abc", "d", "y"]
        ops, extra = menu.select_manipulations()
        assert ops == []

    def test_select_manipulations_cancel_empty(self, mock_input, suppress_print):
        # 'd' -> Done
        # 'n' -> Don't process empty (continue)
        # 'd' -> Done
        # 'y' -> Process empty (exit)
        mock_input.side_effect = ["d", "n", "d", "y"]

        ops, extra = menu.select_manipulations()
        assert ops == []

    @patch("menu.select_images")
    @patch("menu.select_manipulations")
    @patch("menu.process_images_and_save")
    @patch("menu.Image.open")
    def test_interactive_menu_flow(
        self, mock_open, mock_process, mock_sel_manips, mock_sel_imgs, suppress_print
    ):
        # Setup
        mock_sel_imgs.return_value = ["path/to/img.png"]
        mock_sel_manips.return_value = ([{"dest": "flip"}], {"resample": "b"})

        # Mock Image Context Manager
        mock_img = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_img

        # Run
        menu.interactive_menu()

        # Assertions
        mock_sel_imgs.assert_called_once()
        mock_sel_manips.assert_called_once()
        mock_process.assert_called_once()
        args_passed = mock_process.call_args[0][2]
        assert args_passed.resample == "b"

    @patch("menu.select_images")
    def test_interactive_menu_cancel(self, mock_sel_imgs, suppress_print):
        mock_sel_imgs.return_value = []
        menu.interactive_menu()
        # Should return immediately
        mock_sel_imgs.assert_called_once()
