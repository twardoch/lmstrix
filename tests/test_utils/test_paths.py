"""Tests for path utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from lmstrix.utils.paths import (
    get_context_test_log_path,
    get_context_tests_dir,
    get_contexts_dir,
    get_default_models_file,
    get_lmstrix_data_dir,
    get_lmstudio_path,
    get_prompts_dir,
)


class TestPathUtilities:
    """Test path utility functions."""

    def test_get_lmstudio_path_from_pointer(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting LM Studio path from home pointer file."""
        # Create mock home directory with pointer file
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        pointer_file = home_dir / ".lmstudio-home-pointer"
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()
        (lms_path / "models").mkdir()

        pointer_file.write_text(str(lms_path))

        with patch("pathlib.Path.home", return_value=home_dir):
            result = get_lmstudio_path()

        assert result == lms_path

    def test_get_lmstudio_path_fallback_locations(
        self: "TestPathUtilities",
        tmp_path: Path,
    ) -> None:
        """Test fallback to common LM Studio locations."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        # Create LM Studio in cache location
        cache_lms = home_dir / ".cache" / "lm-studio"
        cache_lms.mkdir(parents=True)
        (cache_lms / "models").mkdir()

        with patch("pathlib.Path.home", return_value=home_dir):
            result = get_lmstudio_path()

        assert result == cache_lms

    def test_get_lmstudio_path_shared_location(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test finding LM Studio in shared location."""
        # No home pointer, no cache location
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        # Mock the shared path check
        Path("/Users/Shared/lmstudio")

        with (
            patch("pathlib.Path.home", return_value=home_dir),
            patch(
                "pathlib.Path.exists",
            ) as mock_exists,
        ):

            def exists_side_effect(self: Path) -> bool:
                if str(self) == str(home_dir / ".lmstudio-home-pointer") or str(self) == str(
                    home_dir / ".cache" / "lm-studio",
                ):
                    return False
                return bool(
                    str(self) == "/Users/Shared/lmstudio"
                    or str(self) == "/Users/Shared/lmstudio/models",
                )

            mock_exists.side_effect = exists_side_effect

            result = get_lmstudio_path()

        assert str(result) == "/Users/Shared/lmstudio"

    def test_get_lmstudio_path_not_found(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test error when LM Studio is not found."""
        home_dir = tmp_path / "home"
        home_dir.mkdir()

        with patch("pathlib.Path.home", return_value=home_dir):
            with pytest.raises(RuntimeError) as exc_info:
                get_lmstudio_path()

            assert "Could not find LM Studio" in str(exc_info.value)

    def test_get_lmstrix_data_dir(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting LMStrix data directory."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()
        (lms_path / "models").mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            data_dir = get_lmstrix_data_dir()

        assert data_dir == lms_path / "lmstrix"
        assert data_dir.exists()

    def test_get_lmstrix_data_dir_exists(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting existing LMStrix data directory."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()
        data_dir = lms_path / "lmstrix"
        data_dir.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            result = get_lmstrix_data_dir()

        assert result == data_dir

    def test_get_default_models_file(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting default models file path."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            models_file = get_default_models_file()

        assert models_file == lms_path / "lmstrix.json"

    def test_get_context_tests_dir(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting context tests directory."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            tests_dir = get_context_tests_dir()

        assert tests_dir == lms_path / "lmstrix" / "context_tests"
        assert tests_dir.exists()

    def test_get_context_test_log_path(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting context test log path."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            # Test with simple model ID
            log_path = get_context_test_log_path("model-123")
            assert log_path.name == "model-123_context_test.log"
            assert log_path.parent.name == "context_tests"

            # Test with complex model ID (special chars)
            log_path2 = get_context_test_log_path("model/with:special@chars!")
            assert log_path2.name == "model_with_special_chars__context_test.log"

    def test_get_prompts_dir(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting prompts directory."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            prompts_dir = get_prompts_dir()

        assert prompts_dir == lms_path / "lmstrix" / "prompts"
        assert prompts_dir.exists()

    def test_get_contexts_dir(self: "TestPathUtilities", tmp_path: Path) -> None:
        """Test getting contexts directory."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path):
            contexts_dir = get_contexts_dir()

        assert contexts_dir == lms_path / "lmstrix" / "contexts"
        assert contexts_dir.exists()

    def test_directory_creation_permissions_error(
        self: "TestPathUtilities",
        tmp_path: Path,
    ) -> None:
        """Test handling permission errors when creating directories."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()

        with (
            patch("lmstrix.utils.paths.get_lmstudio_path", return_value=lms_path),
            patch(
                "pathlib.Path.mkdir",
            ) as mock_mkdir,
        ):
            mock_mkdir.side_effect = PermissionError("Access denied")

            # This should raise since we can't create the directory
            with pytest.raises(PermissionError):
                get_lmstrix_data_dir()
