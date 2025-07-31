"""Prompt template resolution and management."""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

import tiktoken
from pydantic import BaseModel, Field

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.utils.logging import logger


class ResolvedPrompt(BaseModel):
    """A prompt after placeholder resolution."""

    name: str = Field(..., description="Name of the prompt")
    template: str = Field(..., description="Original template with placeholders")
    resolved: str = Field(..., description="Resolved prompt text")
    tokens: int = Field(0, description="Estimated token count")
    placeholders_found: list[str] = Field(default_factory=list, description="Placeholders found")
    placeholders_resolved: list[str] = Field(
        default_factory=list,
        description="Placeholders resolved",
    )
    placeholders_unresolved: list[str] = Field(
        default_factory=list,
        description="Unresolved placeholders",
    )


class PromptResolver:
    """Handles two-phase placeholder resolution for prompt templates."""

    PLACEHOLDER_RE = re.compile(r"{{([^{}]+)}}")
    MAX_INTERNAL_PASSES = 10  # Prevent infinite loops on circular refs

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the prompt resolver.

        Args:
            verbose: Enable verbose logging.
        """
        self.verbose = verbose
        self.encoder = tiktoken.get_encoding("cl100k_base")

        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def _get_by_path(self, data: dict[str, Any], dotted_path: str) -> Any:
        """Get value at dotted path from nested dict.

        Args:
            data: Nested dictionary.
            dotted_path: Path like "section.subsection.key".

        Returns:
            Value at path or None if not found.
        """
        current = data
        for part in dotted_path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return None
            current = current[part]
        return current

    def _find_placeholders(self, text: str) -> list[str]:
        """Find all placeholders in text.

        Args:
            text: Text to search.

        Returns:
            List of placeholder names (without brackets).
        """
        return [match.group(1).strip() for match in self.PLACEHOLDER_RE.finditer(text)]

    def _resolve_internal_once(self, text: str, root: dict[str, Any]) -> tuple[str, list[str]]:
        """Replace one pass of internal placeholders.

        Args:
            text: Text with placeholders.
            root: Root data dictionary for internal references.

        Returns:
            Tuple of (resolved_text, resolved_placeholders).
        """
        resolved = []

        def repl(match: re.Match[str]) -> str:
            path = match.group(1).strip()
            value = self._get_by_path(root, path)
            if value is not None:
                resolved.append(path)
                # Escape any braces in the resolved value to prevent format string issues
                value_str = str(value)
                return value_str.replace("{", "{{").replace("}", "}}")
            return match.group(0)

        new_text = self.PLACEHOLDER_RE.sub(repl, text)
        return new_text, resolved

    def _resolve_external(self, text: str, params: Mapping[str, str]) -> tuple[str, list[str]]:
        """Replace external placeholders using provided parameters.

        Args:
            text: Text with placeholders.
            params: External parameters.

        Returns:
            Tuple of (resolved_text, resolved_placeholders).
        """
        if not params:
            return text, []

        resolved = []

        class _SafeDict(dict):
            """Dict that leaves unknown placeholders unchanged."""

            def __missing__(self, key: str) -> str:
                return f"{{{key}}}"

        # Instead of converting to Python format strings, do direct replacement
        result = text
        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                resolved.append(key)
                # Replace the placeholder with the value
                result = result.replace(placeholder, str(value))

        return result, resolved

    def resolve_prompt(
        self,
        prompt_name: str,
        prompts_data: dict[str, Any],
        **params: str,
    ) -> ResolvedPrompt:
        """Resolve a single prompt template.

        Args:
            prompt_name: Name of the prompt to resolve.
            prompts_data: Dictionary containing all prompts.
            **params: External parameters for placeholder resolution.

        Returns:
            ResolvedPrompt with resolution details.

        Raises:
            ConfigurationError: If prompt not found or resolution fails.
        """
        # Find the prompt template
        template = self._get_by_path(prompts_data, prompt_name)
        if template is None:
            raise ConfigurationError(
                prompt_name,
                f"Prompt '{prompt_name}' not found in prompts data",
                {"available_prompts": list(prompts_data.keys())},
            )

        if not isinstance(template, str):
            raise ConfigurationError(
                prompt_name,
                f"Prompt '{prompt_name}' is not a string",
                {"type": type(template).__name__},
            )

        # Track resolution process
        all_placeholders = self._find_placeholders(template)
        resolved_placeholders = []
        current_text = template

        # Phase 1: Internal resolution (multiple passes)
        for i in range(self.MAX_INTERNAL_PASSES):
            new_text, resolved = self._resolve_internal_once(current_text, prompts_data)
            resolved_placeholders.extend(resolved)

            if new_text == current_text:
                logger.debug(f"Internal resolution complete after {i + 1} passes")
                break
            current_text = new_text
        else:
            logger.warning(
                f"Reached maximum internal passes ({self.MAX_INTERNAL_PASSES}). "
                "Possible circular placeholder references?",
            )

        # Phase 2: External resolution
        current_text, resolved = self._resolve_external(current_text, MappingProxyType(params))
        resolved_placeholders.extend(resolved)

        # Find unresolved placeholders
        remaining = self._find_placeholders(current_text)

        # Count tokens
        token_count = len(self.encoder.encode(current_text))

        return ResolvedPrompt(
            name=prompt_name,
            template=template,
            resolved=current_text,
            tokens=token_count,
            placeholders_found=all_placeholders,
            placeholders_resolved=list(set(resolved_placeholders)),
            placeholders_unresolved=remaining,
        )

    def resolve_all_prompts(
        self,
        prompts_data: dict[str, Any],
        **params: str,
    ) -> dict[str, ResolvedPrompt]:
        """Resolve all prompts in the data.

        Args:
            prompts_data: Dictionary containing all prompts.
            **params: External parameters for placeholder resolution.

        Returns:
            Dictionary mapping prompt names to ResolvedPrompt objects.
        """
        results = {}

        def process_prompts(data: dict[str, Any], prefix: str = "") -> None:
            for key, value in data.items():
                full_key = f"{prefix}{key}" if prefix else key

                if isinstance(value, str):
                    try:
                        results[full_key] = self.resolve_prompt(full_key, prompts_data, **params)
                    except ConfigurationError as e:
                        logger.error(f"Failed to resolve prompt '{full_key}': {e}")
                elif isinstance(value, dict):
                    # Check if this dict has a 'template' key - if so, treat it as a prompt definition
                    if "template" in value and isinstance(value["template"], str):
                        try:
                            results[full_key] = self.resolve_prompt(
                                f"{full_key}.template",
                                prompts_data,
                                **params,
                            )
                        except ConfigurationError as e:
                            logger.error(f"Failed to resolve prompt '{full_key}': {e}")
                    else:
                        # Otherwise recurse into the dict
                        process_prompts(value, f"{full_key}.")

        process_prompts(prompts_data)
        return results

    def truncate_to_limit(
        self,
        text: str,
        limit: int,
        strategy: str = "end",
    ) -> str:
        """Truncate text to fit within token limit.

        Args:
            text: Text to truncate.
            limit: Maximum token count.
            strategy: Truncation strategy ('end', 'start', 'middle').

        Returns:
            Truncated text.
        """
        tokens = self.encoder.encode(text)

        if len(tokens) <= limit:
            return text

        if strategy == "start":
            truncated_tokens = tokens[-limit:]
        elif strategy == "middle":
            # Keep start and end
            keep_each = limit // 2
            truncated_tokens = tokens[:keep_each] + tokens[-keep_each:]
        else:  # "end"
            truncated_tokens = tokens[:limit]

        return self.encoder.decode(truncated_tokens)

    def inject_context(
        self,
        prompt: str,
        context: str,
        context_placeholder: str = "{{text}}",
        out_ctx: int | None = None,
    ) -> str:
        """Inject context into a prompt, with optional truncation.

        Args:
            prompt: Prompt template with context placeholder.
            context: Context text to inject.
            context_placeholder: Placeholder to replace with context.
            out_ctx: Maximum total tokens (prompt + context).

        Returns:
            Prompt with context injected.
        """
        if context_placeholder not in prompt:
            logger.warning(f"Context placeholder '{context_placeholder}' not found in prompt")
            return prompt

        if out_ctx:
            # Calculate available space for context
            prompt_without_context = prompt.replace(context_placeholder, "")
            prompt_tokens = len(self.encoder.encode(prompt_without_context))
            available_tokens = out_ctx - prompt_tokens - 100  # Safety margin

            if available_tokens > 0:
                context = self.truncate_to_limit(context, available_tokens)

        return prompt.replace(context_placeholder, context)

    def _resolve_phase(
        self,
        template: str,
        context: dict[str, Any],
    ) -> tuple[str, list[str], list[str], list[str]]:
        """Resolve placeholders in a single phase.

        This method is for backward compatibility with tests.

        Args:
            template: Template text with placeholders.
            context: Context dictionary for resolution.

        Returns:
            Tuple of (resolved_text, found_placeholders, resolved_placeholders, unresolved_placeholders).
        """
        # Find all placeholders
        found = self._find_placeholders(template)

        # Try to resolve them
        resolved_text, resolved_list = self._resolve_internal_once(template, context)

        # Find remaining unresolved
        unresolved = self._find_placeholders(resolved_text)

        return resolved_text, found, resolved_list, unresolved

    def resolve_template(
        self,
        name: str,
        template: str,
        prompt_context: dict[str, Any],
        runtime_context: dict[str, Any],
    ) -> ResolvedPrompt:
        """Resolve a template with both prompt and runtime contexts.

        This method is for backward compatibility with tests.

        Args:
            name: Name of the template.
            template: Template text with placeholders.
            prompt_context: Context from prompt data.
            runtime_context: Runtime parameters.

        Returns:
            ResolvedPrompt object.
        """
        # Combine contexts, with runtime taking precedence

        # Create a temporary prompts data structure
        temp_data = {name: template}
        temp_data.update(prompt_context)

        # Use the main resolve_prompt method
        return self.resolve_prompt(name, temp_data, **runtime_context)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for.

        Returns:
            Number of tokens.
        """
        return len(self.encoder.encode(text))
