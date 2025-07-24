"""Integration tests for CLI functionality."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from lmstrix.cli.main import create_app
from lmstrix.core.models import Model


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    @pytest.fixture
    def mock_lmstudio_setup(self, tmp_path):
        """Set up mock LM Studio environment."""
        lms_path = tmp_path / "lmstudio"
        lms_path.mkdir()
        (lms_path / "models").mkdir()
        
        # Create mock registry file
        registry_file = lms_path / "lmstrix.json"
        registry_data = {
            "llms": {
                "test-model-1": {
                    "id": "test-model-1",
                    "path": "/path/to/model1.gguf",
                    "size_bytes": 1000000,
                    "ctx_in": 4096,
                    "ctx_out": 4096,
                    "has_tools": False,
                    "has_vision": False,
                    "tested_max_context": 3500,
                    "context_test_status": "completed",
                },
                "test-model-2": {
                    "id": "test-model-2",
                    "path": "/path/to/model2.gguf",
                    "size_bytes": 2000000,
                    "ctx_in": 8192,
                    "ctx_out": 4096,
                    "has_tools": True,
                    "has_vision": False,
                    "context_test_status": "untested",
                }
            }
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        
        return lms_path, registry_file

    @patch("lmstrix.utils.paths.get_lmstudio_path")
    @patch("lmstrix.cli.main.LMStudioClient")
    def test_list_models_command(self, mock_client_class, mock_get_path, mock_lmstudio_setup, capsys):
        """Test 'models list' command."""
        lms_path, registry_file = mock_lmstudio_setup
        mock_get_path.return_value = lms_path
        
        # Create app and execute command
        app = create_app()
        
        # Mock Fire to call the method directly
        with patch("fire.Fire") as mock_fire:
            # Call the list method directly
            from lmstrix.cli.main import CLI
            cli = CLI(verbose=False)
            cli.models.list()
        
        # Check output
        captured = capsys.readouterr()
        assert "test-model-1" in captured.out
        assert "test-model-2" in captured.out
        assert "3500" in captured.out  # tested context
        assert "8192" in captured.out  # declared context

    @patch("lmstrix.utils.paths.get_lmstudio_path")
    @patch("lmstrix.cli.main.LMStudioClient")
    @patch("lmstrix.cli.main.ModelScanner")
    def test_scan_models_command(self, mock_scanner_class, mock_client_class, mock_get_path, mock_lmstudio_setup):
        """Test 'models scan' command."""
        lms_path, registry_file = mock_lmstudio_setup
        mock_get_path.return_value = lms_path
        
        # Mock scanner to return new model
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        
        new_model = Model(
            id="new-model",
            path="/path/to/new.gguf",
            size_bytes=3000000,
            ctx_in=16384,
        )
        mock_scanner.sync_with_registry.return_value = ([new_model], [])
        
        # Create CLI and execute scan
        from lmstrix.cli.main import CLI
        cli = CLI(verbose=False)
        cli.models.scan()
        
        # Verify scanner was called
        mock_scanner.sync_with_registry.assert_called_once()

    @patch("lmstrix.utils.paths.get_lmstudio_path")
    @patch("lmstrix.cli.main.LMStudioClient")
    @pytest.mark.asyncio
    async def test_optimize_command(self, mock_client_class, mock_get_path, mock_lmstudio_setup):
        """Test 'optimize' command."""
        lms_path, registry_file = mock_lmstudio_setup
        mock_get_path.return_value = lms_path
        
        # Mock client and context tester
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        with patch("lmstrix.cli.main.ContextTester") as mock_tester_class:
            mock_tester = Mock()
            mock_tester_class.return_value = mock_tester
            
            # Mock optimization result
            optimized_model = Model(
                id="test-model-2",
                path="/path/to/model2.gguf",
                size_bytes=2000000,
                ctx_in=8192,
                tested_max_context=7000,
                context_test_status="completed",
            )
            mock_tester.optimize_model = AsyncMock(return_value=optimized_model)
            
            # Create CLI and call optimize
            from lmstrix.cli.main import CLI
            cli = CLI(verbose=False)
            
            # Need to run async method
            import asyncio
            await cli.optimize("test-model-2")
            
            # Verify optimization was called
            mock_tester.optimize_model.assert_called_once()

    @patch("lmstrix.utils.paths.get_lmstudio_path")
    def test_infer_command_missing_prompt(self, mock_get_path, mock_lmstudio_setup, capsys):
        """Test 'infer' command with missing prompt."""
        lms_path, registry_file = mock_lmstudio_setup
        mock_get_path.return_value = lms_path
        
        from lmstrix.cli.main import CLI
        cli = CLI(verbose=False)
        
        # Should show error for missing prompt
        with pytest.raises(SystemExit):
            cli.infer(model="test-model-1")

    @patch("lmstrix.utils.paths.get_lmstudio_path")
    @patch("lmstrix.cli.main.load_prompts")
    @patch("lmstrix.cli.main.InferenceEngine")
    @pytest.mark.asyncio
    async def test_infer_with_prompt_file(self, mock_engine_class, mock_load_prompts, mock_get_path, mock_lmstudio_setup, tmp_path):
        """Test 'infer' command with prompt file."""
        lms_path, registry_file = mock_lmstudio_setup
        mock_get_path.return_value = lms_path
        
        # Create prompt file
        prompt_file = tmp_path / "test_prompt.toml"
        
        # Mock prompt loading
        from lmstrix.core.prompts import ResolvedPrompt
        mock_prompt = ResolvedPrompt(
            name="test_prompt",
            template="Analyze: {{input}}",
            resolved="Analyze: Test input",
        )
        mock_load_prompts.return_value = {"test_prompt": mock_prompt}
        
        # Mock inference engine
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        from lmstrix.core.inference import InferenceResult
        mock_result = InferenceResult(
            model_id="test-model-1",
            prompt="Analyze: Test input",
            response="Analysis complete",
            tokens_used=50,
            inference_time=0.5,
        )
        mock_engine.infer = AsyncMock(return_value=mock_result)
        
        # Run inference
        from lmstrix.cli.main import CLI
        cli = CLI(verbose=False)
        
        await cli.infer(
            model="test-model-1",
            prompt_file=str(prompt_file),
            input="Test input"
        )
        
        # Verify calls
        mock_load_prompts.assert_called_once()
        mock_engine.infer.assert_called_once()

    def test_cli_help(self, capsys):
        """Test CLI help output."""
        with patch("fire.Fire") as mock_fire:
            from lmstrix.cli.main import main
            main()
            
            # Fire should be called to create the CLI
            mock_fire.assert_called_once()