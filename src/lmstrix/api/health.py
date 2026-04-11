# this_file: src/lmstrix/api/health.py

import json
from datetime import datetime

from lmstrix.api.exceptions import ModelRegistryError
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.utils import setup_logging
from lmstrix.utils.logging import logger
from lmstrix.utils.paths import get_default_models_file


def check_health_command(verbose: bool = False) -> None:
    setup_logging(verbose=verbose)

    models_file = get_default_models_file()
    logger.debug("[blue]Database Health Check[/blue]")
    logger.info(f"Registry file: {models_file}")

    if not models_file.exists():
        logger.debug("✗ Registry file not found")
        return

    logger.success("✓ Registry file exist")

    try:
        with models_file.open() as f:
            json.load(f)
        logger.success("✓ Registry file is valid JSON")
    except json.JSONDecodeError as e:
        logger.debug(f"✗ Registry file is corrupted: {e}")

    try:
        registry = load_model_registry(verbose=verbose)
        logger.success(f"✓ Successfully loaded {len(registry)} model")

        invalid_models = []
        for model_path, model in registry._models.items():
            if not model.validate_integrity():
                invalid_models.append(model_path)

        if invalid_models:
            logger.debug(f"⚠ Found {len(invalid_models)} models with integrity issues")
            if verbose:
                for model_path in invalid_models:
                    logger.debug(f"  - {model_path}")
        else:
            logger.success("✓ All models pass integrity check")

    except (ModelRegistryError, OSError, json.JSONDecodeError) as e:
        logger.debug(f"✗ Failed to load registry: {e}")

    backup_pattern = f"{models_file.stem}.backup_*"
    backup_files = list(models_file.parent.glob(backup_pattern))

    if not backup_files:
        logger.debug("No backup files found")
        return

    backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    logger.debug(f"[blue]Found {len(backup_files)} backup files:[/blue]")

    for backup_file in backup_files[:5]:
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        size_kb = backup_file.stat().st_size // 1024
        try:
            with backup_file.open() as f:
                json.load(f)
            status = "[green]✓[/green]"
        except json.JSONDecodeError:
            status = "✗"

        logger.debug(
            f"  {status} {backup_file.name} ({size_kb}KB, {mtime.strftime('%Y-%m-%d %H:%M')})"
        )

    if len(backup_files) > 5:
        logger.debug(f"  ... and {len(backup_files) - 5} more")
