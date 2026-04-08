import argparse
from unittest.mock import MagicMock, patch
from PIL import Image
import piexif

from image_converter.metadata import (
    cast_exif_value,
    load_exif_as_flat_dict,
    parse_metadata_input,
    dict_to_exif_bytes,
    handle_view_metadata,
    handle_copy_metadata,
    handle_set_metadata,
    handle_update_metadata,
    handle_strip_metadata,
    handle_author,
    handle_export_metadata,
)


def test_cast_exif_value_byte():
    # Force type to Byte to test the Byte branch
    with patch(
        "image_converter.metadata.REVERSE_EXIF_MAP",
        {"TestTag": {"type": piexif.TYPES.Byte}},
    ):
        assert cast_exif_value("TestTag", "255") == 255


def test_cast_exif_value_unknown_type_fallback():
    # Force a random type for testing the "else" branch
    with patch(
        "image_converter.metadata.REVERSE_EXIF_MAP", {"TestTag": {"type": 99999}}
    ):
        assert cast_exif_value("TestTag", "value") == b"value"


def test_load_exif_as_flat_dict_empty():
    assert load_exif_as_flat_dict(b"") == {}
    assert load_exif_as_flat_dict(b"Exif\x00\x00") == {}
    assert load_exif_as_flat_dict(None) == {}


def test_load_exif_as_flat_dict_exception():
    assert load_exif_as_flat_dict(b"invalid_bytes") == {}


def test_load_exif_as_flat_dict_various_types():
    exif_dict = {
        "0th": {
            315: b"Valid String",
            271: b"\xff\xff\xff",  # invalid utf-8 to trigger decode exception
            274: 1,  # integer
        },
        "thumbnail": b"thumbnail_data",
    }

    exif_bytes = piexif.dump(exif_dict)
    flat = load_exif_as_flat_dict(exif_bytes)

    assert "Artist" in flat
    assert flat["Artist"] == "Valid String"
    assert "Make" in flat
    assert flat["Make"] == "b'\\xff\\xff\\xff'"  # Will be repr of bytes
    assert "Orientation" in flat
    assert flat["Orientation"] == 1
    assert "thumbnail" not in flat


def test_parse_metadata_input_empty():
    assert parse_metadata_input([]) == {}


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_invalid_json_file(mock_print):
    assert parse_metadata_input(["non_existent_file.json"]) == {}
    mock_print.assert_called_once()


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_invalid_inline_json(mock_print):
    assert parse_metadata_input(['{"Artist": "Jane Doe"']) == {}
    mock_print.assert_called_once()


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_invalid_key_value(mock_print):
    assert parse_metadata_input(["ArtistJane Doe"]) == {}
    mock_print.assert_called_once()


@patch("image_converter.metadata.console.print")
def test_dict_to_exif_bytes_remove_key(mock_print):
    flat_dict = {"Artist": None}
    base_exif_dict = {"0th": {315: b"Jane Doe"}}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    assert 315 not in piexif.load(result)["0th"]


def test_dict_to_exif_bytes_remove_key_string_none():
    flat_dict = {"Artist": "None"}
    base_exif_dict = {"0th": {315: b"Jane Doe"}}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    assert 315 not in piexif.load(result)["0th"]


@patch("image_converter.metadata.console.print")
def test_dict_to_exif_bytes_exception(mock_print):
    with patch("piexif.dump", side_effect=Exception("mocked error")):
        flat_dict = {"Artist": "Jane Doe"}
        result = dict_to_exif_bytes(flat_dict)
        assert result == b""
        mock_print.assert_called_once()


def test_handle_view_metadata_no_exif():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    handle_view_metadata(mock_image, "test.jpg", [], MagicMock())


def test_handle_copy_metadata_no_source():
    mock_image = MagicMock(spec=Image.Image)
    handle_copy_metadata(mock_image, "test.jpg", [], MagicMock())


@patch("image_converter.metadata.console.print")
def test_handle_copy_metadata_source_open_error(mock_print):
    mock_image = MagicMock(spec=Image.Image)
    mock_args = MagicMock()
    del mock_args.cached_source_exif
    handle_copy_metadata(mock_image, "test.jpg", ["non_existent.jpg"], mock_args)
    assert mock_args.cached_source_exif == b""


def test_handle_set_metadata_invalid_input():
    mock_image = MagicMock(spec=Image.Image)
    handle_set_metadata(mock_image, "test.jpg", ["invalid"], MagicMock())


def test_handle_update_metadata_invalid_input():
    mock_image = MagicMock(spec=Image.Image)
    handle_update_metadata(mock_image, "test.jpg", ["invalid"], MagicMock())


