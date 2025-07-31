"""Command-line interface for LMStrix."""

import json
import time
from datetime import datetime

import fire
from rich.console import Console
from rich.table import Table

from lmstrix.api.exceptions import APIConnectionError, ModelRegistryError
from lmstrix.utils.logging import logger

from lmstrix.core.concrete_config import ConcreteConfigManager
from lmstrix.utils.logging import logger

from lmstrix.core.context_tester import ContextTester
from lmstrix.utils.logging import logger

from lmstrix.core.inference_manager import InferenceManager
from lmstrix.utils.logging import logger

from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.utils.logging import logger

from lmstrix.loaders.model_loader import (
from lmstrix.utils.logging import logger

    load_model_registry,
    scan_and_update_registry,
)
from lmstrix.utils import get_context_test_log_path, setup_logging
from lmstrix.utils.logging import logger

from lmstrix.utils.context_parser import get_model_max_context, parse_out_ctx
from lmstrix.utils.logging import logger

from lmstrix.utils.paths import get_default_models_file, get_lmstudio_path
from lmstrix.utils.logging import logger

from lmstrix.utils.state import StateManager
from lmstrix.utils.logging import logger


console = Console()


def _get_models_to_test(
    registry: ModelRegistry,
    test_all: bool,
    ctx: int | None,
    model_id: str | None,
    reset: bool = False,
    fast_mode: bool = False,
) -> list[Model]:
    """Filter and return a list of models to be tested."""
    tester = ContextTester(fast_mode=fast_mode)  # Create a temporary tester for _is_embedding_model

    if not test_all:
        if not model_id:
            logger.error(f"You must specify a model ID or use the --all flag.")
            return []
        model = registry.find_model(model_id)
        if not model:
            logger.error(f"Model '{model_id}' not found in registry.")
            return []
        if tester._is_embedding_model(model):
            logger.debug(
                f"[red]Error: Model '{model_id}' is an embedding model and cannot be tested as an LLM.[/red]",
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
            f"[yellow]Excluded {skipped_embedding} embedding models from testing.[/yellow]",
        )

    if not models_to_test:
        if ctx is not None:
            logger.debug(
                "[yellow]No LLM models found to test at the specified context size.[/yellow]",
            )
            logger.debug(
                "[dim]Models may already be tested or context exceeds their limits.[/dim]",
            )
        elif reset:
            logger.debug(
                "[yellow]No models found to test (check model availability).[/yellow]",
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
    }
    sort_attr = key_map.get(sort_key.rstrip("d"))

    if not sort_attr:
        logger.debug(f"[red]Invalid sort option: {sort_by}. Using default (id).[/red]")
        return sorted(models, key=lambda m: m.id)

    return sorted(models, key=lambda m: getattr(m, sort_attr) or 0, reverse=reverse)


def _test_single_model(
    tester: ContextTester,
    model: Model,
    ctx: int,
    registry: ModelRegistry,
) -> None:
    """Test a single model at a specific context size."""
    if ctx > model.context_limit:
        logger.debug(
            f"[yellow]Warning: Specified context ({ctx:,}) exceeds model's declared limit ({model.context_limit:,}). Skipping test.[/yellow]",
        )
        return

    if model.last_known_bad_context and ctx >= model.last_known_bad_context:
        max_safe_context = int(model.last_known_bad_context * 0.75)
        logger.debug(
            f"[red]Error: Specified context ({ctx:,}) is at or above the last known bad context ({model.last_known_bad_context:,}).[/red]",
        )
        logger.debug(
            f"[yellow]The maximum safe context to test is {max_safe_context:,} (75% of last bad).[/yellow]",
        )
        return

    logger.debug(
        f"\n[bold cyan]Testing model: {model.id} at specific context: {ctx:,}[/bold cyan]",
    )
    logger.debug(f"[dim]Declared context limit: {model.context_limit:,} tokens[/dim]")

    log_path = get_context_test_log_path(model.id)

    model.context_test_status = ContextTestStatus.TESTING
    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)

    result = tester._test_at_context(model.id, ctx, log_path, model, registry)

    if result.load_success and result.inference_success:
        logger.success(f"✓ Test successful at context {ctx:,}")
        logger.debug(f"[dim]Response length: {len(result.response)} chars[/dim]")
        model.last_known_good_context = ctx
        if not model.tested_max_context or ctx > model.tested_max_context:
            model.tested_max_context = ctx
        model.context_test_status = ContextTestStatus.COMPLETED
    else:
        error_type = "load" if not result.load_success else "inference"
        logger.debug(f"[red]✗ Test failed at context {ctx:,} ({error_type} failed)[/red]")
        logger.debug(f"[dim]Error: {result.error}[/dim]")
        model.last_known_bad_context = ctx
        model.context_test_status = ContextTestStatus.FAILED

    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)


