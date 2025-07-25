"""Tests for prompt loader functionality."""

import pytest
import toml

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.core.prompts import PromptResolver, ResolvedPrompt
from lmstrix.loaders.prompt_loader import load_prompt_file, load_prompts


class TestPromptLoader:
    """Test prompt loading functions."""

    def test_load_prompts_simple(self, tmp_path) -> None:
        """Test loading simple prompts from TOML file."""
        # Create test TOML file
        toml_file = tmp_path / "prompts.toml"
        toml_content = {
            "greeting": {
                "template": "Hello {{name}}!",
                "description": "A simple greeting",
            },
            "question": {
                "template": "{{query}} Please provide a detailed answer.",
                "description": "Question template",
            },
        }
        toml_file.write_text(toml.dumps(toml_content))

        # Load prompts
        prompts = load_prompts(toml_file, verbose=True, name="World", query="What is Python?")

        assert len(prompts) == 2
        assert "greeting" in prompts
        assert "question" in prompts

        # Check resolved prompts
        greeting = prompts["greeting"]
        assert isinstance(greeting, ResolvedPrompt)
        assert greeting.name == "greeting"
        assert greeting.template == "Hello {{name}}!"
        assert greeting.resolved == "Hello World!"
        assert greeting.placeholders_resolved == ["name"]

        question = prompts["question"]
        assert question.resolved == "What is Python? Please provide a detailed answer."

    def test_load_prompts_nonexistent_file(self, tmp_path) -> None:
        """Test loading prompts from non-existent file."""
        nonexistent = tmp_path / "does_not_exist.toml"

        with pytest.raises(ConfigurationError) as exc_info:
            load_prompts(nonexistent)

        assert "not found" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    def test_load_prompts_invalid_toml(self, tmp_path) -> None:
        """Test loading prompts from invalid TOML file."""
        invalid_file = tmp_path / "invalid.toml"
        invalid_file.write_text("This is not valid TOML { syntax")

        with pytest.raises(ConfigurationError) as exc_info:
            load_prompts(invalid_file)

        assert "parse" in str(exc_info.value).lower()

    def test_load_prompts_with_nested_placeholders(self, tmp_path) -> None:
        """Test loading prompts with nested placeholders."""
        toml_file = tmp_path / "nested.toml"
        toml_content = {
            "base": {
                "template": "{{prefix}}: {{content}}",
            },
            "prefix": {
                "template": "Important",
            },
            "final": {
                "template": "{{base}}",
            },
        }
        toml_file.write_text(toml.dumps(toml_content))

        prompts = load_prompts(toml_file, content="Test message")

        # Check that nested resolution worked
        final = prompts["final"]
        assert final.resolved == "Important: Test message"
        assert set(final.placeholders_found) == {"base"}
        assert set(final.placeholders_resolved) == {"base"}

    def test_load_prompts_with_missing_params(self, tmp_path) -> None:
        """Test loading prompts with missing parameters."""
        toml_file = tmp_path / "missing.toml"
        toml_content = {
            "template1": {
                "template": "Hello {{name}} from {{city}}!",
            },
        }
        toml_file.write_text(toml.dumps(toml_content))

        # Load with only partial params
        prompts = load_prompts(toml_file, name="Alice")

        template1 = prompts["template1"]
        assert template1.resolved == "Hello Alice from {{city}}!"
        assert template1.placeholders_unresolved == ["city"]
        assert template1.placeholders_resolved == ["name"]

    def test_load_prompts_with_custom_resolver(self, tmp_path) -> None:
        """Test loading prompts with custom resolver."""
        toml_file = tmp_path / "custom.toml"
        toml_content = {
            "test": {
                "template": "Result: {{value}}",
            },
        }
        toml_file.write_text(toml.dumps(toml_content))

        # Create custom resolver
        custom_resolver = PromptResolver(verbose=True)

        prompts = load_prompts(toml_file, resolver=custom_resolver, value="42")

        assert prompts["test"].resolved == "Result: 42"

    def test_load_prompts_empty_file(self, tmp_path) -> None:
        """Test loading prompts from empty TOML file."""
        empty_file = tmp_path / "empty.toml"
        empty_file.write_text("")

        prompts = load_prompts(empty_file)

        assert len(prompts) == 0

    def test_load_prompt_file_simple(self, tmp_path) -> None:
        """Test loading a single prompt file."""
        prompt_file = tmp_path / "single_prompt.toml"
        toml_content = {
            "template": "Analyze this {{language}} code: {{code}}",
            "description": "Code analysis prompt",
            "metadata": {
                "version": "1.0",
                "author": "test",
            },
        }
        prompt_file.write_text(toml.dumps(toml_content))

        # Load single prompt
        prompt = load_prompt_file(
            prompt_file,
            name="code_analysis",
            language="Python",
            code="def hello(): pass",
        )

        assert isinstance(prompt, ResolvedPrompt)
        assert prompt.name == "code_analysis"
        assert prompt.template == "Analyze this {{language}} code: {{code}}"
        assert prompt.resolved == "Analyze this Python code: def hello(): pass"
        assert set(prompt.placeholders_resolved) == {"language", "code"}

    def test_load_prompt_file_missing_template(self, tmp_path) -> None:
        """Test loading prompt file without template field."""
        prompt_file = tmp_path / "no_template.toml"
        toml_content = {
            "description": "Missing template",
            "metadata": {"version": "1.0"},
        }
        prompt_file.write_text(toml.dumps(toml_content))

        with pytest.raises(ConfigurationError) as exc_info:
            load_prompt_file(prompt_file, name="test")

        assert "template" in str(exc_info.value).lower()

    def test_load_prompt_file_with_defaults(self, tmp_path) -> None:
        """Test loading prompt file with default values."""
        prompt_file = tmp_path / "defaults.toml"
        toml_content = {
            "template": "Model: {{model}}, Temperature: {{temperature}}",
            "defaults": {
                "model": "gpt-4",
                "temperature": "0.7",
            },
        }
        prompt_file.write_text(toml.dumps(toml_content))

        # Load without providing params - should use defaults
        prompt = load_prompt_file(prompt_file, name="test")

        assert prompt.resolved == "Model: gpt-4, Temperature: 0.7"

        # Load with partial params - should override defaults
        prompt2 = load_prompt_file(prompt_file, name="test", model="claude")

        assert prompt2.resolved == "Model: claude, Temperature: 0.7"