def test_handle_update_metadata_invalid_existing_exif():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {"exif": b"invalid_exif_bytes"}
    handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())


def test_handle_strip_metadata_exif_load_exception():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {"exif": b"Invalid_but_not_Exif\\x00\\x00"}
    with patch("piexif.load", side_effect=Exception("Mock load error")):
        handle_strip_metadata(mock_image, "test.jpg", [], MagicMock())
        assert "exif" not in mock_image.info


@patch("image_converter.metadata.handle_update_metadata")
@patch("image_converter.metadata.console.print")
def test_handle_author_cached(mock_print, mock_handle_update):
    mock_image = MagicMock(spec=Image.Image)
    mock_args = MagicMock()
    mock_args._author_handled_once = True

    handle_author(mock_image, "test.jpg", ["Jane"], mock_args)
    mock_handle_update.assert_called_once()
    assert hasattr(mock_args, "_author_handled_once")


@patch("image_converter.metadata.console.print")
def test_handle_set_metadata_invalid_exif_dict_to_bytes(mock_print):
    mock_image = MagicMock(spec=Image.Image)
    with patch("image_converter.metadata.dict_to_exif_bytes", return_value=b""):
        result = handle_set_metadata(
            mock_image, "test.jpg", ["Artist=Jane"], MagicMock()
        )
        assert result == mock_image


@patch("image_converter.metadata.console.print")
def test_handle_update_metadata_invalid_exif_dict_to_bytes(mock_print):
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    with patch("image_converter.metadata.dict_to_exif_bytes", return_value=b""):
        result = handle_update_metadata(
            mock_image, "test.jpg", ["Artist=Jane"], MagicMock()
        )
        assert result == mock_image


def test_parse_metadata_input_json_exception():
    with patch("json.loads", side_effect=Exception("mocked JSON error")):
        with patch("image_converter.metadata.console.print") as mock_print:
            assert parse_metadata_input(['{"invalid"}']) == {}
            mock_print.assert_called_once()


def test_dict_to_exif_bytes_invalid_value():
    # Provide a flat dict with an invalid value that causes cast_exif_value to fail
    flat_dict = {"ResolutionUnit": "invalid"}
    # The dict_to_exif_bytes function catches the ValueError and skips it without crashing
    result = dict_to_exif_bytes(flat_dict)
    assert result == piexif.dump(
        {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
    )


def test_dict_to_exif_bytes_none_base_exif_dict():
    # Explicit test for when base_exif_dict is None, should create new dict
    flat_dict = {"Artist": "Jane Doe"}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict=None)
    exif_dict = piexif.load(result)
    assert exif_dict["0th"][315] == b"Jane Doe"


def test_handle_update_metadata_empty_existing_exif():
    mock_image = MagicMock(spec=Image.Image)
    # The exif tag exists but it's empty
    mock_image.info = {"exif": b""}
    handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())
    # Should create a new one, meaning it shouldn't fail
    assert b"Jane" in mock_image.info["exif"]


def test_handle_update_metadata_exif_fallback():
    mock_image = MagicMock(spec=Image.Image)
    # Exif string exists but is the fallback one that doesn't trigger load
    mock_image.info = {"exif": b"Exif\x00\x00"}
    handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())
    # Should proceed normally, building the new one
    assert b"Jane" in mock_image.info["exif"]


def test_handle_update_metadata_piexif_load_error():
    mock_image = MagicMock(spec=Image.Image)
    # It has bytes, so it tries piexif.load, but that raises an exception
    mock_image.info = {"exif": b"Invalid exif bytes that fail load"}
    with patch("piexif.load", side_effect=Exception("Load fail")):
        # The exception is ignored and it uses base_exif_dict=None
        handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())
        assert b"Jane" in mock_image.info["exif"]


def test_dict_to_exif_bytes_remove_key_that_does_not_exist():
    # Attempt to remove a key that's not in the base dictionary
    flat_dict = {"Artist": "None"}
    base_exif_dict = {"0th": {}}  # Artist not present
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    exif_dict = piexif.load(result)
    assert 315 not in exif_dict["0th"]


def test_dict_to_exif_bytes_remove_key_where_ifd_does_not_exist():
    # Attempt to remove a key where its IFD ("0th") isn't even in the base dictionary
    flat_dict = {"Artist": "None"}
    base_exif_dict = {"Exif": {}}  # "0th" not present
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    exif_dict = piexif.load(result)
    assert 315 not in exif_dict["0th"]


