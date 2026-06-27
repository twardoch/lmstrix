"""Tests for model listing output."""

from pathlib import Path

from lmstrix.api.listing import list_models_command
from lmstrix.core.models import Model, ModelRegistry


def test_list_models_command_reports_capabilities(tmp_path: Path, capsys) -> None:
    """Test default list output includes model capabilities."""
    registry = ModelRegistry(models_file=tmp_path / "models.json")
    registry.update_model(
        "capable-model",
        Model(
            model_id="capable-model",
            path="/path/to/capable-model",
            size_bytes=1024,
            ctx_in=8192,
            capabilities={
                "vision": True,
                "trained_for_tool_use": True,
                "reasoning": {"allowed_options": ["off", "on"], "default": "on"},
            },
        ),
    )

    list_models_command(registry=registry)

    captured = capsys.readouterr()
    assert "Capabilities" in captured.out
    assert "vision" in captured.out
    assert "tools" in captured.out
    assert "reasoning" in captured.out
