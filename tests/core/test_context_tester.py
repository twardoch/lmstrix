# tests/core/test_context_tester.py
import pytest
from unittest.mock import MagicMock, patch
from lmstrix.core.context_tester import ContextTester, TestPattern
from lmstrix.core.models import Model

# Mock the LmsClient to avoid actual model loading
@pytest.fixture
def mock_lms_client():
    client = MagicMock()
    client.get_model.return_value.load.return_value.__enter__.return_value = client
    return client

@pytest.fixture
def model_instance():
    """Provides a basic Model instance for testing."""
    return Model(
        id="test-model",
        path="/fake/path/to/test-model.gguf",
        name="test-model.gguf"
    )

def mock_inference_logic(succeed_above_context: int):
    """
    Factory to create a mock inference function that fails above a certain
    context size.
    """
    def infer_mock(prompt: str, **kwargs):
        # Simulate failure based on prompt length (as a proxy for context size)
        if len(prompt) > succeed_above_context:
            raise Exception("Inference failed due to large context")
        
        # Simulate a valid generator response for success cases
        def response_generator():
            yield "response"
        return response_generator()
    return infer_mock

@patch('lmstrix.core.context_tester.LmsClient')
def test_binary_search_finds_correct_midpoint(mock_client_class, model_instance):
    """
    Test that binary search correctly identifies the highest passing context size.
    """
    # Arrange
    mock_lms_client = mock_client_class.return_value
    
    # Simulate inference failing for any context > 4096
    mock_lms_client.infer = mock_inference_logic(succeed_above_context=4096)
    
    tester = ContextTester(model=model_instance, client=mock_lms_client)

    # Act
    result = tester.test(
        start_context=1024,
        max_context=8192,
        pattern=TestPattern.BINARY
    )

    # Assert
    # The binary search should identify 4096 as the highest working context
    assert result == 4096

@patch('lmstrix.core.context_tester.LmsClient')
def test_model_never_loads(mock_client_class, model_instance):
    """
    Test that the tester handles a model that always fails to load.
    """
    # Arrange
    mock_lms_client = mock_client_class.return_value
    mock_lms_client.load_model.side_effect = Exception("Failed to load model")
    
    tester = ContextTester(model=model_instance, client=mock_lms_client)

    # Act & Assert
    with pytest.raises(Exception, match="Failed to load model"):
        tester.test(max_context=4096)

@patch('lmstrix.core.context_tester.LmsClient')
def test_inference_always_fails(mock_client_class, model_instance):
    """
    Test behavior when inference fails even at the smallest context size.
    """
    # Arrange
    mock_lms_client = mock_client_class.return_value
    mock_lms_client.infer.side_effect = Exception("Inference always fails")
    
    tester = ContextTester(model=model_instance, client=mock_lms_client)

    # Act
    result = tester.test(start_context=1024, max_context=8192)

    # Assert
    # Should return the context size just below the first one tested
    assert result == 1023

@patch('lmstrix.core.context_tester.LmsClient')
def test_model_works_at_all_sizes(mock_client_class, model_instance):
    """
    Test that if the model works at max_context, it returns max_context.
    """
    # Arrange
    mock_lms_client = mock_client_class.return_value
    # Mock inference to always succeed
    mock_lms_client.infer = mock_inference_logic(succeed_above_context=10000)
    
    tester = ContextTester(model=model_instance, client=mock_lms_client)

    # Act
    result = tester.test(start_context=1024, max_context=8192)

    # Assert
    assert result == 8192

@patch('lmstrix.core.context_tester.LmsClient')
def test_linear_search_pattern(mock_client_class, model_instance):
    """
    Test the linear search pattern to ensure it steps correctly.
    """
    # Arrange
    mock_lms_client = mock_client_class.return_value
    # Fail inference above 3000 tokens
    mock_lms_client.infer = mock_inference_logic(succeed_above_context=3000)
    
    tester = ContextTester(model=model_instance, client=mock_lms_client)

    # Act
    result = tester.test(
        start_context=1024,
        max_context=4096,
        step=1024,
        pattern=TestPattern.LINEAR
    )

    # Assert
    # It should pass at 1024, 2048, but fail at 3072.
    # The highest passing value is 2048.
    assert result == 2048