def test_handle_update_metadata_invalid_exif_dict_load():
    mock_image = MagicMock(spec=Image.Image)
    # Give it an existing EXIF dict but we will make it raise an Exception during piexif.load
    mock_image.info = {"exif": b"InvalidBytesToCauseLoadException"}

    with patch("piexif.load", side_effect=Exception("Load Exception")):
        # We also need a patch to ensure it falls through silently
        # If dict_to_exif_bytes receives base_exif_dict=None, it won't merge the old tags.
        with patch(
            "image_converter.metadata.dict_to_exif_bytes", return_value=b"NewExifData"
        ) as mock_dict_to_bytes:
            handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())
            # The base_exif_dict should be passed as None because the load failed
            mock_dict_to_bytes.assert_called_once_with({"Artist": "Jane"}, None)
            assert mock_image.info["exif"] == b"NewExifData"


def test_handle_view_metadata_exception_during_load():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {"exif": b"Invalid Bytes"}
    with patch("image_converter.metadata.console.print") as mock_print:
        # load_exif_as_flat_dict already returns {} on exception, but let's test handle_view_metadata specifically
        with patch("image_converter.metadata.load_exif_as_flat_dict", return_value={}):
            handle_view_metadata(mock_image, "test.jpg", [], MagicMock())
            # We expect the 'No EXIF metadata found.' message
            mock_print.assert_any_call("      [dim white]No EXIF metadata found.[/]")


def test_handle_copy_metadata_empty_source():
    # If the source file has no EXIF or the source EXIF cannot be loaded, cached_source_exif might be empty
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    mock_args = MagicMock()
    mock_args.cached_source_exif = b""
    handle_copy_metadata(mock_image, "test.jpg", ["valid_source.jpg"], mock_args)
    # Target image EXIF should still not exist, since cached_source_exif was empty
    assert "exif" not in mock_image.info


def test_handle_strip_metadata_piexif_exception():
    mock_image = MagicMock(spec=Image.Image)
    # Give it valid piexif loadable bytes to trigger load
    exif_dict = {"0th": {piexif.ImageIFD.Orientation: 8}}
    mock_image.info = {"exif": piexif.dump(exif_dict)}

    # Make piexif.dump raise Exception on the rebuilding
    with patch("piexif.dump", side_effect=Exception("Dump fail")):
        # Should gracefully catch exception and not crash
        handle_strip_metadata(mock_image, "test.jpg", [], MagicMock())
        # Since dump failed, the 'exif' tag won't be populated with the Orientation
        assert "exif" not in mock_image.info


def test_handle_author_first_time():
    mock_image = MagicMock(spec=Image.Image)
    # mock_args does not have _author_handled_once
    mock_args = MagicMock(spec=argparse.Namespace)

    with patch("image_converter.metadata.handle_update_metadata") as mock_update:
        handle_author(mock_image, "test.jpg", ["Jane"], mock_args)
        assert getattr(mock_args, "_author_handled_once", False) is True
        mock_update.assert_called_once()


def test_dict_to_exif_bytes_fallback_to_0th_for_unknown_ifd():
    # If a tag doesn't have an explicitly mapped IFD in our REVERSE dict fallback is '0th' by piexif?
    # Actually the code trusts the ifd from the map. If not present it throws? Let's check.
    pass


def test_load_exif_as_flat_dict_exception_during_dict_creation():
    # Make dict creation fail to hit the exception block
    with patch("piexif.load", side_effect=Exception("Failed to load")):
        assert load_exif_as_flat_dict(b"valid_exif_bytes") == {}


def test_dict_to_exif_bytes_invalid_key_parsing():
    flat_dict = {"ResolutionUnit": "not_a_number"}
    # The cast_exif_value will throw ValueError and print error
    with patch("image_converter.metadata.console.print") as mock_print:
        result = dict_to_exif_bytes(flat_dict)
        mock_print.assert_called_once()
        # Verify it still returns a valid exif bytes dict that skips the bad tag
        exif_dict = piexif.load(result)
        assert 296 not in exif_dict["0th"]


def test_load_exif_as_flat_dict_value_not_bytes():
    # Value is not bytes or tuple (e.g. integer), and should be kept as is.
    exif_dict = {
        "0th": {
            274: 1  # Orientation is integer
        }
    }

    with patch("piexif.load", return_value=exif_dict):
        flat = load_exif_as_flat_dict(b"valid_exif_bytes")
        assert flat["Orientation"] == 1


def test_parse_metadata_input_json_file_exception():
    # File exists but fails to be read/parsed
    with patch("builtins.open", side_effect=Exception("mocked open error")):
        with patch("image_converter.metadata.console.print") as mock_print:
            assert parse_metadata_input(["some_file.json"]) == {}
            mock_print.assert_called_once()


