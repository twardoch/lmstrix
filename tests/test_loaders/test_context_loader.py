"""Tests for context file loader functionality."""

from unittest.mock import patch

import pytest

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.loaders.context_loader import (
    load_context,
    load_context_batch,
    merge_contexts,
)


class TestContextLoader:
    """Test context loading functions."""

    def test_load_context_simple(self, tmp_path):
        """Test loading simple text context."""
        context_file = tmp_path / "context.txt"
        test_content = "This is a test context file.\nIt has multiple lines.\nAnd some content."
        context_file.write_text(test_content)

        content = load_context(context_file, verbose=True)

        assert content == test_content

    def test_load_context_with_encoding(self, tmp_path):
        """Test loading context with specific encoding."""
        context_file = tmp_path / "context_utf8.txt"
        test_content = "Unicode content: 你好世界 🌍"
        context_file.write_text(test_content, encoding="utf-8")

        content = load_context(context_file, encoding="utf-8")

        assert content == test_content

    def test_load_context_nonexistent_file(self, tmp_path):
        """Test loading from non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(ConfigurationError) as exc_info:
            load_context(nonexistent)

        assert "not found" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    def test_load_context_read_error(self, tmp_path):
        """Test handling read errors."""
        # Create a file then make it unreadable (platform-specific)
        bad_file = tmp_path / "unreadable.txt"
        bad_file.write_text("content")

        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.side_effect = PermissionError("Access denied")

            with pytest.raises(ConfigurationError) as exc_info:
                load_context(bad_file)

            assert "read" in str(exc_info.value).lower()

    def test_load_context_string_path(self, tmp_path):
        """Test loading context with string path."""
        context_file = tmp_path / "string_path.txt"
        test_content = "String path test"
        context_file.write_text(test_content)

        # Pass as string instead of Path
        content = load_context(str(context_file))

        assert content == test_content

    def test_load_context_large_file(self, tmp_path):
        """Test loading large context file."""
        large_file = tmp_path / "large.txt"
        # Create a ~1MB file
        large_content = "x" * 1024 * 1024
        large_file.write_text(large_content)

        content = load_context(large_file)

        assert len(content) == 1024 * 1024

    def test_load_context_batch_single(self, tmp_path):
        """Test loading batch with single file."""
        file1 = tmp_path / "batch1.txt"
        file1.write_text("Content 1")

        contexts = load_context_batch([file1])

        assert len(contexts) == 1
        assert str(file1) in contexts
        assert contexts[str(file1)] == "Content 1"

    def test_load_context_batch_multiple(self, tmp_path):
        """Test loading batch with multiple files."""
        file1 = tmp_path / "batch1.txt"
        file2 = tmp_path / "batch2.txt"
        file3 = tmp_path / "batch3.txt"

        file1.write_text("Content 1")
        file2.write_text("Content 2")
        file3.write_text("Content 3")

        contexts = load_context_batch([file1, file2, file3], verbose=True)

        assert len(contexts) == 3
        assert contexts[str(file1)] == "Content 1"
        assert contexts[str(file2)] == "Content 2"
        assert contexts[str(file3)] == "Content 3"

    def test_load_context_batch_with_errors(self, tmp_path):
        """Test batch loading continues on error."""
        file1 = tmp_path / "exists.txt"
        file2 = tmp_path / "does_not_exist.txt"
        file3 = tmp_path / "also_exists.txt"

        file1.write_text("Content 1")
        file3.write_text("Content 3")

        contexts = load_context_batch([file1, file2, file3])

        # Should load files that exist, skip the one that doesn't
        assert len(contexts) == 2
        assert contexts[str(file1)] == "Content 1"
        assert contexts[str(file3)] == "Content 3"
        assert str(file2) not in contexts

    def test_load_context_batch_empty(self):
        """Test loading empty batch."""
        contexts = load_context_batch([])

        assert contexts == {}

    def test_merge_contexts_simple(self):
        """Test merging simple contexts."""
        contexts = {
            "file1": "First content",
            "file2": "Second content",
            "file3": "Third content",
        }

        merged = merge_contexts(contexts)

        assert "First content" in merged
        assert "Second content" in merged
        assert "Third content" in merged
        assert merged.count("\n---\n") == 2  # Two separators between 3 files

    def test_merge_contexts_with_separator(self):
        """Test merging with custom separator."""
        contexts = {
            "file1": "Content 1",
            "file2": "Content 2",
        }

        merged = merge_contexts(contexts, separator="\n***\n")

        assert "Content 1" in merged
        assert "Content 2" in merged
        assert "\n***\n" in merged

    def test_merge_contexts_single(self):
        """Test merging single context."""
        contexts = {"only_file": "Only content"}

        merged = merge_contexts(contexts)

        assert merged == "Only content"

    def test_merge_contexts_empty(self):
        """Test merging empty contexts."""
        merged = merge_contexts({})

        assert merged == ""

    def test_merge_contexts_with_headers(self):
        """Test that merge includes file headers."""
        contexts = {
            "/path/to/file1.txt": "Content 1",
            "/path/to/file2.txt": "Content 2",
        }

        merged = merge_contexts(contexts, include_headers=True)

        assert "file1.txt" in merged
        assert "file2.txt" in merged
        assert "Content 1" in merged
        assert "Content 2" in merged
