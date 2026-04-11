# this_file: src/lmstrix/api/configs.py

from rich.console import Console

from lmstrix.core.concrete_config import ConcreteConfigManager
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.utils import setup_logging
from lmstrix.utils.logging import logger
from lmstrix.utils.paths import get_lmstudio_path

console = Console()


def save_configs_command(
    flash: bool = False,
    limit: str | int = "100%",
    threshold: int = 0,
    verbose: bool = False,
) -> None:
    setup_logging(verbose=verbose)

    is_percentage = False
    limit_value = 100

    if isinstance(limit, str):
        if limit.endswith("%"):
            is_percentage = True
            try:
                limit_value = int(limit.rstrip("%"))
                if limit_value < 1 or limit_value > 100:
                    logger.error(f"Invalid percentage: {limit}. Must be between 1% and 100%.")
                    return
            except ValueError:
                logger.error(f"Invalid percentage format: {limit}")
                return
        else:
            try:
                limit_value = int(limit)
            except ValueError:
                logger.error(
                    f"Invalid limit value: {limit}. Must be an integer or percentage (e.g., '50%')."
                )
                return
    else:
        limit_value = limit

    registry = load_model_registry(verbose=verbose)
    models_with_context = [m for m in registry.list_models() if m.tested_max_context]

    if not models_with_context:
        logger.debug("No models with tested context limits found.")
        logger.debug("Run 'lmstrix test' to test model context limits first.")
        return

    logger.debug(f"[blue]Found {len(models_with_context)} models with tested context limits[/blue]")

    try:
        lms_path = get_lmstudio_path()
    except Exception as e:
        logger.debug(f"Failed to find LM Studio installation: {e}")
        return

    config_manager = ConcreteConfigManager(lms_path)
    with console.status("Saving concrete configurations..."):
        successful, failed = config_manager.save_all_configs(
            models_with_context,
            enable_flash=flash,
            limit_value=limit_value,
            is_percentage=is_percentage,
            threshold=threshold,
        )

    if successful > 0:
        logger.debug(f"[green]✓ Successfully saved {successful} model configurations[/green]")
    if failed > 0:
        logger.debug(f"✗ Failed to save {failed} model configurations")

    if flash:
        gguf_count = sum(1 for m in models_with_context if str(m.path).endswith(".gguf"))
        if gguf_count > 0:
            logger.debug(f"[blue]Flash attention enabled for {gguf_count} GGUF models[/blue]")

    if is_percentage:
        if threshold > 0:
            logger.debug(
                f"[blue]Applied limit: {limit_value}% for contexts > {threshold:,} tokens[/blue]"
            )
        else:
            logger.debug(f"[blue]Applied limit: {limit_value}% to all models[/blue]")
    else:
        logger.debug(
            f"[blue]Applied absolute limit: {limit_value:,} tokens (or tested max if lower)[/blue]"
        )