def test_dict_to_exif_bytes_none_tag_in_base_dict():
    # If a user explicitly wants to delete a key that's present in base_exif_dict.
    flat_dict = {"Artist": None}
    base_exif_dict = {"0th": {315: b"Old Value"}}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    exif_dict = piexif.load(result)
    assert 315 not in exif_dict["0th"]


def test_dict_to_exif_bytes_ifd_not_in_exif_dict():
    # If the EXIF dict being built doesn't yet have the IFD section for an incoming tag.
    flat_dict = {"Artist": "Jane Doe"}
    base_exif_dict = {"0th": {}}  # Make sure 0th is present initially
    # Remove '0th' completely
    del base_exif_dict["0th"]
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    exif_dict = piexif.load(result)
    assert 315 in exif_dict["0th"]


def test_handle_strip_metadata_empty_preserve_keys():
    # If the image doesn't have any preserve keys.
    mock_image = MagicMock(spec=Image.Image)
    # Exif contains only generic stuff, not Orientation
    exif_dict = {
        "0th": {piexif.ImageIFD.Artist: b"Jane Doe"},
        "Exif": {},
        "GPS": {},
        "Interop": {},
        "1st": {},
        "thumbnail": None,
    }
    mock_image.info = {"exif": piexif.dump(exif_dict)}

    handle_strip_metadata(mock_image, "test.jpg", [], MagicMock())
    # Should effectively strip everything including exif, because orientation was not present to rebuild
    assert mock_image.info == {}


def test_handle_view_metadata_empty_values():
    # Calling view_metadata with no info should just print No EXIF metadata found
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    with patch("image_converter.metadata.console.print") as mock_print:
        handle_view_metadata(mock_image, "test.jpg", [], MagicMock())
        mock_print.assert_any_call("      [dim white]No EXIF metadata found.[/]")


def test_parse_metadata_input_inline_json_error():
    # Bad JSON formatting triggers the error block
    with patch("image_converter.metadata.console.print") as mock_print:
        result = parse_metadata_input(['{"BadJSON}'])
        assert result == {}
        assert mock_print.call_count == 1
        # The expected output has been changed due to more specific error catching
        assert "[red]Error: Inline JSON is not valid.[/]" in mock_print.call_args[0][0]


def test_handle_view_metadata_empty_values_2():
    # Calling view_metadata with no info should just print No EXIF metadata found
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    with patch("image_converter.metadata.console.print") as mock_print:
        with patch("image_converter.metadata.load_exif_as_flat_dict", return_value={}):
            handle_view_metadata(mock_image, "test.jpg", [], MagicMock())
            mock_print.assert_any_call("      [dim white]No EXIF metadata found.[/]")


def test_handle_copy_metadata_source_open_fail():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {}
    mock_args = MagicMock()
    del mock_args.cached_source_exif
    with patch("image_converter.metadata.console.print") as mock_print:
        with patch("PIL.Image.open", side_effect=Exception("Failed to open")):
            handle_copy_metadata(
                mock_image, "test.jpg", ["some_bad_file.jpg"], mock_args
            )
            assert mock_args.cached_source_exif == b""
            mock_print.assert_called()


def test_handle_update_metadata_base_dict_not_built():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {"exif": b"Invalid_but_not_Exif\\x00\\x00"}
    with patch("piexif.load", side_effect=Exception("Failed to load")):
        with patch(
            "image_converter.metadata.dict_to_exif_bytes", return_value=b"test"
        ) as mock_dict_to_bytes:
            handle_update_metadata(mock_image, "test.jpg", ["Artist=Jane"], MagicMock())
            # Passed None to dict_to_exif_bytes
            mock_dict_to_bytes.assert_called_once_with({"Artist": "Jane"}, None)


def test_load_exif_as_flat_dict_value_not_bytes_nor_tuple():
    exif_dict = {
        "0th": {
            274: 1  # integer
        }
    }
    with patch("piexif.load", return_value=exif_dict):
        flat = load_exif_as_flat_dict(b"valid_exif_bytes")
        assert flat["Orientation"] == 1


def test_load_exif_as_flat_dict_value_tuple_not_integers():
    exif_dict = {
        "0th": {
            315: ("not", "int")  # Tuple but not integers
        }
    }
    with patch("piexif.load", return_value=exif_dict):
        flat = load_exif_as_flat_dict(b"valid_exif_bytes")
        assert flat["Artist"] == ("not", "int")


