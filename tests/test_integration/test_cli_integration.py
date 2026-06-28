"""Integration tests for CLI functionality.

Tests in this file split into two groups:

* **Mock-based** — return a synthetic registry without touching disk or
  LM Studio.  These always run.

* **Live-server** — marked ``@pytest.mark.integration`` and guarded by the
  ``lmstudio_server`` fixture.  They are skipped automatically in CI unless
  a real LM Studio instance is reachable at ``http://localhost:1234``.
"""

# this_file: tests/test_integration/test_cli_integration.py

import json
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from lmstrix.__main__ import LMStrixCLI
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lmstudio_reachable() -> bool:
    """Return True when LM Studio's REST API is reachable."""
    try:
        r = httpx.get("http://localhost:1234/v1/models", timeout=2.0)
        return r.status_code < 500
    except Exception:
        return False


def _make_test_model() -> Model:
    """Return a minimal Model instance for use in tests."""
    return Model(
        model_id="test-model",
        path="/path/to/model.gguf",
        size_bytes=1_000_000,
        ctx_in=4096,
        ctx_out=4096,
        has_tools=False,
        has_vision=False,
        tested_max_context=3500,
        context_test_status="completed",
    )


def _make_registry(tmp_path: Path) -> ModelRegistry:
    """Return a ModelRegistry backed by a temp file containing one model."""
    registry_file = tmp_path / "lmstrix.json"
    data = {
        "llms": {
            "test-model": {
                "id": "test-model",
                "path": "/path/to/model.gguf",
                "size_bytes": 1_000_000,
                "ctx_in": 4096,
                "ctx_out": 4096,
                "has_tools": False,
                "has_vision": False,
                "tested_max_context": 3500,
                "context_test_status": "completed",
            },
        },
    }
    registry_file.write_text(json.dumps(data, indent=2))
    return ModelRegistry(models_file=registry_file)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lmstudio_server() -> None:
    """Skip the test if LM Studio server is not running locally.

    Mark tests that need a live server with ``@pytest.mark.integration``
    and list this fixture in their signature.  In CI (no LM Studio) the
    test is automatically skipped with a clear message.
    """
    if not _lmstudio_reachable():
        pytest.skip(
            "LM Studio server not reachable at http://localhost:1234 — skipping integration test"
        )


# ---------------------------------------------------------------------------
# Mock-based tests (always run)
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """CLI tests that run without a live LM Studio server."""

    def test_cli_initialization(self) -> None:
        """CLI can be instantiated and exposes the expected commands."""
        cli = LMStrixCLI()
        assert cli is not None
        assert hasattr(cli, "scan")
        assert hasattr(cli, "list")
        assert hasattr(cli, "test")
        assert hasattr(cli, "infer")

    def test_list_command(self, tmp_path: Path, capsys) -> None:
        """list command prints registered models from the registry."""
        registry = _make_registry(tmp_path)
        # list_models_command calls scan_and_update_registry first; patch that.
        with patch("lmstrix.api.listing.scan_and_update_registry", return_value=registry):
            cli = LMStrixCLI()
            cli.list()

        captured = capsys.readouterr()
        assert "test-model" in captured.out
        assert "3,500" in captured.out  # displayed with thousands separator

    def test_list_json_format(self, tmp_path: Path, capsys) -> None:
        """list --show json emits valid JSON containing the registry models."""
        registry = _make_registry(tmp_path)
        with patch("lmstrix.api.listing.scan_and_update_registry", return_value=registry):
            cli = LMStrixCLI()
            cli.list(show="json")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "test-model"

    def test_infer_requires_parameters(self) -> None:
        """infer raises TypeError when called with no arguments."""
        cli = LMStrixCLI()
        with pytest.raises(TypeError):
            cli.infer()  # type: ignore[call-arg]

    def test_dry_run_flag(self, tmp_path: Path) -> None:
        """test --dry-run resolves models and returns without running inference.

        Verified by mocking the ContextTester so that no network calls are
        made, then asserting that the inference entry points are never called.
        """
        registry = _make_registry(tmp_path)
        # Reset the model so it appears in the "to test" list
        model = registry.find_model("test-model")
        assert model is not None
        model.context_test_status = ContextTestStatus.UNTESTED

        with (
            patch("lmstrix.api.main.load_model_registry", return_value=registry),
            patch("lmstrix.api.main.ContextTester") as mock_tester_cls,
        ):
            mock_tester = Mock()
            mock_tester._is_embedding_model.return_value = False
            mock_tester_cls.return_value = mock_tester

            cli = LMStrixCLI()
            cli.test(model_id="test-model", dry_run=True)

        # The real inference entry points must not have been called
        mock_tester.test_model.assert_not_called()
        mock_tester.test_all_models.assert_not_called()


# ---------------------------------------------------------------------------
# Live-server tests (skipped in CI when LM Studio is unavailable)
# ---------------------------------------------------------------------------


class TestCLILiveIntegration:
    """Integration tests that require a running LM Studio instance."""

    @pytest.mark.integration
    def test_scan_connects_to_lmstudio(self, lmstudio_server: None) -> None:
        """scan command completes without raising when LM Studio is running."""
        cli = LMStrixCLI()
        cli.scan()
