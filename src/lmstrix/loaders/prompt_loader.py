"""Prompt loading functionality."""

from pathlib import Path
from typing import Any

try:
    # Use tomllib (Python 3.11+) directly
    import tomllib
except ImportError:
    # Fall back to tomli for older Python versions
    import tomli as tomllib

from loguru import logger
from topl.core import resolve_placeholders

from lmstrix.api.exceptions import ConfigurationError
from lmstrix.core.prompts import PromptResolver, ResolvedPrompt


def load_prompts(
    toml_path: Path,
    resolver: PromptResolver | None = None,
    verbose: bool = False,
    **params: str,
) -> dict[str, ResolvedPrompt]:
    """Load and resolve prompts from a TOML file.

    Args:
        toml_path: Path to the TOML file containing prompts.
        resolver: PromptResolver instance. If None, creates a default resolver.
        verbose: Enable verbose logging.
        **params: External parameters for placeholder resolution.

    Returns:
        Dictionary mapping prompt names to ResolvedPrompt objects.

    Raises:
        ConfigurationError: If the TOML file cannot be loaded or parsed.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    # Check if file exists
    if not toml_path.exists():
        raise ConfigurationError(
            "prompts_file",
            f"Prompts file not found: {toml_path}",
            {"path": str(toml_path)},
        )

    # Load TOML data using tomllib
    try:
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        logger.info(f"Loaded prompts from {toml_path}")
    except Exception as e:
        raise ConfigurationError(
            "prompts_file",
            f"Failed to load TOML file: {e}",
            {"path": str(toml_path), "error": str(e)},
        ) from e

    # Resolve placeholders with TOPL if parameters provided
    if params:
        try:
            resolved_data = resolve_placeholders(data, **params)
            # Convert back to dict
            data = dict(resolved_data)
            logger.info("Resolved placeholders with TOPL")
        except Exception as e:
            logger.warning(f"TOPL placeholder resolution failed: {e}")
            # Continue with unresolved data

    # Create resolver if not provided
    if resolver is None:
        resolver = PromptResolver(verbose=verbose)

    # Resolve all prompts
    resolved_prompts = resolver.resolve_all_prompts(data, **params)

    logger.info(f"Resolved {len(resolved_prompts)} prompts")
    if params:
        logger.info(f"Applied parameters: {list(params.keys())}")

    return resolved_prompts


def load_single_prompt(
    toml_path: Path,
    prompt_name: str,
    resolver: PromptResolver | None = None,
    verbose: bool = False,
    **params: str,
) -> ResolvedPrompt:
    """Load and resolve a single prompt from a TOML file.

    Args:
        toml_path: Path to the TOML file containing prompts.
        prompt_name: Name of the prompt to load.
        resolver: PromptResolver instance. If None, creates a default resolver.
        verbose: Enable verbose logging.
        **params: External parameters for placeholder resolution.

    Returns:
        ResolvedPrompt object.

    Raises:
        ConfigurationError: If the prompt cannot be found or resolved.
    """
    if verbose:
        logger.enable("lmstrix")
    else:
        logger.disable("lmstrix")

    # Check if file exists
    if not toml_path.exists():
        raise ConfigurationError(
            "prompts_file",
            f"Prompts file not found: {toml_path}",
            {"path": str(toml_path)},
        )

    # Load TOML data using tomllib
    try:
        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        logger.info(f"Loaded prompts from {toml_path}")
    except Exception as e:
        raise ConfigurationError(
            "prompts_file",
            f"Failed to load TOML file: {e}",
            {"path": str(toml_path), "error": str(e)},
        ) from e

    # Resolve placeholders with TOPL if parameters provided
    if params:
        try:
            resolved_data = resolve_placeholders(data, **params)
            # Convert back to dict
            data = dict(resolved_data)
            logger.info("Resolved placeholders with TOPL")
        except Exception as e:
            logger.warning(f"TOPL placeholder resolution failed: {e}")
            # Continue with unresolved data

    # Create resolver if not provided
    if resolver is None:
        resolver = PromptResolver(verbose=verbose)

    # Resolve the specific prompt
    resolved = resolver.resolve_prompt(prompt_name, data, **params)

    logger.info(f"Resolved prompt '{prompt_name}'")
    if resolved.placeholders_unresolved:
        logger.warning(
            f"Unresolved placeholders in '{prompt_name}': {resolved.placeholders_unresolved}",
        )

    return resolved


def save_prompts(
    prompts: dict[str, Any],
    toml_path: Path,
) -> None:
    """Save prompts to a TOML file.

    Args:
        prompts: Dictionary of prompts to save.
        toml_path: Path where to save the TOML file.
    """
    # We need toml-w or tomlkit for writing
    try:
        import tomli_w

        writer = tomli_w
    except ImportError:
        try:
            import tomlkit

            writer = tomlkit
        except ImportError:
            # Fall back to old toml if needed
            import toml

            writer = toml

    # Ensure parent directory exists
    toml_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to TOML
    with toml_path.open("w") as f:
        if hasattr(writer, "dump"):
            writer.dump(prompts, f)
        else:
            # tomli_w uses dumps
            f.write(writer.dumps(prompts))

    logger.info(f"Saved {len(prompts)} prompts to {toml_path}")
