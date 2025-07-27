"""Test context loading functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.loaders.context_loader import load_context


class TestContextLoader:
    """Test context loading functions."""

    def test_load_context_simple(self, tmp_path: Path) -> None:
        """Test loading simple text context."""
        context_file = tmp_path / "context.txt"
        test_content = "This is a test context file.\nIt has multiple lines.\nAnd some content."
        context_file.write_text(test_content)

        content = load_context(context_file, verbose=True)

        assert content == test_content

    def test_load_context_with_encoding(self, tmp_path: Path) -> None:
        """Test loading context with specific encoding."""
        context_file = tmp_path / "context_utf8.txt"
        test_content = "Unicode content: 你好世界 🌍"
        context_file.write_text(test_content, encoding="utf-8")

        content = load_context(context_file, encoding="utf-8")

        assert content == test_content

    def test_load_context_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(ConfigurationError) as exc_info:
            load_context(nonexistent)

        assert "not found" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    def test_load_context_read_error(self, tmp_path: Path) -> None:
        """Test handling read errors."""
        # Create a file then make it unreadable (platform-specific)
        bad_file = tmp_path / "unreadable.txt"
        bad_file.write_text("content")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.side_effect = PermissionError("Access denied")

            with pytest.raises(ConfigurationError) as exc_info:
                load_context(bad_file)

            assert "read" in str(exc_info.value).lower()

    def test_load_context_string_path(self, tmp_path: Path) -> None:
        """Test loading context with string path."""
        context_file = tmp_path / "string_path.txt"
        test_content = "String path test"
        context_file.write_text(test_content)

        # Pass as string instead of Path
        content = load_context(str(context_file))

        assert content == test_content

    def test_load_context_large_file(self, tmp_path: Path) -> None:
        """Test loading large context file."""
        large_file = tmp_path / "large.txt"
        # Create a ~1MB file
        large_content = "x" * 1024 * 1024
        large_file.write_text(large_content)

        content = load_context(large_file)

        assert len(content) == 1024 * 1024
