"""Unit tests for path utility functions in LMStrix.

This suite tests the functions responsible for locating the LM Studio home directory
and the default model registry file. It uses mocking to simulate different
environmental conditions, such as the presence or absence of the `.lmstudio-home-pointer`
file and the existence of common LM Studio installation directories.

Key functions tested:
- `get_lmstudio_path()`: Verifies its ability to find the LM Studio path from the
  pointer file and fall back to default locations.
- `get_default_models_file()`: Ensures it correctly constructs the path to the
  `lmstrix.json` file within the application's data directory.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from lmstrix.utils.paths import get_lmstudio_path, get_default_models_file

# --- Tests for get_lmstudio_path --- 

@patch("pathlib.Path.home")
def test_get_lmstudio_path_from_pointer_file(mock_home):
    """Test that the path is correctly read from the .lmstudio-home-pointer file."""
    # Setup: Mock the home directory and the pointer file
    mock_home.return_value = Path("/fake/home")
    pointer_path = Path("/fake/home/.lmstudio-home-pointer")
    expected_path = "/fake/lmstudio/custom/path"

    # Use mock_open to simulate reading the file content
    with patch("pathlib.Path.open", mock_open(read_data=expected_path)) as mock_file,
         patch("pathlib.Path.exists", return_value=True) as mock_exists:
        
        # Run the function
        lmstudio_path = get_lmstudio_path()

        # Assertions
        mock_exists.assert_called_with(pointer_path)
        mock_file.assert_called_once_with("r", encoding="utf-8")
        assert lmstudio_path == Path(expected_path)

@patch("pathlib.Path.home")
def test_get_lmstudio_path_fallback_to_default(mock_home):
    """Test the fallback mechanism when the pointer file does not exist."""
    # Setup: No pointer file, but a default directory exists
    mock_home.return_value = Path("/fake/home")
    pointer_path = Path("/fake/home/.lmstudio-home-pointer")
    default_path = Path("/fake/home/.cache/lm-studio")

    # Simulate which paths exist
    def path_exists_side_effect(path):
        if path == pointer_path:
            return False # Pointer file does not exist
        if path == default_path:
            return True  # Default directory exists
        return False

    with patch("pathlib.Path.exists", side_effect=path_exists_side_effect):
        # Run the function
        lmstudio_path = get_lmstudio_path()

        # Assertion
        assert lmstudio_path == default_path

@patch("pathlib.Path.home")
def test_get_lmstudio_path_not_found(mock_home):
    """Test that an exception is raised if no path can be found."""
    # Setup: No pointer file and no default directories exist
    mock_home.return_value = Path("/fake/home")
    
    with patch("pathlib.Path.exists", return_value=False):
        # Run and assert that a FileNotFoundError is raised
        with pytest.raises(FileNotFoundError, match="Could not find LM Studio home directory."):
            get_lmstudio_path()

# --- Tests for get_default_models_file ---

@patch("appdirs.user_data_dir")
@patch("pathlib.Path.mkdir")
def test_get_default_models_file_creates_dir(mock_mkdir, mock_appdirs):
    """Test that the function creates the necessary directory and returns the correct file path."""
    # Setup
    expected_dir = Path("/fake/appdata/lmstrix")
    expected_file = expected_dir / "lmstrix.json"
    mock_appdirs.return_value = str(expected_dir)

    # Run the function
    models_file_path = get_default_models_file()

    # Assertions
    mock_appdirs.assert_called_once_with("lmstrix", "lmstrix")
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    assert models_file_path == expected_file
