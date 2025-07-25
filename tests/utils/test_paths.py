# tests/utils/test_paths.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from lmstrix.utils.paths import get_lmstudio_path, get_default_models_file

@patch('lmstrix.utils.paths.Path.home')
def test_get_lmstudio_path_from_pointer(mock_home):
    """
    Tests that the path is correctly read from the .lmstudio-home-pointer file.
    """
    # Arrange
    mock_home_dir = MagicMock()
    mock_pointer_file = MagicMock()
    mock_pointer_file.exists.return_value = True
    mock_pointer_file.read_text.return_value = "/custom/lmstudio/path"
    mock_home.return_value = mock_home_dir
    mock_home_dir / ".lmstudio-home-pointer" = mock_pointer_file

    # Act
    path = get_lmstudio_path()

    # Assert
    assert path == Path("/custom/lmstudio/path")

@patch('lmstrix.utils.paths.Path.exists')
@patch('lmstrix.utils.paths.Path.home')
def test_fallback_to_default_directories(mock_home, mock_exists):
    """
    Tests the fallback mechanism when the pointer file doesn't exist.
    """
    # Arrange
    mock_home_dir = Path("/home/user")
    mock_home.return_value = mock_home_dir
    
    # Simulate pointer file not existing, but a default path existing
    def path_exists_side_effect(path):
        return str(path) == str(mock_home_dir / ".cache/lm-studio")

    mock_exists.side_effect = path_exists_side_effect

    # Act
    path = get_lmstudio_path()

    # Assert
    assert path == mock_home_dir / ".cache/lm-studio"

@patch('lmstrix.utils.paths.Path.exists')
@patch('lmstrix.utils.paths.Path.home')
def test_no_path_found_raises_error(mock_home, mock_exists):
    """
    Tests that a FileNotFoundError is raised if no LM Studio path can be found.
    """
    # Arrange
    mock_home.return_value = Path("/home/user")
    mock_exists.return_value = False # Simulate no paths existing

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        get_lmstudio_path()

@patch('lmstrix.utils.paths.get_lmstudio_path')
def test_get_default_models_file_path(mock_get_lmstudio_path):
    """
    Ensures the models file path is correctly constructed inside the LM Studio dir.
    """
    # Arrange
    mock_lmstudio_path = Path("/fake/lmstudio")
    mock_get_lmstudio_path.return_value = mock_lmstudio_path

    # Act
    models_file_path = get_default_models_file()

    # Assert
    assert models_file_path == mock_lmstudio_path / "lmstrix.json"
