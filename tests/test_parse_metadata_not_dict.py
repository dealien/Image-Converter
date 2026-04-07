import pytest
from unittest.mock import patch, mock_open
from image_converter.metadata import parse_metadata_input


@pytest.fixture
def mock_print():
    with patch("image_converter.metadata.console.print") as mock:
        yield mock


def test_parse_metadata_input_json_file_not_dict(mock_print):
    """Test parse_metadata_input where JSON file parses to a non-dict (e.g. list)."""
    with patch("builtins.open", mock_open(read_data="[]")):
        assert parse_metadata_input(["some_file.json"]) == {}
        mock_print.assert_called_once()
        assert "key-value dictionary" in mock_print.call_args[0][0]


def test_parse_metadata_input_inline_json_not_dict(mock_print):
    """Test parse_metadata_input where inline JSON parses to a non-dict."""
    with patch("json.loads", return_value=["a", "list", "instead", "of", "dict"]):
        assert parse_metadata_input(['{"mocked": "anyway"}']) == {}
        mock_print.assert_called_once()
        assert "key-value dictionary" in mock_print.call_args[0][0]
