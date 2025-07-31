"""Tests for model scanner functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

from lmstrix.core.scanner import ModelScanner


class TestModelScanner:
    """Test ModelScanner class."""

    @patch("lmstrix.core.scanner.get_lmstudio_path")
    def test_scanner_initialization(
        self: "TestModelScanner",
        mock_get_path: Mock,
        tmp_path: Path,
    ) -> None:
        """Test scanner initialization."""
        mock_lms_path = tmp_path / "lmstudio"
        mock_get_path.return_value = mock_lms_path

        scanner = ModelScanner()

        assert scanner.lms_path == mock_lms_path
        assert scanner.models_dir == mock_lms_path / "models"

    def test_get_model_size_file(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test getting size of a single model file."""
        scanner = ModelScanner()

        # Create a test file
        model_file = tmp_path / "model.gguf"
        model_file.write_text("x" * 1000)

        size = scanner._get_model_size(model_file)
        assert size == 1000

    def test_get_model_size_directory(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test getting size of a model directory."""
        scanner = ModelScanner()

        # Create a model directory with multiple files
        model_dir = tmp_path / "model_dir"
        model_dir.mkdir()

        (model_dir / "weights.bin").write_text("x" * 500)
        (model_dir / "config.json").write_text("x" * 100)
        (model_dir / "subfolder").mkdir()
        (model_dir / "subfolder" / "more.bin").write_text("x" * 200)

        size = scanner._get_model_size(model_dir)
        assert size == 800  # 500 + 100 + 200

    def test_get_model_size_nonexistent(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test getting size of non-existent path."""
        scanner = ModelScanner()

        non_existent = tmp_path / "does_not_exist"
        size = scanner._get_model_size(non_existent)
        assert size == 0

    def test_extract_model_info_gguf_file(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test extracting info from GGUF model file."""
        scanner = ModelScanner()

        model_file = tmp_path / "llama-7b.gguf"
        model_file.write_text("x" * 1000)

        info = scanner._extract_model_info(model_file)

        assert info is not None
        assert info["id"] == str(model_file)  # Uses full path when not in models_dir
        assert info["path"] == str(model_file)
        assert info["size_bytes"] == 1000
        assert info["ctx_in"] == 4096  # Default

    def test_extract_model_info_mlx_directory(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test extracting info from MLX model directory."""
        scanner = ModelScanner()

        # Create MLX model structure
        model_dir = tmp_path / "llama-7b-mlx"
        model_dir.mkdir()
        (model_dir / "weights.npz").write_text("x" * 500)
        (model_dir / "config.json").write_text("{}")

        info = scanner._extract_model_info(model_dir)

        assert info is not None
        assert info["id"] == str(model_dir)  # Uses full path when not in models_dir
        assert info["path"] == str(model_dir)
        assert info["size_bytes"] >= 500  # At least the size of weights.npz

    def test_extract_model_info_hidden_file(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test that hidden files are skipped."""
        scanner = ModelScanner()

        hidden_file = tmp_path / ".hidden_model.gguf"
        hidden_file.write_text("x" * 1000)

        info = scanner._extract_model_info(hidden_file)
        assert info is None

    def test_extract_model_info_non_model_file(self: "TestModelScanner", tmp_path: Path) -> None:
        """Test that non-model files are skipped."""
        scanner = ModelScanner()

        text_file = tmp_path / "readme.txt"
        text_file.write_text("Not a model")

        info = scanner._extract_model_info(text_file)
        assert info is None

    @patch("lmstrix.core.scanner.get_lmstudio_path")
    def test_scan_models(self: "TestModelScanner", mock_get_path: Mock, tmp_path: Path) -> None:
        """Test scanning for models."""
        # Set up mock LM Studio directory structure
        lms_path = tmp_path / "lmstudio"
        models_dir = lms_path / "models"
        models_dir.mkdir(parents=True)

        # Create some test models
        (models_dir / "model1.gguf").write_text("x" * 1000)
        (models_dir / "model2.gguf").write_text("x" * 2000)

        mlx_dir = models_dir / "model3-mlx"
        mlx_dir.mkdir()
        (mlx_dir / "weights.npz").write_text("x" * 3000)
        (mlx_dir / "config.json").write_text("{}")

        # Hidden and non-model files to skip
        (models_dir / ".hidden.gguf").write_text("x" * 100)
        (models_dir / "readme.txt").write_text("info")

        mock_get_path.return_value = lms_path

        scanner = ModelScanner()
        models = scanner.scan_models()

        assert len(models) == 3

        # Check model IDs
        model_ids = list(models.keys())
        assert "model1.gguf" in model_ids
        assert "model2.gguf" in model_ids
        assert "model3-mlx" in model_ids

        # Check sizes
        assert models["model1.gguf"]["size_bytes"] == 1000
        assert models["model2.gguf"]["size_bytes"] == 2000
        assert models["model3-mlx"]["size_bytes"] >= 3000  # Allow for filesystem overhead

    @patch("lmstrix.core.scanner.get_lmstudio_path")
    def test_sync_with_registry(
        self: "TestModelScanner",
        mock_get_path: Mock,
        tmp_path: Path,
    ) -> None:
        """Test syncing scanned models with registry."""
        # Set up mock LM Studio directory
        lms_path = tmp_path / "lmstudio"
        models_dir = lms_path / "models"
        models_dir.mkdir(parents=True)

        # Create a test model
        (models_dir / "new-model.gguf").write_text("x" * 1000)

        mock_get_path.return_value = lms_path

        # Mock registry
        mock_registry = Mock()
        mock_registry.get_model.return_value = None  # Model not in registry
        mock_registry.list_models.return_value = []  # No existing models
        mock_registry.remove_model = Mock()
        mock_registry.update_model = Mock()
        mock_registry.save = Mock()

        scanner = ModelScanner()
        new_models, removed_models = scanner.sync_with_registry(mock_registry)

        assert len(new_models) == 1
        assert new_models[0] == "new-model.gguf"
        assert len(removed_models) == 0

        # Verify model was added to registry
        mock_registry.update_model.assert_called_once()
        call_args = mock_registry.update_model.call_args
        assert call_args[0][0] == "new-model.gguf"
        assert call_args[0][1].id == "new-model.gguf"
