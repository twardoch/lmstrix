# this_file: src/lmstrix/api/listing.py

import json

from rich.console import Console
from rich.table import Table

from lmstrix.core.describer import (
    filter_models_by_keywords,
    format_models_markdown,
    sort_models_by_keywords,
)
from lmstrix.core.models import ModelRegistry
from lmstrix.loaders.model_loader import load_model_registry, scan_and_update_registry
from lmstrix.utils import setup_logging
from lmstrix.utils.logging import logger

console = Console(width=160)


def _format_capabilities(model) -> str:
    """Format model capabilities for terminal output."""
    labels = []
    if model.has_vision:
        labels.append("vision")
    if model.has_tools:
        labels.append("tools")
    if getattr(model, "has_reasoning", False):
        labels.append("reasoning")
    return ", ".join(labels) if labels else "-"


def list_models_command(
    sort: str = "id",
    show: str | None = None,
    key: str | None = None,
    verbose: bool = False,
    registry: ModelRegistry | None = None,
) -> None:
    setup_logging(verbose=verbose)

    if registry is None:
        try:
            registry = scan_and_update_registry(verbose=verbose)
        except Exception:
            registry = load_model_registry(verbose=verbose)
    models = registry.list_models()

    if not models:
        logger.debug("No models found. Run 'lmstrix scan' to discover models.")
        return

    if key:
        keywords = [k.strip() for k in key.split(",") if k.strip()]
        models = filter_models_by_keywords(models, keywords)
        if not models:
            console.print(f"[yellow]No models match keywords: {', '.join(keywords)}[/yellow]")
            return

    sort_key = sort.lower()
    reverse = sort_key.endswith("d") and len(sort_key) > 1

    if sort_key in ("arch", "archd", "inp", "inpd", "outp", "outpd", "proc", "procd"):
        sorted_models = sort_models_by_keywords(models, sort_key)
    elif sort_key in ("id", "idd"):
        sorted_models = sorted(models, key=lambda m: m.id, reverse=reverse)
    elif sort_key in ("ctx", "ctxd"):
        sorted_models = sorted(models, key=lambda m: m.tested_max_context or 0, reverse=reverse)
    elif sort_key in ("dtx", "dtxd"):
        sorted_models = sorted(models, key=lambda m: m.context_limit, reverse=reverse)
    elif sort_key in ("size", "sized"):
        sorted_models = sorted(models, key=lambda m: m.size, reverse=reverse)
    elif sort_key in ("smart", "smartd"):
        sorted_models = sorted(
            models,
            key=lambda m: (
                (m.tps or 0) * 2000
                + (m.tested_max_context or 0)
                + m.context_limit
                + (m.size / (1024 * 1024)) * 500
            ),
            reverse=reverse,
        )
    elif sort_key in ("ttft", "ttftd"):
        sorted_models = sorted(models, key=lambda m: m.ttft_seconds or 0, reverse=reverse)
    elif sort_key in ("tps", "tpsd"):
        sorted_models = sorted(models, key=lambda m: m.tps or 0, reverse=reverse)
    else:
        logger.debug(f"Invalid sort option: {sort}. Using default (id).")
        sorted_models = sorted(models, key=lambda m: m.id)

    if show:
        if show in {"id", "path"}:
            for model in sorted_models:
                print(model.id)
        elif show == "json":
            print(json.dumps([model.to_dict() for model in sorted_models], indent=2))
        elif show == "md":
            print(format_models_markdown(sorted_models))
        else:
            logger.debug(f"Invalid show option: {show}. Options: id, path, json, md.")
        return

    table = Table(show_lines=False, box=None, expand=True)
    table.add_column("Model ID", style="cyan", no_wrap=False)
    table.add_column("Size(GB)", style="magenta")
    table.add_column("Declared", style="yellow")
    table.add_column("Tested", style="green")
    table.add_column("Good", style="green")
    table.add_column("Bad", style="red")
    table.add_column("TTFT", justify="right", style="blue")
    table.add_column("TPS", justify="right", style="blue")
    table.add_column("Capabilities", style="cyan", no_wrap=False)
    table.add_column("Status", style="blue")

    for model in sorted_models:
        tested_ctx = f"{model.tested_max_context:,}" if model.tested_max_context else "-"
        last_good = f"{model.last_known_good_context:,}" if model.last_known_good_context else "-"
        last_bad = f"{model.last_known_bad_context:,}" if model.last_known_bad_context else "-"
        ttft_str = f"{model.ttft_seconds:.2f}s" if model.ttft_seconds is not None else "-"
        tps_str = f"{model.tps:.1f}" if model.tps is not None else "-"

        status_map = {
            "untested": "Untested",
            "testing": "Testing...",
            "completed": "[green]✓ Tested[/green]",
            "failed": "✗ Failed",
        }
        status = status_map.get(model.context_test_status.value, "Unknown")

        table.add_row(
            model.id,
            f"{model.size / (1024**3):.2f}" if model.size else "N/A",
            f"{model.context_limit:,}",
            tested_ctx,
            last_good,
            last_bad,
            ttft_str,
            tps_str,
            _format_capabilities(model),
            status,
        )
    console.print(table)
