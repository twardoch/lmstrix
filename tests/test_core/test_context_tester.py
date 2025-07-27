"""Tests for context testing functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import NoReturn
from unittest.mock import AsyncMock, Mock, patch

import pytest

from lmstrix.api.exceptions import InferenceError, ModelLoadError
from lmstrix.core.context_tester import ContextTester, ContextTestResult
from lmstrix.core.models import ContextTestStatus, Model


class TestContextTestResult:
    """Test ContextTestResult class."""

    def test_result_creation_minimal(self: "TestContextTestResult") -> None:
        """Test creating a minimal test result."""
        result = ContextTestResult(
            context_size=4096,
            load_success=True,
        )

        assert result.context_size == 4096
        assert result.load_success is True
        assert result.inference_success is False
        assert result.prompt == ""
        assert result.response == ""
        assert result.error == ""
        assert isinstance(result.timestamp, datetime)

    def test_result_creation_full(self: "TestContextTestResult") -> None:
        """Test creating a full test result."""
        result = ContextTestResult(
            context_size=8192,
            load_success=True,
            inference_success=True,
            prompt="2+2=",
            response="4",
            error="",
        )

        assert result.context_size == 8192
        assert result.load_success is True
        assert result.inference_success is True
        assert result.prompt == "2+2="
        assert result.response == "4"
        assert result.error == ""

    def test_result_with_error(self: "TestContextTestResult") -> None:
        """Test result with error."""
        result = ContextTestResult(
            context_size=16384,
            load_success=False,
            error="Out of memory",
        )

        assert result.load_success is False
        assert result.inference_success is False
        assert result.error == "Out of memory"

    def test_result_to_dict(self: "TestContextTestResult") -> None:
        """Test converting result to dictionary."""
        result = ContextTestResult(
            context_size=4096,
            load_success=True,
            inference_success=True,
            prompt="test prompt",
            response="test response",
        )

        result_dict = result.to_dict()

        assert result_dict["context_size"] == 4096
        assert result_dict["load_success"] is True
        assert result_dict["inference_success"] is True
        assert result_dict["prompt"] == "test prompt"
        assert result_dict["response"] == "test response"
        assert result_dict["error"] == ""
        assert "timestamp" in result_dict

    def test_is_valid_response(self: "TestContextTestResult") -> None:
        """Test response validation."""
        result = ContextTestResult(
            context_size=4096,
            load_success=True,
            response="4",
        )

        assert result.is_valid_response("4") is True
        assert result.is_valid_response(" 4 ") is True  # Strips whitespace
        assert result.is_valid_response("5") is False
        assert result.is_valid_response("") is False


class TestContextTester:
    """Test ContextTester class."""

    def test_tester_initialization(self: "TestContextTester", mock_lmstudio_client: Mock) -> None:
        """Test context tester initialization."""
        tester = ContextTester(mock_lmstudio_client)

        assert tester.client == mock_lmstudio_client
        assert tester.test_prompt == "2+2="
        assert tester.expected_response == "4"
        assert tester.filler_char == "."

    def test_tester_default_client(self: "TestContextTester") -> None:
        """Test tester creates default client if none provided."""
        with patch("lmstrix.core.context_tester.LMStudioClient") as mock_client_class:
            tester = ContextTester()
            mock_client_class.assert_called_once()
            assert tester.client == mock_client_class.return_value

    def test_generate_test_prompt(self: "TestContextTester") -> None:
        """Test test prompt generation."""
        tester = ContextTester()

        # Test small context
        prompt = tester._generate_test_prompt(100)
        assert tester.test_prompt in prompt
        assert len(prompt) < 100  # Should be smaller due to test prompt

        # Test exact size
        prompt = tester._generate_test_prompt(10)
        assert prompt == "......" + tester.test_prompt  # 6 dots + 4 chars = 10

    def test_estimate_tokens(self: "TestContextTester") -> None:
        """Test token estimation."""
        tester = ContextTester()

        # Rough estimation: ~4 chars per token
        assert 20 <= tester._estimate_tokens("This is a test prompt") <= 30
        assert 2 <= tester._estimate_tokens("Hello") <= 5
        assert tester._estimate_tokens("") == 0

    @pytest.mark.asyncio
    async def test_test_context_load_failure(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
    ) -> None:
        """Test context testing when model fails to load."""
        mock_lmstudio_client.load_model.side_effect = ModelLoadError("test-model", "OOM")

        tester = ContextTester(mock_lmstudio_client)
        result = await tester._test_context("test-model", 8192)

        assert result.context_size == 8192
        assert result.load_success is False
        assert result.inference_success is False
        assert "OOM" in result.error

    @pytest.mark.asyncio
    async def test_test_context_inference_failure(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
    ) -> None:
        """Test context testing when inference fails."""
        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_lmstudio_client.acompletion = AsyncMock(
            side_effect=InferenceError("test-model", "Context too long"),
        )

        tester = ContextTester(mock_lmstudio_client)
        result = await tester._test_context("test-model", 8192)

        assert result.load_success is True
        assert result.inference_success is False
        assert "Context too long" in result.error

    @pytest.mark.asyncio
    async def test_test_context_success(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
    ) -> None:
        """Test successful context testing."""
        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="4")
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        tester = ContextTester(mock_lmstudio_client)
        result = await tester._test_context("test-model", 4096)

        assert result.load_success is True
        assert result.inference_success is True
        assert result.response == "4"
        assert result.error == ""

        # Verify the prompt was generated correctly
        call_args = mock_lmstudio_client.acompletion.call_args
        prompt = call_args[0][1]  # Second positional argument
        assert "2+2=" in prompt

    @pytest.mark.asyncio
    async def test_test_context_invalid_response(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
    ) -> None:
        """Test context testing with invalid response."""
        mock_lmstudio_client.load_model.return_value = mock_llm
        mock_response = Mock(content="5")  # Wrong answer
        mock_lmstudio_client.acompletion = AsyncMock(return_value=mock_response)

        tester = ContextTester(mock_lmstudio_client)
        result = await tester._test_context("test-model", 4096)

        assert result.load_success is True
        assert result.inference_success is True
        assert result.response == "5"
        # Note: is_valid_response check is done at a higher level

    @pytest.mark.asyncio
    async def test_find_optimal_context_simple(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
    ) -> None:
        """Test finding optimal context with simple scenario."""
        mock_lmstudio_client.load_model.return_value = mock_llm

        # Mock responses: succeed up to 4096, fail above
        async def mock_completion(llm: Mock, prompt: str, **kwargs: dict) -> Mock:
            if len(prompt) <= 4096:
                return Mock(content="4")
            raise InferenceError("test-model", "Too long")

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=mock_completion)

        tester = ContextTester(mock_lmstudio_client)

        # Create a model with higher declared limit
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal_size, loadable_size, test_log = await tester.find_optimal_context(model)

        # Should find that 4096 works but higher doesn't
        assert 3000 < optimal_size <= 4096
        assert loadable_size > optimal_size
        assert len(test_log) > 0

    @pytest.mark.asyncio
    async def test_save_test_log(self: "TestContextTester", tmp_path: Path) -> None:
        """Test saving test log to file."""
        tester = ContextTester()

        test_results = [
            ContextTestResult(4096, True, True, "test", "4"),
            ContextTestResult(8192, True, False, "test2", "", "Failed"),
        ]

        log_file = tmp_path / "test_log.json"
        tester._save_test_log(test_results, log_file)

        assert log_file.exists()

        # Load and verify
        data = json.loads(log_file.read_text())
        assert len(data) == 2
        assert data[0]["context_size"] == 4096
        assert data[0]["inference_success"] is True
        assert data[1]["context_size"] == 8192
        assert data[1]["inference_success"] is False

    @pytest.mark.asyncio
    async def test_optimize_model_integration(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
        tmp_path: Path,
    ) -> None:
        """Test full model optimization workflow."""
        mock_lmstudio_client.load_model.return_value = mock_llm

        # Mock successful inference up to 4096
        async def mock_completion(llm: Mock, prompt: str, **kwargs: dict) -> Mock:
            if len(prompt) <= 4096:
                return Mock(content="4")
            raise InferenceError("test-model", "Too long")

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=mock_completion)

        # Mock registry
        mock_registry = Mock()

        # Create model
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        with patch("lmstrix.core.context_tester.get_context_test_log_path") as mock_get_path:
            mock_get_path.return_value = tmp_path / "test_log.json"

            tester = ContextTester(mock_lmstudio_client)
            updated_model = await tester.optimize_model(model, mock_registry)

        # Verify model was updated
        assert updated_model.tested_max_context is not None
        assert updated_model.tested_max_context <= 4096
        assert updated_model.loadable_max_context >= updated_model.tested_max_context
        assert updated_model.context_test_status == ContextTestStatus.COMPLETED
        assert updated_model.context_test_date is not None
        assert updated_model.context_test_log is not None

        # Verify registry was called
        mock_registry.update_model.assert_called_once_with("test-model", updated_model)

    @pytest.mark.asyncio
    async def test_optimize_model_failure(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
    ) -> None:
        """Test model optimization when all tests fail."""
        # Mock all loads failing
        mock_lmstudio_client.load_model.side_effect = ModelLoadError("test-model", "Cannot load")

        mock_registry = Mock()
        model = Model(
            id="test-model",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        tester = ContextTester(mock_lmstudio_client)
        updated_model = await tester.optimize_model(model, mock_registry)

        # Should mark as failed
        assert updated_model.context_test_status == ContextTestStatus.FAILED
        assert updated_model.tested_max_context is None
        assert updated_model.loadable_max_context is None

        mock_registry.update_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_binary_search_logic(
        self: "TestContextTester",
        mock_lmstudio_client: Mock,
        mock_llm: Mock,
    ) -> None:
        """Test binary search algorithm with various edge cases."""
        mock_lmstudio_client.load_model.return_value = mock_llm

        # Test Case 1: Model works at all sizes
        async def always_works(llm: Mock, prompt: str, **kwargs: dict) -> Mock:
            return Mock(content="4")

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=always_works)
        tester = ContextTester(mock_lmstudio_client)

        model = Model(
            id="test-model-1",
            path="/path/to/model.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal, loadable, log = await tester.find_optimal_context(model)
        assert optimal >= 7000  # Should find close to max
        assert loadable == 8192

        # Test Case 2: Model never works
        async def never_works(llm: Mock, prompt: str, **kwargs: dict) -> NoReturn:
            raise InferenceError("test-model", "Always fails")

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=never_works)

        model2 = Model(
            id="test-model-2",
            path="/path/to/model2.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal2, loadable2, log2 = await tester.find_optimal_context(model2)
        assert optimal2 == 0  # Should return 0 when nothing works
        assert loadable2 == 8192

        # Test Case 3: Model loads but never passes inference
        mock_lmstudio_client.load_model.return_value = mock_llm

        async def loads_but_fails_inference(llm: Mock, prompt: str, **kwargs: dict) -> Mock:
            return Mock(content="wrong answer")  # Never returns "4"

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=loads_but_fails_inference)

        model3 = Model(
            id="test-model-3",
            path="/path/to/model3.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal3, loadable3, log3 = await tester.find_optimal_context(model3)
        assert optimal3 == 0  # Should return 0 when no valid responses
        assert loadable3 == 8192

        # Test Case 4: Model works up to exactly 2048
        async def works_up_to_2048(llm: Mock, prompt: str, **kwargs: dict) -> Mock:
            if len(prompt) <= 2048:
                return Mock(content="4")
            raise InferenceError("test-model", "Too long")

        mock_lmstudio_client.acompletion = AsyncMock(side_effect=works_up_to_2048)

        model4 = Model(
            id="test-model-4",
            path="/path/to/model4.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal4, loadable4, log4 = await tester.find_optimal_context(model4)
        assert 1800 <= optimal4 <= 2048  # Should find close to 2048
        assert loadable4 > optimal4

        # Test Case 5: Model that never loads
        mock_lmstudio_client.load_model.side_effect = ModelLoadError("test-model", "Cannot load")

        model5 = Model(
            id="test-model-5",
            path="/path/to/model5.gguf",
            size_bytes=1000000,
            ctx_in=8192,
        )

        optimal5, loadable5, log5 = await tester.find_optimal_context(model5)
        assert optimal5 == 0
        assert loadable5 == 0  # Cannot load at any size
