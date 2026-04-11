"""Main API service layer. Hooks up the CLI commands to the underlying core logic."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.table import Table

from lmstrix.api.about import about_command
from lmstrix.api.configs import save_configs_command
from lmstrix.api.describe import describe_models_command
from lmstrix.api.exceptions import APIConnectionError, ModelRegistryError
from lmstrix.api.health import check_health_command
from lmstrix.api.helptext import show_help_command
from lmstrix.api.infer import run_inference_command
from lmstrix.api.listing import list_models_command
from lmstrix.core.context_tester import ContextTester
from lmstrix.core.describer import KEYWORD_VOCAB, filter_models_by_keywords
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.loaders.model_loader import (
    load_model_registry,
    scan_and_update_registry,
)
from lmstrix.utils import get_context_test_log_path, setup_logging
from lmstrix.utils.logging import logger
from lmstrix.utils.paths import get_default_models_file

console = Console()


def _format_response_preview(response: str | None, max_length: int = 60) -> str:
    """Format response text for table display."""
    if not response:
        return "❌"

    # Clean up whitespace and newlines
    cleaned = " ".join(response.strip().split())

    # Truncate if needed
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3] + "..."


def _get_models_to_test(
    registry: ModelRegistry,
    test_all: bool,
    ctx: int | None,
    model_id: str | None,
    reset: bool = False,
    fast_mode: bool = False,
) -> list[Model]:
    """Filter and return a list of models to be tested."""
    tester = ContextTester(
        fast_mode=fast_mode,
    )  # Create a temporary tester for _is_embedding_model

    if not test_all:
        if not model_id:
            logger.error("You must specify a model ID or use the --all flag.")
            return []
        model = registry.find_model(model_id)
        if not model:
            logger.error(f"Model '{model_id}' not found in registry.")
            return []
        if tester._is_embedding_model(model):
            logger.debug(
                f"Error: Model '{model_id}' is an embedding model and cannot be tested as an LLM.",
            )
            return []
        return [model]

    all_models = registry.list_models()
    models_to_test = []
    skipped_embedding = 0

    for m in all_models:
        if tester._is_embedding_model(m):
            skipped_embedding += 1
            continue

        if ctx is not None:
            if not reset and m.context_test_status.value == "completed":
                continue
            if ctx > m.context_limit:
                continue
            if not reset and m.last_known_bad_context and ctx >= m.last_known_bad_context:
                continue
            models_to_test.append(m)
        elif reset or m.context_test_status.value != "completed":
            models_to_test.append(m)

    if skipped_embedding > 0:
        logger.debug(
            f"Excluded {skipped_embedding} embedding models from testing.",
        )

    if not models_to_test:
        if ctx is not None:
            logger.debug(
                "No LLM models found to test at the specified context size.",
            )
            logger.debug(
                "Models may already be tested or context exceeds their limits.",
            )
        elif reset:
            logger.debug(
                "No models found to test (check model availability).",
            )
        else:
            logger.debug(
                "[green]All LLM models have already been successfully tested.[/green]",
            )
    return models_to_test


def _sort_models(models: list[Model], sort_by: str) -> list[Model]:
    """Sort a list of models based on a given key."""
    sort_key = sort_by.lower()
    reverse = sort_key.endswith("d") and len(sort_key) > 1
    key_map = {
        "id": "id",
        "ctx": "tested_max_context",
        "dtx": "context_limit",
        "size": "size",
        "ttft": "ttft_seconds",
        "tps": "tps",
    }
    sort_attr = key_map.get(sort_key.rstrip("d"))

    if not sort_attr:
        logger.debug(f"Invalid sort option: {sort_by}. Using default (id).")
        return sorted(models, key=lambda m: m.id)

    return sorted(models, key=lambda m: getattr(m, sort_attr) or 0, reverse=reverse)


def _test_single_model(
    tester: ContextTester,
    model: Model,
    ctx: int,
    registry: ModelRegistry,
    force: bool = False,
    verbose: bool = False,
) -> None:
    """Test a single model at a specific context size."""
    if ctx > model.context_limit:
        logger.warning(
            f"Warning: Specified context ({ctx:,}) exceeds model's declared limit ({model.context_limit:,}). Skipping test.",
        )
        return

    if model.last_known_bad_context and ctx >= model.last_known_bad_context and not force:
        max_safe_context = int(model.last_known_bad_context * 0.75)
        logger.error(
            f"Error: Specified context ({ctx:,}) is at or above the last known bad context ({model.last_known_bad_context:,}).",
        )
        logger.error(
            f"The maximum safe context to test is {max_safe_context:,} (75% of last bad).",
        )
        logger.error(
            "Use --force to override this safety limit.",
        )
        return
    if model.last_known_bad_context and ctx >= model.last_known_bad_context and force:
        logger.warning(
            f"FORCE MODE: Testing context ({ctx:,}) despite being at/above last known bad context ({model.last_known_bad_context:,}).",
        )

    if verbose:
        logger.info(
            f"\n[bold cyan]Testing model: {model.id} at specific context: {ctx:,}[/bold cyan]",
        )
        logger.info(f"Declared context limit: {model.context_limit:,} tokens")
    else:
        # Compact output - create a live table for testing progress
        table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Context", justify="right", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Response", style="white")

        # Initial row
        table.add_row(
            model.id[:40] + "..." if len(model.id) > 40 else model.id,
            f"{ctx:,}",
            "[blue]Testing...[/blue]",
            "",
        )

        live = Live(table, console=console, refresh_per_second=4)
        live.start()

    log_path = get_context_test_log_path(model.id)

    model.context_test_status = ContextTestStatus.TESTING
    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)

    result = tester._test_at_context(model.id, ctx, log_path, model, registry)

    if result.load_success and result.inference_success:
        # Format response for display
        response_preview = _format_response_preview(result.response)
        if verbose:
            logger.success(f"✓ Test successful at context {ctx:,}")
            logger.debug(f"Response length: {len(result.response)} chars")
            logger.info(f"Response preview: ||{response_preview}||")
        else:
            # Update the table with success
            ttft_str = f"{result.ttft_seconds:.2f}s" if result.ttft_seconds is not None else "-"
            tps_str = f"{result.tps:.1f}" if result.tps is not None else "-"
            table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
            table.add_column("Model", style="cyan", no_wrap=True)
            table.add_column("Context", justify="right", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("TTFT", justify="right", style="blue")
            table.add_column("TPS", justify="right", style="blue")
            table.add_column("Response", style="white")

            table.add_row(
                model.id[:40] + "..." if len(model.id) > 40 else model.id,
                f"{ctx:,}",
                "[green]✓ Success[/green]",
                ttft_str,
                tps_str,
                f"||{response_preview}||",
            )
            live.update(table)
            live.stop()
        model.last_known_good_context = ctx
        if not model.tested_max_context or ctx > model.tested_max_context:
            model.tested_max_context = ctx
        model.context_test_status = ContextTestStatus.COMPLETED
        if result.ttft_seconds is not None:
            model.ttft_seconds = result.ttft_seconds
        if result.tps is not None:
            model.tps = result.tps
    else:
        error_type = "load" if not result.load_success else "inference"
        if verbose:
            logger.error(f"✗ Test failed at context {ctx:,} ({error_type} failed)")
            logger.error(f"Error: {result.error}")
        else:
            # Update the table with failure
            table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
            table.add_column("Model", style="cyan", no_wrap=True)
            table.add_column("Context", justify="right", style="yellow")
            table.add_column("Status", style="red")
            table.add_column("Response", style="white")

            table.add_row(
                model.id[:40] + "..." if len(model.id) > 40 else model.id,
                f"{ctx:,}",
                f"[red]✗ {error_type.capitalize()} failed[/red]",
                "",
            )
            live.update(table)
            live.stop()
        model.last_known_bad_context = ctx
        model.context_test_status = ContextTestStatus.FAILED

    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)


def _test_all_models_at_ctx(
    tester: ContextTester,
    models_to_test: list[Model],
    ctx: int,
    registry: ModelRegistry,
    verbose: bool = False,
) -> list[Model]:
    """Test all models at a specific context size."""
    if verbose:
        logger.debug(
            f"[bold]Testing {len(models_to_test)} models at context size {ctx:,}[/bold]\n",
        )
    else:
        # Compact output - create a live table for testing progress
        table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Context", justify="right", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Response", style="white")
        table.add_column("Progress", justify="right", style="magenta")

        live = Live(table, console=console, refresh_per_second=4)
        live.start()

    updated_models = []
    for i, model in enumerate(models_to_test, 1):
        if verbose:
            logger.info(f"[{i}/{len(models_to_test)}] Testing {model.id}...")
        else:
            # Update table with current model
            table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
            table.add_column("Model", style="cyan", no_wrap=True)
            table.add_column("Context", justify="right", style="yellow")
            table.add_column("Status", style="blue")
            table.add_column("TTFT", justify="right", style="blue")
            table.add_column("TPS", justify="right", style="blue")
            table.add_column("Response", style="white")
            table.add_column("Progress", justify="right", style="magenta")

            # Add previous results
            for j, prev_model in enumerate(updated_models):
                status = (
                    "[green]✓ Success[/green]"
                    if prev_model.last_known_good_context == ctx
                    else "[red]✗ Failed[/red]"
                )
                response_preview = getattr(prev_model, "_test_response_preview", "❌")
                prev_ttft = (
                    f"{prev_model.ttft_seconds:.2f}s"
                    if getattr(prev_model, "ttft_seconds", None) is not None
                    else "-"
                )
                prev_tps = (
                    f"{prev_model.tps:.1f}" if getattr(prev_model, "tps", None) is not None else "-"
                )
                table.add_row(
                    prev_model.id[:40] + "..." if len(prev_model.id) > 40 else prev_model.id,
                    f"{ctx:,}",
                    status,
                    prev_ttft,
                    prev_tps,
                    f"||{response_preview}||" if response_preview else "❌",
                    f"{j + 1}/{len(models_to_test)}",
                )

            # Add current testing model
            table.add_row(
                model.id[:40] + "..." if len(model.id) > 40 else model.id,
                f"{ctx:,}",
                "[blue]Testing...[/blue]",
                "-",
                "-",
                "",
                f"{i}/{len(models_to_test)}",
            )

            live.update(table)

        if i > 1:
            if verbose:
                logger.info(
                    "\n\n  ⏳ Waiting 3 seconds before next model (resource cleanup)...",
                )
            time.sleep(3.0)

        log_path = get_context_test_log_path(model.id)

        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()
        registry.update_model_by_id(model)

        result = tester._test_at_context(model.id, ctx, log_path, model, registry)

        # Store the response preview on the model for later display
        if result.load_success and result.inference_success:
            response_preview = _format_response_preview(result.response)
            if verbose:
                logger.debug(f"  ✓ Success at context {ctx:,}")
                logger.info(f"  Response preview: ||{response_preview}||")
            model.last_known_good_context = ctx
            if not model.tested_max_context or ctx > model.tested_max_context:
                model.tested_max_context = ctx
            if result.ttft_seconds is not None:
                model.ttft_seconds = result.ttft_seconds
            if result.tps is not None:
                model.tps = result.tps
            model.context_test_status = ContextTestStatus.TESTING
            # Store response preview temporarily for display
            model._test_response_preview = response_preview if response_preview else "❌"
        else:
            error_type = "load" if not result.load_success else "inference"
            if verbose:
                logger.debug(f"  ✗ Failed at context {ctx:,} ({error_type} failed)")
            model.last_known_bad_context = ctx
            model.context_test_status = ContextTestStatus.FAILED
            model._test_response_preview = "❌"

        model.context_test_date = datetime.now()
        registry.update_model_by_id(model)
        updated_models.append(model)

    if not verbose:
        # Final update with all results
        table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Context", justify="right", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("TTFT", justify="right", style="blue")
        table.add_column("TPS", justify="right", style="blue")
        table.add_column("Response", style="white")
        table.add_column("Progress", justify="right", style="magenta")

        for j, model in enumerate(updated_models):
            status = (
                "[green]✓ Success[/green]"
                if model.last_known_good_context == ctx
                else "[red]✗ Failed[/red]"
            )
            response_preview = getattr(model, "_test_response_preview", "❌")
            final_ttft = (
                f"{model.ttft_seconds:.2f}s"
                if getattr(model, "ttft_seconds", None) is not None
                else "-"
            )
            final_tps = f"{model.tps:.1f}" if getattr(model, "tps", None) is not None else "-"
            table.add_row(
                model.id[:40] + "..." if len(model.id) > 40 else model.id,
                f"{ctx:,}",
                status,
                final_ttft,
                final_tps,
                f"||{response_preview}||" if response_preview else "❌",
                f"{j + 1}/{len(models_to_test)}",
            )

        live.update(table)
        live.stop()

    return updated_models


def _test_all_models_optimized(
    tester: ContextTester,
    models_to_test: list[Model],
    threshold: int,
    registry: ModelRegistry,
) -> list[Model]:
    """Run optimized batch testing for multiple models."""
    logger.debug(
        f"[bold]Starting optimized batch testing for {len(models_to_test)} models[/bold]",
    )
    logger.debug(f"Threshold: {threshold:,} tokens\n")

    return tester.test_all_models(
        models_to_test,
        threshold=threshold,
        registry=registry,
    )


def _print_final_results(updated_models: list[Model]) -> None:
    """Print the final results table."""
    logger.info(f"\n{'=' * 60}")
    logger.info("Final Results:")
    logger.info(f"{'=' * 60}\n")

    table = Table(show_header=False, header_style="bold cyan", expand=False)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Optimal Context", justify="right")
    table.add_column("Declared Limit", justify="right")
    table.add_column("Efficiency", justify="right")
    table.add_column("TTFT", justify="right", style="blue")
    table.add_column("TPS", justify="right", style="blue")

    for model in updated_models:
        status = "✓ Completed" if model.context_test_status.value == "completed" else "✗ Failed"
        optimal = f"{model.tested_max_context:,}" if model.tested_max_context else "N/A"
        declared = f"{model.context_limit:,}"
        efficiency = (
            f"{(model.tested_max_context / model.context_limit * 100):.1f}%"
            if model.tested_max_context
            else "N/A"
        )
        final_ttft = (
            f"{model.ttft_seconds:.2f}s"
            if getattr(model, "ttft_seconds", None) is not None
            else "-"
        )
        final_tps = f"{model.tps:.1f}" if getattr(model, "tps", None) is not None else "-"

        table.add_row(
            model.id,
            status,
            optimal,
            declared,
            efficiency,
            final_ttft,
            final_tps,
        )

    logger.debug(table)


class LMStrixService:
    """Service layer for LMStrix operations."""

    def scan_models(
        self,
        failed: bool = False,
        reset: bool = False,
        verbose: bool = False,
    ) -> None:
        """Scan for LM Studio models and update the local registry."""
        setup_logging(verbose=verbose)

        if failed and reset:
            logger.error("Cannot use --failed and --all together.")
            return

        try:
            with console.status("Scanning for models..."):
                registry = scan_and_update_registry(
                    rescan_failed=failed,
                    rescan_all=reset,
                    verbose=verbose,
                )

            logger.success("✓ Model scan complete")

            # Show summary of what was found
            models = registry.list_models()
            if models:
                logger.debug(f"[blue]Found {len(models)} models in registry[/blue]")
            else:
                logger.debug(
                    "No models found. Make sure LM Studio is running and has models downloaded.",
                )

        except (APIConnectionError, ModelRegistryError, OSError) as e:
            logger.debug(f"✗ Scan failed: {e}")
            logger.debug("Check that LM Studio is running and accessible.")
            if verbose:
                logger.debug(f"Error details: {e}")
            return

        self.list_models(verbose=verbose, _registry=registry)

    def list_models(
        self,
        sort: str = "id",
        show: str | None = None,
        key: str | None = None,
        verbose: bool = False,
        _registry: "ModelRegistry | None" = None,
    ) -> None:
        list_models_command(
            sort=sort,
            show=show,
            key=key,
            verbose=verbose,
            registry=_registry,
        )

    def describe_models(
        self,
        model_id: str | None = None,
        desc_all: bool = False,
        describer_model_id: str | None = None,
        reset: bool = False,
        verbose: bool = False,
    ) -> None:
        describe_models_command(
            model_id=model_id,
            desc_all=desc_all,
            describer_model_id=describer_model_id,
            reset=reset,
            verbose=verbose,
        )

    def test_models(
        self,
        model_id: str | None = None,
        test_all: bool = False,
        reset: bool = False,
        threshold: int = 31744,
        ctx: int | None = None,
        sort: str = "id",
        fast: bool = False,
        verbose: bool = False,
        force: bool = False,
        prompt: str | None = None,
        file_prompt: str | None = None,
        key: str | None = None,
    ) -> None:
        """Test the context limits for models."""
        setup_logging(verbose=verbose)
        registry = load_model_registry(verbose=verbose)

        if test_all and model_id:
            logger.error("Cannot use --all and specify a model ID together.")
            return

        models_to_test = _get_models_to_test(
            registry,
            test_all,
            ctx,
            model_id,
            reset,
            fast,
        )
        if not models_to_test:
            return

        # Apply keyword filtering if specified
        if key:
            keywords = [k.strip() for k in key.split(",") if k.strip()]
            if keywords:
                models_to_test = filter_models_by_keywords(models_to_test, keywords)
                if not models_to_test:
                    logger.error(f"No models match all keywords: {', '.join(keywords)}")
                    return

        # If reset flag is used, clear test results for all models being tested
        if reset:
            logger.debug("Resetting test results for selected models...")
            for model in models_to_test:
                model.context_test_status = ContextTestStatus.UNTESTED
                model.tested_max_context = None
                model.last_known_good_context = None
                model.last_known_bad_context = None
                model.loadable_max_context = None
                model.context_test_date = None
                model.context_test_log = None
                model.ttft_seconds = None
                model.tps = None
                registry.update_model_by_id(model)
            registry.save()
            logger.success(f"Reset {len(models_to_test)} models for re-testing")

        # Handle custom prompt loading
        custom_prompt = None
        if prompt and file_prompt:
            logger.error("Cannot use both --prompt and --file_prompt together.")
            return
        if prompt:
            custom_prompt = prompt
            if verbose:
                logger.debug(
                    f"Using custom prompt: {prompt[:50]}..."
                    if len(prompt) > 50
                    else f"Using custom prompt: {prompt}"
                )
        elif file_prompt:
            try:
                prompt_path = Path(file_prompt).expanduser()
                if not prompt_path.exists():
                    logger.error(f"Prompt file not found: {file_prompt}")
                    return
                custom_prompt = prompt_path.read_text(encoding="utf-8").strip()
                if verbose:
                    logger.debug(f"Loaded prompt from file: {file_prompt}")
                    logger.debug(
                        f"Prompt: {custom_prompt[:50]}..."
                        if len(custom_prompt) > 50
                        else f"Prompt: {custom_prompt}"
                    )
            except Exception as e:
                logger.error(f"Error reading prompt file: {e}")
                return

        if test_all:
            # Filter out embedding models for --all flag
            tester = ContextTester(verbose=verbose, fast_mode=fast, custom_prompt=custom_prompt)
            models_to_test = tester._filter_models_for_testing(models_to_test)
            if not models_to_test:
                logger.debug(
                    "No LLM models found to test after filtering embedding models.",
                )
                return
            # Custom sorting for optimal testing: size_bytes + context_limit*100000
            # This prioritizes smaller models first, then lower context within similar sizes
            models_to_test = sorted(
                models_to_test,
                key=lambda m: m.size + (m.context_limit * 100_000),
            )
            logger.debug(
                "[cyan]Sorting models by optimal testing order (size + context priority).[/cyan]",
            )

        tester = ContextTester(verbose=verbose, fast_mode=fast, custom_prompt=custom_prompt)

        if ctx is not None:
            if test_all:
                updated_models = _test_all_models_at_ctx(
                    tester,
                    models_to_test,
                    ctx,
                    registry,
                    verbose,
                )
                _print_final_results(updated_models)
            else:
                _test_single_model(tester, models_to_test[0], ctx, registry, force, verbose)
            return

        if test_all:
            updated_models = _test_all_models_optimized(
                tester,
                models_to_test,
                threshold,
                registry,
            )
            _print_final_results(updated_models)
        else:
            model = models_to_test[0]
            max_test_context = min(threshold, model.context_limit)

            if verbose:
                logger.debug(f"\n[bold cyan]Testing model: {model.id}[/bold cyan]")
                logger.debug(f"Declared context limit: {model.context_limit:,} tokens")
                logger.debug(f"Threshold: {threshold:,} tokens")
            else:
                # Compact output - create a live table for testing progress
                table = Table(show_header=False, header_style="bold cyan", box=None, expand=False)
                table.add_column("Model", style="cyan", no_wrap=True)
                table.add_column("Context", justify="right", style="yellow")
                table.add_column("Status", style="blue")
                table.add_column("Response", style="white")

                # Initial row
                table.add_row(
                    model.id[:40] + "..." if len(model.id) > 40 else model.id,
                    f"{max_test_context:,}",
                    "[blue]Testing...[/blue]",
                    "",
                )

                live = Live(table, console=console, refresh_per_second=4)
                live.start()

            updated_model = tester.test_model(
                model,
                max_context=max_test_context,
                registry=registry,
            )

            if updated_model.context_test_status.value == "completed":
                response_preview = getattr(updated_model, "_test_response_preview", "❌")
                if verbose:
                    logger.debug(
                        f"[green]✓ Test complete. Optimal context: {updated_model.tested_max_context:,}[/green]",
                    )
                    if response_preview:
                        logger.info(f"Response preview: ||{response_preview}||")
                else:
                    # Update the table with success
                    ttft_str = (
                        f"{updated_model.ttft_seconds:.2f}s"
                        if getattr(updated_model, "ttft_seconds", None) is not None
                        else "-"
                    )
                    tps_str = (
                        f"{updated_model.tps:.1f}"
                        if getattr(updated_model, "tps", None) is not None
                        else "-"
                    )
                    table = Table(
                        show_header=False, header_style="bold cyan", box=None, expand=False
                    )
                    table.add_column("Model", style="cyan", no_wrap=True)
                    table.add_column("Context", justify="right", style="yellow")
                    table.add_column("Status", style="green")
                    table.add_column("TTFT", justify="right", style="blue")
                    table.add_column("TPS", justify="right", style="blue")
                    table.add_column("Response", style="white")

                    table.add_row(
                        model.id[:40] + "..." if len(model.id) > 40 else model.id,
                        f"{updated_model.tested_max_context:,}",
                        "[green]✓ Success[/green]",
                        ttft_str,
                        tps_str,
                        f"||{response_preview}||" if response_preview else "❌",
                    )
                    live.update(table)
                    live.stop()
            else:
                error_msg = getattr(updated_model, "error_msg", "Unknown error")
                if verbose:
                    logger.debug(f"✗ Test failed: {error_msg}")
                else:
                    # Update the table with failure
                    table = Table(
                        show_header=False, header_style="bold cyan", box=None, expand=False
                    )
                    table.add_column("Model", style="cyan", no_wrap=True)
                    table.add_column("Context", justify="right", style="yellow")
                    table.add_column("Status", style="red")
                    table.add_column("Response", style="white")

                    table.add_row(
                        model.id[:40] + "..." if len(model.id) > 40 else model.id,
                        f"{max_test_context:,}",
                        "[red]✗ Failed[/red]",
                        "",
                    )
                    live.update(table)
                    live.stop()

    def run_inference(
        self,
        prompt: str,
        model_id: str | None = None,
        out_ctx: int | str = -1,
        in_ctx: int | str | None = None,
        reload: bool = False,
        file_prompt: str | None = None,
        dict_params: str | None = None,
        text: str | None = None,
        text_file: str | None = None,
        param_temp: float = 0.8,
        param_top_k: int = 40,
        param_top_p: float = 0.95,
        param_repeat: float = 1.1,
        param_min_p: float = 0.05,
        stream: bool = False,
        stream_timeout: int = 120,
        verbose: bool = False,
    ) -> None:
        run_inference_command(
            prompt=prompt,
            model_id=model_id,
            out_ctx=out_ctx,
            in_ctx=in_ctx,
            reload=reload,
            file_prompt=file_prompt,
            dict_params=dict_params,
            text=text,
            text_file=text_file,
            param_temp=param_temp,
            param_top_k=param_top_k,
            param_top_p=param_top_p,
            param_repeat=param_repeat,
            param_min_p=param_min_p,
            stream=stream,
            stream_timeout=stream_timeout,
            verbose=verbose,
        )

    def check_health(self, verbose: bool = False) -> None:
        check_health_command(verbose=verbose)

    def save_configs(
        self,
        flash: bool = False,
        limit: str | int = "100%",
        threshold: int = 0,
        verbose: bool = False,
    ) -> None:
        save_configs_command(
            flash=flash,
            limit=limit,
            threshold=threshold,
            verbose=verbose,
        )

    def about(self, verbose: bool = False) -> None:
        about_command(verbose=verbose)

    def show_help(self) -> None:
        show_help_command()
