"""Integration tests for CLI functionality - SIMPLIFIED."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lmstrix.__main__ import LMStrixCLI


class TestCLIIntegration:
    """Test CLI integration - basic functionality only."""

    @pytest.fixture
    def mock_registry(self, tmp_path: Path) -> Path:
        """Create a mock model registry."""
        registry_file = tmp_path / "lmstrix.json"
        registry_data = {
            "llms": {
                "test-model": {
                    "id": "test-model",
                    "path": "/path/to/model.gguf",
                    "size_bytes": 1000000,
                    "ctx_in": 4096,
                    "ctx_out": 4096,
                    "has_tools": False,
                    "has_vision": False,
                    "tested_max_context": 3500,
                    "context_test_status": "completed",
                },
            },
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        return registry_file

    def test_cli_initialization(self) -> None:
        """Test CLI can be initialized."""
        cli = LMStrixCLI()
        assert cli is not None
        assert hasattr(cli, "scan")
        assert hasattr(cli, "list")
        assert hasattr(cli, "test")
        assert hasattr(cli, "infer")

    @patch("lmstrix.api.main.get_default_models_file")
    def test_list_command(self, mock_get_file: Mock, mock_registry: Path, capsys) -> None:
        """Test list command shows models."""
        mock_get_file.return_value = mock_registry

        cli = LMStrixCLI()
        cli.list()

        captured = capsys.readouterr()
        assert "test-model" in captured.out
        assert "3500" in captured.out  # tested context

    @patch("lmstrix.api.main.get_default_models_file")
    def test_list_json_format(self, mock_get_file: Mock, mock_registry: Path, capsys) -> None:
        """Test list command with JSON output."""
        mock_get_file.return_value = mock_registry

        cli = LMStrixCLI()
        cli.list(show="json")

        captured = capsys.readouterr()
        # Should be valid JSON
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "test-model"

    def test_infer_requires_parameters(self) -> None:
        """Test infer command validates required parameters."""
        cli = LMStrixCLI()

        # Should handle missing parameters gracefully
        # The actual implementation would show an error
        with pytest.raises(TypeError):
            cli.infer()  # Missing required arguments