def _test_all_models_at_ctx(
    tester: ContextTester,
    models_to_test: list[Model],
    ctx: int,
    registry: ModelRegistry,
) -> list[Model]:
    """Test all models at a specific context size."""
    logger.debug(
        f"[bold]Testing {len(models_to_test)} models at context size {ctx:,}[/bold]\n",
    )

    updated_models = []
    for i, model in enumerate(models_to_test, 1):
        logger.info(f"[{i}/{len(models_to_test)}] Testing {model.id}...")

        if i > 1:
            logger.info("\n\n  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
            time.sleep(3.0)

        log_path = get_context_test_log_path(model.id)

        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()
        registry.update_model_by_id(model)

        result = tester._test_at_context(model.id, ctx, log_path, model, registry)

        if result.load_success and result.inference_success:
            logger.debug(f"  ✓ Success at context {ctx:,}")
            model.last_known_good_context = ctx
            if not model.tested_max_context or ctx > model.tested_max_context:
                model.tested_max_context = ctx
            model.context_test_status = ContextTestStatus.TESTING
        else:
            error_type = "load" if not result.load_success else "inference"
            logger.debug(f"  ✗ Failed at context {ctx:,} ({error_type} failed)")
            model.last_known_bad_context = ctx
            model.context_test_status = ContextTestStatus.FAILED

        model.context_test_date = datetime.now()
        registry.update_model_by_id(model)
        updated_models.append(model)

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
    logger.debug(f"[dim]Threshold: {threshold:,} tokens[/dim]\n")

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

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Optimal Context", justify="right")
    table.add_column("Declared Limit", justify="right")
    table.add_column("Efficiency", justify="right")

    for model in updated_models:
        status = "✓ Completed" if model.context_test_status.value == "completed" else "✗ Failed"
        optimal = f"{model.tested_max_context:,}" if model.tested_max_context else "N/A"
        declared = f"{model.context_limit:,}"
        efficiency = (
            f"{(model.tested_max_context / model.context_limit * 100):.1f}%"
            if model.tested_max_context
            else "N/A"
        )

        table.add_row(
            model.id,
            status,
            optimal,
            declared,
            efficiency,
        )

    logger.debug(table)


class LMStrixCLI:
    """A CLI for testing and managing LM Studio models."""

    def scan(self, failed: bool = False, reset: bool = False, verbose: bool = False) -> None:
        """Scan for LM Studio models and update the local registry.

        Args:
            failed: Re-scan only models that previously failed.
            all: Re-scan all models (clear existing test data).
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        if failed and reset:
            logger.error(f"Cannot use --failed and --all together.")
            return

        try:
            with console.status("Scanning for models..."):
                registry = scan_and_update_registry(
                    rescan_failed=failed,
                    rescan_all=reset,
                    verbose=verbose,
                )

            logger.success(f"✓ Model scan complete")

            # Show summary of what was found
            models = registry.list_models()
            if models:
                logger.debug(f"[blue]Found {len(models)} models in registry[/blue]")
            else:
                logger.debug(
                    "[yellow]No models found. Make sure LM Studio is running "
                    "and has models downloaded.[/yellow]",
                )

        except (APIConnectionError, ModelRegistryError, OSError) as e:
            logger.debug(f"[red]✗ Scan failed: {e}[/red]")
            logger.debug("[yellow]Check that LM Studio is running and accessible.[/yellow]")
            if verbose:
                logger.debug(f"[dim]Error details: {e}[/dim]")
            return

        self.list()

    def list(self, sort: str = "id", show: str | None = None, verbose: bool = False) -> None:
        """List all models from the registry with their test status.

        Args:
            sort: Sort order. Options: id, idd, ctx, ctxd, dtx, dtxd, size, sized, smart, smartd (d = descending).
            show: Output format. Options: id (plain IDs), path (relative paths), json (JSON array).
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        if not models:
            logger.debug(
                "[yellow]No models found. Run 'lmstrix scan' to discover models.[/yellow]",
            )
            return

        # Sort models based on the sort parameter
        sort_key = sort.lower()
        reverse = sort_key.endswith("d") and len(sort_key) > 1

        if sort_key in ("id", "idd"):
            sorted_models = sorted(models, key=lambda m: m.id, reverse=reverse)
        elif sort_key in ("ctx", "ctxd"):
            sorted_models = sorted(models, key=lambda m: m.tested_max_context or 0, reverse=reverse)
        elif sort_key in ("dtx", "dtxd"):
            sorted_models = sorted(models, key=lambda m: m.context_limit, reverse=reverse)
        elif sort_key in ("size", "sized"):
            sorted_models = sorted(models, key=lambda m: m.size, reverse=reverse)
        elif sort_key in ("smart", "smartd"):
            # Use the same smart sorting as 'test --all': size + context_limit * 100,000
            # This prioritizes smaller models first, then lower context within similar sizes
            sorted_models = sorted(
                models,
                key=lambda m: m.size + (m.context_limit * 100_000),
                reverse=reverse,
            )
        else:
            logger.debug(f"[red]Invalid sort option: {sort}. Using default (id).[/red]")
            sorted_models = sorted(models, key=lambda m: m.id)

        # Handle different show formats
        if show:
            if show == "id":
                # Plain newline-delimited list of model IDs
                for model in sorted_models:
                    logger.info(model.id)
            elif show == "path":
                # Newline-delimited list of relative paths
                for model in sorted_models:
                    # Model.id is already the relative path
                    logger.info(model.id)
            elif show == "json":
                # JSON array of models (matching registry format)
                models_dict = []
                for model in sorted_models:
                    model_data = model.model_dump(by_alias=True, mode="json")
                    models_dict.append(model_data)
                logger.info(json.dumps(models_dict, indent=2))
            else:
                logger.debug(f"[red]Invalid show option: {show}. Options: id, path, json.[/red]")
                return
            return

        table = Table(title="LM Studio Models", show_lines=False)
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Size\n(GB)", style="magenta", width=8)
        table.add_column("Declared\nCtx", style="yellow", width=10)
        table.add_column("Tested\nCtx", style="green", width=10)
        table.add_column("Last\nGood", style="green", width=10)
        table.add_column("Last\nBad", style="red", width=10)
        table.add_column("Status", style="blue", width=12)

        for model in sorted_models:
            tested_ctx = f"{model.tested_max_context:,}" if model.tested_max_context else "-"
            last_good = (
                f"{model.last_known_good_context:,}" if model.last_known_good_context else "-"
            )
            last_bad = f"{model.last_known_bad_context:,}" if model.last_known_bad_context else "-"

            status_map = {
                "untested": "[dim]Untested[/dim]",
                "testing": "[yellow]Testing...[/yellow]",
                "completed": "[green]✓ Tested[/green]",
                "failed": "[red]✗ Failed[/red]",
            }
            status = status_map.get(model.context_test_status.value, "[dim]Unknown[/dim]")

            table.add_row(
                model.id,
                f"{model.size / (1024**3):.2f}" if model.size else "N/A",
                f"{model.context_limit:,}",
                tested_ctx,
                last_good,
                last_bad,
                status,
            )
        logger.debug(table)

    def test(
        self,
        model_id: str | None = None,
        all: bool = False,
        reset: bool = False,
        threshold: int = 31744,
        ctx: int | None = None,
        sort: str = "id",
        fast: bool = False,
        verbose: bool = False,
    ) -> None:
        """Test the context limits for models.

        Args:
            model_id: The specific model ID to test.
            all: Test all untested or previously failed models.
            reset: Re-test all models, including those already tested.
            threshold: Maximum context size for initial testing (default: 31744).
                      Prevents system crashes from very large contexts.
            ctx: Test only this specific context value (skips if > declared context).
            sort: Sort order (only used for single model tests). --all always sorts by size.
            fast: Skip semantic verification - only test if inference completes technically.
            verbose: Enable verbose output.
        """
        setup_logging(verbose=verbose)
        registry = load_model_registry(verbose=verbose)

        # Handle both --all and --test_all flags
        test_all_models = all

        if test_all_models and model_id:
            logger.error(f"Cannot use --all and specify a model ID together.")
            return

        models_to_test = _get_models_to_test(registry, test_all_models, ctx, model_id, reset, fast)
        if not models_to_test:
            return

        # If reset flag is used, clear test results for all models being tested
        if reset:
            logger.debug("[yellow]Resetting test results for selected models...[/yellow]")
            for model in models_to_test:
                model.context_test_status = ContextTestStatus.UNTESTED
                model.tested_max_context = None
                model.last_known_good_context = None
                model.last_known_bad_context = None
                model.loadable_max_context = None
                model.context_test_date = None
                model.context_test_log = None
                registry.update_model_by_id(model)
            registry.save()
            logger.success(f"Reset {len(models_to_test)} models for re-testing")

        if test_all_models:
            # Filter out embedding models for --all flag
            tester = ContextTester(verbose=verbose, fast_mode=fast)
            models_to_test = tester._filter_models_for_testing(models_to_test)
            if not models_to_test:
                logger.debug(
                    "[yellow]No LLM models found to test after filtering embedding models.[/yellow]",
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

        tester = ContextTester(verbose=verbose, fast_mode=fast)

        if ctx is not None:
            if test_all_models:
                updated_models = _test_all_models_at_ctx(tester, models_to_test, ctx, registry)
                _print_final_results(updated_models)
            else:
                _test_single_model(tester, models_to_test[0], ctx, registry)
            return

        if test_all_models:
            updated_models = _test_all_models_optimized(tester, models_to_test, threshold, registry)
            _print_final_results(updated_models)
        else:
            model = models_to_test[0]
            logger.debug(f"\n[bold cyan]Testing model: {model.id}[/bold cyan]")
            logger.debug(f"[dim]Declared context limit: {model.context_limit:,} tokens[/dim]")
            logger.debug(f"[dim]Threshold: {threshold:,} tokens[/dim]")

            max_test_context = min(threshold, model.context_limit)
            updated_model = tester.test_model(
                model,
                max_context=max_test_context,
                registry=registry,
            )

            if updated_model.context_test_status.value == "completed":
                logger.debug(
                    f"[green]✓ Test complete. Optimal context: {updated_model.tested_max_context:,}[/green]",
                )
            else:
                error_msg = getattr(updated_model, "error_msg", "Unknown error")
                logger.debug(f"[red]✗ Test failed: {error_msg}[/red]")

    def infer(
        self,
        prompt: str,
        model_id: str | None = None,
        out_ctx: int | str = -1,
        in_ctx: int | str | None = None,
        reload: bool = False,
        file_prompt: str | None = None,
        dict: str | None = None,
        text: str | None = None,
        text_file: str | None = None,
        temperature: float = 0.7,
        verbose: bool = False,
    ) -> None:
        """Run inference on a specified model.

        Args:
            prompt: The text prompt to send to the model. If file_prompt is specified,
                   this refers to the prompt name in the TOML file.
            model_id: The ID of the model to use for inference. If not specified, uses the last loaded model.
            out_ctx: Maximum tokens to generate (-1 for unlimited, or "50%" for percentage of max context).
            in_ctx: Context size at which to load the model. If 0, load without specified context.
                   If not specified, reuse existing loaded model if available.
            reload: Force reload the model even if already loaded.
            file_prompt: Path to TOML file containing prompt templates.
            dict: Dictionary parameters as key=value pairs (e.g., "name=Alice,topic=AI").
            text: Text content to use for {{text}} placeholder (overrides text in dict).
            text_file: Path to file containing text content for {{text}} placeholder.
            temperature: The sampling temperature.
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        if not out_ctx:
            out_ctx = -1  # Default to unlimited

        # Handle --text and --text_file for simple prompts without file_prompt
        if not file_prompt and (text or text_file):
            if text_file:
                from pathlib import Path

                try:
                    text_path = Path(text_file).expanduser()
                    if not text_path.exists():
                        logger.error(f"Text file not found: {text_file}")
                        return
                    text_content = text_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.debug(f"[red]Error reading text file: {e}[/red]")
                    return
            else:
                text_content = text

            # Replace {{text}} placeholder in the prompt
            actual_prompt = prompt.replace("{{text}}", text_content)
        # Handle prompt file loading if specified
        elif file_prompt:
            from pathlib import Path

            from lmstrix.loaders.prompt_loader import load_single_prompt
from lmstrix.utils.logging import logger


            # Parse dictionary parameters
            prompt_params = {}
            if dict:
                # Support both comma-separated and space-separated formats
                if "," in dict:
                    # Format: "key1=value1,key2=value2"
                    pairs = dict.split(",")
                else:
                    # Format: "key1=value1 key2=value2" (fire might split this)
                    # For now, assume comma-separated
                    pairs = dict.split(",")

                for pair in pairs:
                    pair = pair.strip()
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        prompt_params[key.strip()] = value.strip()
                    else:
                        logger.debug(
                            f"[yellow]Warning: Invalid parameter format '{pair}'. Expected 'key=value'.[/yellow]",
                        )

            # Handle --text and --text_file
            if text_file:
                try:
                    text_path = Path(text_file).expanduser()
                    if not text_path.exists():
                        logger.error(f"Text file not found: {text_file}")
                        return
                    prompt_params["text"] = text_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.debug(f"[red]Error reading text file: {e}[/red]")
                    return
            elif text:
                prompt_params["text"] = text

            # Load and resolve prompt from TOML file
            try:
                prompt_path = Path(file_prompt).expanduser()
                if not prompt_path.exists():
                    logger.error(f"Prompt file not found: {file_prompt}")
                    return

                resolved_prompt = load_single_prompt(
                    toml_path=prompt_path,
                    prompt_name=prompt,  # Now refers to prompt name in TOML
                    verbose=verbose,
                    **prompt_params,
                )

                actual_prompt = resolved_prompt.resolved

                if verbose:
                    logger.debug(f"[dim]Loaded prompt '{prompt}' from {file_prompt}[/dim]")
                    if resolved_prompt.placeholders_resolved:
                        logger.debug(
                            f"[dim]Resolved placeholders: {', '.join(resolved_prompt.placeholders_resolved)}[/dim]",
                        )
                    if resolved_prompt.placeholders_unresolved:
                        logger.debug(
                            f"[yellow]Warning: Unresolved placeholders: {', '.join(resolved_prompt.placeholders_unresolved)}[/yellow]",
                        )

            except Exception as e:
                logger.debug(f"[red]Error loading prompt from file: {e}[/red]")
                return
        else:
            # No file_prompt, just use the prompt as-is
            actual_prompt = prompt

        # Initialize state manager
        state_manager = StateManager()

        # Handle model_id
        if not model_id:
            # Try to use the last used model
            model_id = state_manager.get_last_used_model()
            if not model_id:
                logger.error(f"No model specified and no last-used model found.")
                logger.debug("[yellow]Please specify a model with -m or --model_id[/yellow]")
                return
            if verbose:
                logger.debug(f"[dim]Using last-used model: {model_id}[/dim]")

        registry = load_model_registry(verbose=verbose)
        model = registry.find_model(model_id)
        if not model:
            logger.error(f"Model '{model_id}' not found in registry.")
            return

        # Update last-used model
        state_manager.set_last_used_model(model_id)

        # Handle reload by setting in_ctx to optimal if not specified
        if reload and in_ctx is None:
            # Force reload with optimal context
            in_ctx = model.tested_max_context or model.context_limit
            logger.debug(
                f"[yellow]Force reload requested, loading with context {in_ctx:,}[/yellow]",
            )

        # Parse out_ctx if it's a percentage
        if isinstance(out_ctx, str) and out_ctx != "-1":
            try:
                max_context = get_model_max_context(model, use_tested=True)
                if not max_context:
                    max_context = model.context_limit
                parsed_out_ctx = parse_out_ctx(out_ctx, max_context)
                if verbose:
                    logger.debug(
                        f"[dim]Parsed out_ctx '{out_ctx}' as {parsed_out_ctx} tokens[/dim]",
                    )
                out_ctx = parsed_out_ctx
            except ValueError as e:
                logger.error(f"{e}")
                return

        # Parse in_ctx if it's a percentage
        if isinstance(in_ctx, str):
            try:
                max_context = get_model_max_context(model, use_tested=True)
                if not max_context:
                    max_context = model.context_limit
                parsed_in_ctx = parse_out_ctx(in_ctx, max_context)
                if verbose:
                    logger.debug(
                        f"[dim]Parsed in_ctx '{in_ctx}' as {parsed_in_ctx} tokens[/dim]",
                    )
                in_ctx = parsed_in_ctx
            except ValueError as e:
                logger.error(f"{e}")
                return

        manager = InferenceManager(registry=registry, verbose=verbose)

        # Show status only in verbose mode
        if verbose:
            with console.status(f"Running inference on {model.id}..."):
                result = manager.infer(
                    model_id=model.id,  # Use the full ID for inference
                    prompt=actual_prompt,  # Use the resolved prompt
                    in_ctx=in_ctx,
                    out_ctx=out_ctx,
                    temperature=temperature,
                )
        else:
            result = manager.infer(
                model_id=model.id,  # Use the full ID for inference
                prompt=actual_prompt,  # Use the resolved prompt
                in_ctx=in_ctx,
                out_ctx=out_ctx,
                temperature=temperature,
            )

        if result["succeeded"]:
            if verbose:
                logger.debug("\n[green]Model Response:[/green]")
                logger.debug(result["response"])
                # Stats are now shown in the completion method, no need to duplicate
            else:
                # In non-verbose mode, only print the response
                logger.debug(result["response"])
        else:
            logger.debug(f"[red]Inference failed: {result['error']}[/red]")

    def health(self, verbose: bool = False) -> None:
        """Check database health and backup status.

        Args:
            verbose: Enable verbose output.
        """
        setup_logging(verbose=verbose)

        models_file = get_default_models_file()
        logger.debug("[blue]Database Health Check[/blue]")
        logger.debug(f"Registry file: {models_file}")

        # Check if registry exists
        if not models_file.exists():
            logger.debug("[red]✗ Registry file not found[/red]")
            return

        logger.success(f"✓ Registry file exist")

        # Check if registry is valid JSON
        try:
            with models_file.open() as f:
                json.load(f)
            logger.success(f"✓ Registry file is valid JSO")
        except json.JSONDecodeError as e:
            logger.debug(f"[red]✗ Registry file is corrupted: {e}[/red]")

        # Load with validation
        try:
            registry = load_model_registry(verbose=verbose)
            model_count = len(registry)
            logger.success(f"✓ Successfully loaded {model_count} model")

            # Check for validation issues
            invalid_models = []
            for model_path, model in registry.models.items():
                if not model.validate_integrity():
                    invalid_models.append(model_path)

            if invalid_models:
                logger.debug(
                    f"[yellow]⚠ Found {len(invalid_models)} models with integrity issues[/yellow]",
                )
                if verbose:
                    for model_path in invalid_models:
                        logger.debug(f"  - {model_path}")
            else:
                logger.success(f"✓ All models pass integrity check")

        except (ModelRegistryError, OSError, json.JSONDecodeError) as e:
            logger.debug(f"[red]✗ Failed to load registry: {e}[/red]")

        # Check backup files
        backup_pattern = f"{models_file.stem}.backup_*"
        backup_files = list(models_file.parent.glob(backup_pattern))

        if backup_files:
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            logger.debug(f"[blue]Found {len(backup_files)} backup files:[/blue]")

            for _i, backup_file in enumerate(backup_files[:5]):  # Show latest 5
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                size_kb = backup_file.stat().st_size // 1024

                # Test if backup is valid
                try:
                    with backup_file.open() as f:
                        json.load(f)
                    status = "[green]✓[/green]"
                except json.JSONDecodeError:
                    status = "[red]✗[/red]"

                logger.debug(
                    f"  {status} {backup_file.name} ({size_kb}KB, {mtime.strftime('%Y-%m-%d %H:%M')})",
                )

            if len(backup_files) > 5:
                logger.debug(f"  ... and {len(backup_files) - 5} more")
        else:
            logger.debug("[yellow]No backup files found[/yellow]")

    def save(self, flash: bool = False, verbose: bool = False) -> None:
        """Save tested context limits to LM Studio concrete config files.

        This command reads the lmstrix.json database and creates or updates
        concrete JSON configuration files in LM Studio's .internal directory
        for each model that has a tested_max_context value.

        Args:
            flash: Enable flash attention for GGUF models.
            verbose: Enable verbose output.
        """
        setup_logging(verbose=verbose)

        # Load the model registry
        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        # Filter models with tested context
        models_with_context = [m for m in models if m.tested_max_context]

        if not models_with_context:
            logger.debug("[yellow]No models with tested context limits found.[/yellow]")
            logger.debug("[dim]Run 'lmstrix test' to test model context limits first.[/dim]")
            return

        logger.debug(
            f"[blue]Found {len(models_with_context)} models with tested context limits[/blue]",
        )

        # Get LM Studio path
        try:
            lms_path = get_lmstudio_path()
        except Exception as e:
            logger.debug(f"[red]Failed to find LM Studio installation: {e}[/red]")
            return

        # Create concrete config manager
        config_manager = ConcreteConfigManager(lms_path)

        # Save configurations
        with console.status("Saving concrete configurations..."):
            successful, failed = config_manager.save_all_configs(
                models_with_context,
                enable_flash=flash,
            )

        # Report results
        if successful > 0:
            logger.debug(
                f"[green]✓ Successfully saved {successful} model configurations[/green]",
            )

        if failed > 0:
            logger.debug(
                f"[red]✗ Failed to save {failed} model configurations[/red]",
            )

        if flash:
            gguf_count = sum(1 for m in models_with_context if str(m.path).endswith(".gguf"))
            if gguf_count > 0:
                logger.debug(
                    f"[blue]Flash attention enabled for {gguf_count} GGUF models[/blue]",
                )


def show_help() -> None:
    """Show comprehensive help text."""
    logger.debug("[bold cyan]LMStrix - LM Studio Model Testing Toolkit[/bold cyan]")
    logger.debug("\n[cyan]Available commands:[/cyan]")
    logger.debug("  [green]scan[/green]            Scan for LM Studio models and update registry")
    logger.debug("    [dim]--failed          Re-scan only previously failed models[/dim]")
    logger.debug("    [dim]--reset           Re-scan all models (clear test data)[/dim]")
    logger.debug("    [dim]--verbose         Enable verbose output[/dim]")
    logger.debug("")
    logger.debug("  [green]list[/green]            List all models with their test status")
    logger.debug(
        "    [dim]--sort id|ctx|dtx|size|smart  Sort by: id, tested context, declared context, size, smart[/dim]",
    )
    logger.debug("    [dim]--show id|path|json     Output format[/dim]")
    logger.debug("    [dim]--verbose         Enable verbose output[/dim]")
    logger.debug("")
    logger.debug("  [green]test[/green]            Test model context limits")
    logger.debug("    [dim]MODEL_ID          Test specific model[/dim]")
    logger.debug("    [dim]--all             Test all untested models[/dim]")
    logger.debug("    [dim]--reset           Re-test all models[/dim]")
    logger.debug("    [dim]--ctx SIZE        Test specific context size[/dim]")
    logger.debug(
        "    [dim]--threshold SIZE  Max context for initial testing (default: 31744)[/dim]",
    )
    logger.debug(
        "    [dim]--fast            Skip semantic verification (only test if inference completes)[/dim]",
    )
    logger.debug("    [dim]--verbose         Enable verbose output[/dim]")
    logger.debug("")
    logger.debug("  [green]infer[/green]           Run inference on a model")
    logger.debug("    [dim]PROMPT MODEL_ID   Required prompt and model[/dim]")
    logger.debug(
        "    [dim]--out_ctx NUM|%   Maximum tokens to generate (e.g., 500 or '80%')[/dim]",
    )
    logger.debug("    [dim]--in_ctx NUM      Context size for loading model[/dim]")
    logger.debug("    [dim]--file_prompt PATH Load prompt from TOML file[/dim]")
    logger.debug("    [dim]--dict PARAMS     Parameters as key=value pairs[/dim]")
    logger.debug("    [dim]--temperature NUM Temperature for generation[/dim]")
    logger.debug("    [dim]--reload          Force reload model[/dim]")
    logger.debug("    [dim]--verbose         Enable verbose output[/dim]")
    logger.debug("")
    logger.debug("  [green]health[/green]          Check database health and backups")
    logger.debug("    [dim]--verbose         Show detailed health information[/dim]")
    logger.debug("")
    logger.debug("  [green]save[/green]            Save tested contexts to LM Studio configs")
    logger.debug("    [dim]--flash           Enable flash attention for GGUF models[/dim]")
    logger.debug("    [dim]--verbose         Enable verbose output[/dim]")
    logger.debug("")
    logger.debug("[dim]Examples:[/dim]")
    logger.debug("  [dim]lmstrix scan --verbose[/dim]")
    logger.debug("  [dim]lmstrix list --sort ctx[/dim]")
    logger.debug("  [dim]lmstrix test --all[/dim]")
    logger.debug("  [dim]lmstrix test my-model --ctx 8192[/dim]")
    logger.debug('  [dim]lmstrix infer "Hello world" my-model[/dim]')
    logger.debug("  [dim]lmstrix save --flash[/dim]")


def main() -> None:
    """Main entry point for the CLI."""
    import sys

    # Check for help flags first
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h", "help"):
        show_help()
        return

    try:
        fire.Fire(LMStrixCLI)
    except TypeError as e:
        if "Inspector.__init__()" in str(e) and "theme_name" in str(e):
            # Handle Fire/IPython compatibility issue - show our custom help
            show_help()
        else:
            raise


if __name__ == "__main__":
    main()