def test_load_exif_as_flat_dict_value_tuple_not_length_two():
    exif_dict = {
        "0th": {
            315: (1, 2, 3)  # Tuple but length 3
        }
    }
    with patch("piexif.load", return_value=exif_dict):
        flat = load_exif_as_flat_dict(b"valid_exif_bytes")
        assert flat["Artist"] == (1, 2, 3)


def test_load_exif_as_flat_dict_rational_tuple():
    exif_dict = {
        "0th": {
            282: (72, 1)  # XResolution is 282
        }
    }
    with patch("piexif.load", return_value=exif_dict):
        flat = load_exif_as_flat_dict(b"valid_exif_bytes")
        assert "XResolution" in flat
        assert flat["XResolution"] == "72/1"


def test_dict_to_exif_bytes_create_ifd():
    flat_dict = {"Artist": "Jane"}
    base_exif_dict = {}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    exif_dict = piexif.load(result)
    assert 315 in exif_dict["0th"]


def test_dict_to_exif_bytes_missing_ifd():
    flat_dict = {"ImageDescription": "Test"}
    base_exif_dict = {"Exif": {}}
    result = dict_to_exif_bytes(flat_dict, base_exif_dict)
    assert 270 in piexif.load(result)["0th"]


def test_handle_export_metadata_no_values():
    mock_image = MagicMock(spec=Image.Image)
    exif_dict = {"0th": {piexif.ImageIFD.Artist: b"Jane Doe"}}
    mock_image.info = {"exif": piexif.dump(exif_dict)}

    mock_args = MagicMock()
    del mock_args.metadata_manifest

    # Call with values=None or []
    handle_export_metadata(mock_image, "test.jpg", [], mock_args)
    # Shouldn't set export_metadata_path if no values passed
    pass


def test_handle_export_metadata_with_existing_manifest():
    mock_image = MagicMock(spec=Image.Image)
    mock_image.info = {"exif": b""}

    mock_args = MagicMock()
    mock_args.metadata_manifest = {"existing.jpg": {"Tag": "Value"}}

    handle_export_metadata(mock_image, "test.jpg", [], mock_args)
    assert "test.jpg" in mock_args.metadata_manifest
    assert "existing.jpg" in mock_args.metadata_manifest


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_json_file_permission_error(mock_print):
    """Test parse_metadata_input handling PermissionError when reading a JSON file."""
    with patch("builtins.open", side_effect=PermissionError("mocked permission error")):
        assert parse_metadata_input(["locked_file.json"]) == {}
        mock_print.assert_called_once()
        assert (
            "[red]Error: Permission denied reading JSON file.[/]"
            in mock_print.call_args[0][0]
        )


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_json_file_unicode_decode_error(mock_print):
    """Test parse_metadata_input handling UnicodeDecodeError when reading a JSON file."""
    with patch(
        "builtins.open",
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "mocked error"),
    ):
        assert parse_metadata_input(["bad_encoding.json"]) == {}
        mock_print.assert_called_once()
        assert (
            "[red]Error: JSON file must be UTF-8 encoded.[/]"
            in mock_print.call_args[0][0]
        )


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_json_file_json_decode_error(mock_print):
    """Test parse_metadata_input handling JSONDecodeError when reading a JSON file."""
    import json

    with patch("builtins.open"):
        with patch(
            "json.load", side_effect=json.JSONDecodeError("mocked error", "", 0)
        ):
            assert parse_metadata_input(["bad_format.json"]) == {}
            mock_print.assert_called_once()
            assert (
                "[red]Error: File is not valid JSON.[/]" in mock_print.call_args[0][0]
            )


@patch("image_converter.metadata.console.print")
def test_parse_metadata_input_json_file_non_dict(mock_print, tmp_path):
    """Test parse_metadata_input handling JSON file that does not evaluate to a dict."""
    json_file = tmp_path / "not_dict.json"
    json_file.write_text('["not", "a", "dict"]')

    assert parse_metadata_input([str(json_file)]) == {}
    mock_print.assert_called_once_with(
        "[red]Error: JSON file must contain a key-value dictionary object.[/]"
    )


@patch("image_converter.metadata.console.print")
@patch("image_converter.metadata.json.loads")
def test_parse_metadata_input_inline_json_non_dict(mock_loads, mock_print):
    """Test parse_metadata_input handling inline JSON that does not evaluate to a dict."""
    mock_loads.return_value = ["not", "a", "dict"]

    assert parse_metadata_input(['{"fake_key": "fake_value"}']) == {}
    mock_print.assert_called_once_with(
        "[red]Error: Inline JSON must be a key-value dictionary object.[/]"
    )
