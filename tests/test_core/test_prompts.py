"""Tests for prompt template resolution."""

from lmstrix.core.prompts import PromptResolver, ResolvedPrompt


class TestResolvedPrompt:
    """Test ResolvedPrompt model."""

    def test_resolved_prompt_creation(self) -> None:
        """Test creating a resolved prompt."""
        prompt = ResolvedPrompt(
            name="test_prompt",
            template="Hello {{name}}!",
            resolved="Hello World!",
            tokens=10,
            placeholders_found=["name"],
            placeholders_resolved=["name"],
        )

        assert prompt.name == "test_prompt"
        assert prompt.template == "Hello {{name}}!"
        assert prompt.resolved == "Hello World!"
        assert prompt.tokens == 10
        assert prompt.placeholders_found == ["name"]
        assert prompt.placeholders_resolved == ["name"]
        assert prompt.placeholders_unresolved == []

    def test_resolved_prompt_minimal(self) -> None:
        """Test creating resolved prompt with minimal fields."""
        prompt = ResolvedPrompt(
            name="minimal",
            template="Test",
            resolved="Test",
        )

        assert prompt.name == "minimal"
        assert prompt.template == "Test"
        assert prompt.resolved == "Test"
        assert prompt.tokens == 0
        assert prompt.placeholders_found == []
        assert prompt.placeholders_resolved == []
        assert prompt.placeholders_unresolved == []


class TestPromptResolver:
    """Test PromptResolver class."""

    def test_resolver_initialization(self) -> None:
        """Test resolver initialization."""
        resolver = PromptResolver(verbose=True)
        assert resolver.verbose is True
        assert resolver.encoder is not None

        resolver2 = PromptResolver(verbose=False)
        assert resolver2.verbose is False

    def test_find_placeholders(self) -> None:
        """Test finding placeholders in templates."""
        resolver = PromptResolver()

        # Simple placeholders
        placeholders = resolver._find_placeholders("Hello {{name}}!")
        assert placeholders == ["name"]

        # Multiple placeholders
        placeholders = resolver._find_placeholders("{{greeting}} {{name}}, how are {{you}}?")
        assert set(placeholders) == {"greeting", "name", "you"}

        # No placeholders
        placeholders = resolver._find_placeholders("Hello World!")
        assert placeholders == []

        # Nested braces (not placeholders)
        placeholders = resolver._find_placeholders("Code: {function() { return {{x}}; }}")
        assert placeholders == ["x"]

    def test_resolve_phase_simple(self) -> None:
        """Test simple single-phase resolution."""
        resolver = PromptResolver()

        template = "Hello {{name}}!"
        context = {"name": "Alice"}

        resolved, found, resolved_list, unresolved = resolver._resolve_phase(template, context)

        assert resolved == "Hello Alice!"
        assert found == ["name"]
        assert resolved_list == ["name"]
        assert unresolved == []

    def test_resolve_phase_missing_placeholder(self) -> None:
        """Test resolution with missing placeholders."""
        resolver = PromptResolver()

        template = "Hello {{name}} from {{location}}!"
        context = {"name": "Bob"}

        resolved, found, resolved_list, unresolved = resolver._resolve_phase(template, context)

        assert resolved == "Hello Bob from {{location}}!"
        assert set(found) == {"name", "location"}
        assert resolved_list == ["name"]
        assert unresolved == ["location"]

    def test_resolve_phase_extra_context(self) -> None:
        """Test resolution with extra context values."""
        resolver = PromptResolver()

        template = "Hello {{name}}!"
        context = {"name": "Charlie", "age": 25, "location": "NYC"}

        resolved, found, resolved_list, unresolved = resolver._resolve_phase(template, context)

        assert resolved == "Hello Charlie!"
        assert found == ["name"]
        assert resolved_list == ["name"]
        assert unresolved == []

    def test_resolve_template_two_phase(self) -> None:
        """Test two-phase template resolution."""
        resolver = PromptResolver()

        template = "{{greeting}} {{name}}!"
        prompt_context = {"greeting": "Hello"}
        runtime_context = {"name": "David"}

        result = resolver.resolve_template("test", template, prompt_context, runtime_context)

        assert result.name == "test"
        assert result.template == template
        assert result.resolved == "Hello David!"
        assert set(result.placeholders_found) == {"greeting", "name"}
        assert set(result.placeholders_resolved) == {"greeting", "name"}
        assert result.placeholders_unresolved == []
        assert result.tokens > 0

    def test_resolve_template_recursive(self) -> None:
        """Test recursive placeholder resolution."""
        resolver = PromptResolver()

        template = "{{level1}}"
        prompt_context = {
            "level1": "{{level2}} World",
            "level2": "Hello",
        }

        result = resolver.resolve_template("recursive", template, prompt_context, {})

        assert result.resolved == "Hello World"
        assert "level1" in result.placeholders_found
        assert "level1" in result.placeholders_resolved

    def test_resolve_template_circular_reference(self) -> None:
        """Test handling of circular references."""
        resolver = PromptResolver()

        template = "{{a}}"
        prompt_context = {
            "a": "{{b}}",
            "b": "{{a}}",  # Circular reference
        }

        # Should not hang, but will leave placeholders unresolved
        result = resolver.resolve_template("circular", template, prompt_context, {})

        # After max passes, should still have unresolved placeholders
        assert "{{" in result.resolved
        assert len(result.placeholders_unresolved) > 0

    def test_resolve_template_no_placeholders(self) -> None:
        """Test template with no placeholders."""
        resolver = PromptResolver()

        template = "Hello World!"

        result = resolver.resolve_template("static", template, {}, {})

        assert result.resolved == "Hello World!"
        assert result.placeholders_found == []
        assert result.placeholders_resolved == []
        assert result.placeholders_unresolved == []

    def test_resolve_template_numeric_values(self) -> None:
        """Test resolution with numeric values."""
        resolver = PromptResolver()

        template = "The answer is {{number}} and pi is {{pi}}"
        context = {"number": 42, "pi": 3.14159}

        result = resolver.resolve_template("numeric", template, context, {})

        assert result.resolved == "The answer is 42 and pi is 3.14159"
        assert set(result.placeholders_resolved) == {"number", "pi"}

    def test_resolve_template_empty_value(self) -> None:
        """Test resolution with empty string values."""
        resolver = PromptResolver()

        template = "Start{{middle}}End"
        context = {"middle": ""}

        result = resolver.resolve_template("empty", template, context, {})

        assert result.resolved == "StartEnd"
        assert result.placeholders_resolved == ["middle"]

    def test_count_tokens(self) -> None:
        """Test token counting."""
        resolver = PromptResolver()

        # Simple text
        count = resolver._count_tokens("Hello World!")
        assert count > 0
        assert count < 10  # Should be just a few tokens

        # Empty string
        count = resolver._count_tokens("")
        assert count == 0

        # Longer text
        long_text = "The quick brown fox jumps over the lazy dog. " * 10
        count = resolver._count_tokens(long_text)
        assert count > 50  # Should be many tokens

    def test_resolve_with_special_characters(self) -> None:
        """Test resolution with special characters in values."""
        resolver = PromptResolver()

        template = "Code: {{code}}"
        context = {"code": "function() { return {{x}}; }"}

        result = resolver.resolve_template("special", template, context, {})

        assert result.resolved == "Code: function() { return {{x}}; }"
        assert result.placeholders_resolved == ["code"]
        # Note: {{x}} in the value is not treated as a placeholder
