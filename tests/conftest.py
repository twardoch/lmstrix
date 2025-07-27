"""Pytest configuration and shared fixtures."""

import asyncio
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Add the src directory to the path so we can import lmstrix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_lmstudio_client() -> Mock:
    """Mock LMStudioClient for testing."""
    client = Mock()
    client.list_models.return_value = [
        {
            "id": "test-model-1",
            "path": "/path/to/model1.gguf",
            "size_bytes": 1000000,
            "ctx_in": 4096,
            "ctx_out": 4096,
            "has_tools": False,
            "has_vision": False,
        },
        {
            "id": "test-model-2",
            "path": "/path/to/model2.gguf",
            "size_bytes": 2000000,
            "ctx_in": 8192,
            "ctx_out": 4096,
            "has_tools": True,
            "has_vision": True,
        },
    ]
    return client


@pytest.fixture
def mock_llm() -> Mock:
    """Mock LLM object returned by lmstudio.llm()."""
    llm = Mock()
    llm.model_id = "test-model-1"
    return llm


@pytest.fixture
def sample_model_data() -> dict[str, Any]:
    """Sample model data for testing."""
    return {
        "id": "test-model",
        "path": "/path/to/test-model.gguf",
        "size_bytes": 1500000,
        "ctx_in": 4096,
        "ctx_out": 4096,
        "has_tools": False,
        "has_vision": False,
    }


@pytest.fixture
def tmp_models_dir(tmp_path: Path) -> Path:
    """Create a temporary models directory."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    return models_dir


@pytest.fixture
def tmp_registry_file(tmp_path: Path) -> Path:
    """Create a temporary registry file path."""
    return tmp_path / "models_registry.json"


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_completion_response() -> dict[str, Any]:
    """Mock completion response from LM Studio."""
    return {
        "choices": [{"text": "4"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
        "model": "test-model",
    }


@pytest.fixture
def mock_prompt_template() -> dict[str, Any]:
    """Sample prompt template for testing."""
    return {
        "name": "test_prompt",
        "template": "Calculate: {expression}",
        "variables": ["expression"],
        "description": "A test prompt for calculations",
    }


@pytest.fixture
def mock_context_data() -> dict[str, str]:
    """Sample context data for testing."""
    return {
        "expression": "2+2",
        "expected": "4",
    }
