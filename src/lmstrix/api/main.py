"""Main API service layer for LMStrix CLI operations."""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from lmstrix.api.exceptions import APIConnectionError, ModelRegistryError
from lmstrix.core.concrete_config import ConcreteConfigManager
from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.loaders.model_loader import (
    load_model_registry,
    scan_and_update_registry,
)
from lmstrix.loaders.prompt_loader import load_single_prompt
from lmstrix.utils import get_context_test_log_path, setup_logging
from lmstrix.utils.context_parser import get_model_max_context, parse_out_ctx
from lmstrix.utils.logging import logger
from lmstrix.utils.paths import get_default_models_file, get_lmstudio_path
from lmstrix.utils.state import StateManager

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

    logger.info(
        f"\n[bold cyan]Testing model: {model.id} at specific context: {ctx:,}[/bold cyan]",
    )
    logger.info(f"Declared context limit: {model.context_limit:,} tokens")

    log_path = get_context_test_log_path(model.id)

    model.context_test_status = ContextTestStatus.TESTING
    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)

    result = tester._test_at_context(model.id, ctx, log_path, model, registry)

    if result.load_success and result.inference_success:
        logger.success(f"✓ Test successful at context {ctx:,}")
        logger.debug(f"Response length: {len(result.response)} chars")
        model.last_known_good_context = ctx
        if not model.tested_max_context or ctx > model.tested_max_context:
            model.tested_max_context = ctx
        model.context_test_status = ContextTestStatus.COMPLETED
    else:
        error_type = "load" if not result.load_success else "inference"
        logger.error(f"✗ Test failed at context {ctx:,} ({error_type} failed)")
        logger.error(f"Error: {result.error}")
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
            logger.info(
                "\n\n  ⏳ Waiting 3 seconds before next model (resource cleanup)...",
            )
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

        # After scanning, list the models
        self.list_models(verbose=verbose)

    def list_models(
        self,
        sort: str = "id",
        show: str | None = None,
        verbose: bool = False,
    ) -> None:
        """List all models from the registry with their test status."""
        setup_logging(verbose=verbose)

        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        if not models:
            logger.debug(
                "No models found. Run 'lmstrix scan' to discover models.",
            )
            return

        # Sort models based on the sort parameter
        sort_key = sort.lower()
        reverse = sort_key.endswith("d") and len(sort_key) > 1

        if sort_key in ("id", "idd"):
            sorted_models = sorted(models, key=lambda m: m.id, reverse=reverse)
        elif sort_key in ("ctx", "ctxd"):
            sorted_models = sorted(
                models,
                key=lambda m: m.tested_max_context or 0,
                reverse=reverse,
            )
        elif sort_key in ("dtx", "dtxd"):
            sorted_models = sorted(
                models,
                key=lambda m: m.context_limit,
                reverse=reverse,
            )
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
            logger.debug(f"Invalid sort option: {sort}. Using default (id).")
            sorted_models = sorted(models, key=lambda m: m.id)

        # Handle different show formats
        if show:
            if show == "id":
                # Plain newline-delimited list of model IDs
                for model in sorted_models:
                    print(model.id)
            elif show == "path":
                # Newline-delimited list of relative paths
                for model in sorted_models:
                    # Model.id is already the relative path
                    print(model.id)
            elif show == "json":
                # JSON array of models (matching registry format)
                models_dict = []
                for model in sorted_models:
                    model_data = model.model_dump(by_alias=True, mode="json")
                    models_dict.append(model_data)
                print(json.dumps(models_dict, indent=2))
            else:
                logger.debug(f"Invalid show option: {show}. Options: id, path, json.")
                return
            return

        table = Table(title="LM Studio Models", show_lines=False, box=None)
        table.add_column("Model ID", style="cyan", no_wrap=False)
        table.add_column("Size(GB)", style="magenta", width=8)
        table.add_column("Declared", style="yellow", width=10)
        table.add_column("Tested", style="green", width=10)
        table.add_column("Good", style="green", width=10)
        table.add_column("Bad", style="red", width=10)
        table.add_column("Status", style="blue", width=10)

        for model in sorted_models:
            tested_ctx = f"{model.tested_max_context:,}" if model.tested_max_context else "-"
            last_good = (
                f"{model.last_known_good_context:,}" if model.last_known_good_context else "-"
            )
            last_bad = f"{model.last_known_bad_context:,}" if model.last_known_bad_context else "-"

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
                status,
            )
        console.print(table)

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
                registry.update_model_by_id(model)
            registry.save()
            logger.success(f"Reset {len(models_to_test)} models for re-testing")

        if test_all:
            # Filter out embedding models for --all flag
            tester = ContextTester(verbose=verbose, fast_mode=fast)
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

        tester = ContextTester(verbose=verbose, fast_mode=fast)

        if ctx is not None:
            if test_all:
                updated_models = _test_all_models_at_ctx(
                    tester,
                    models_to_test,
                    ctx,
                    registry,
                )
                _print_final_results(updated_models)
            else:
                _test_single_model(tester, models_to_test[0], ctx, registry, force)
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
            logger.debug(f"\n[bold cyan]Testing model: {model.id}[/bold cyan]")
            logger.debug(f"Declared context limit: {model.context_limit:,} tokens")
            logger.debug(f"Threshold: {threshold:,} tokens")

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
                logger.debug(f"✗ Test failed: {error_msg}")

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
        """Run inference on a specified model."""
        setup_logging(verbose=verbose)

        if not out_ctx:
            out_ctx = -1  # Default to unlimited

        # Handle --text and --text_file for simple prompts without file_prompt
        if not file_prompt and (text or text_file):
            if text_file:
                try:
                    text_path = Path(text_file).expanduser()
                    if not text_path.exists():
                        logger.error(f"Text file not found: {text_file}")
                        return
                    text_content = text_path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.debug(f"Error reading text file: {e}")
                    return
            else:
                text_content = text

            # Replace {{text}} placeholder in the prompt
            actual_prompt = prompt.replace("{{text}}", text_content)
        # Handle prompt file loading if specified
        elif file_prompt:
            # Parse dictionary parameters
            prompt_params = {}
            if dict_params:
                # Support both comma-separated and space-separated formats
                if "," in dict_params:
                    # Format: "key1=value1,key2=value2"
                    pairs = dict_params.split(",")
                else:
                    # Format: "key1=value1 key2=value2" (fire might split this)
                    # For now, assume comma-separated
                    pairs = dict_params.split(",")

                for pair in pairs:
                    pair = pair.strip()
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        prompt_params[key.strip()] = value.strip()
                    else:
                        logger.debug(
                            f"Warning: Invalid parameter format '{pair}'. Expected 'key=value'.",
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
                    logger.debug(f"Error reading text file: {e}")
                    return
            elif text:
                prompt_params["text"] = text

            # Load and resolve prompt from TOML file
            try:
                prompt_path = Path(file_prompt).expanduser()
                if not prompt_path.exists():
                    logger.error(f"Prompt file not found: {file_prompt}")
                    return

                # Check if prompt contains commas (multiple templates)
                if "," in prompt:
                    # Split by comma and load each template
                    prompt_names = [name.strip() for name in prompt.split(",") if name.strip()]
                    concatenated_prompts = []
                    all_placeholders_resolved = []
                    all_placeholders_unresolved = []

                    if verbose:
                        logger.debug(
                            f"Loading multiple prompts: {', '.join(prompt_names)}",
                        )

                    for prompt_name in prompt_names:
                        resolved_prompt = load_single_prompt(
                            toml_path=prompt_path,
                            prompt_name=prompt_name,
                            verbose=verbose,
                            **prompt_params,
                        )
                        concatenated_prompts.append(resolved_prompt.resolved)
                        all_placeholders_resolved.extend(
                            resolved_prompt.placeholders_resolved,
                        )
                        all_placeholders_unresolved.extend(
                            resolved_prompt.placeholders_unresolved,
                        )

                        if verbose:
                            logger.debug(
                                f"Loaded prompt '{prompt_name}' from {file_prompt}",
                            )

                    # Concatenate all prompts with double newline separator
                    actual_prompt = "\n\n".join(concatenated_prompts)

                    if verbose:
                        logger.debug(f"Concatenated {len(prompt_names)} prompts")
                        if all_placeholders_resolved:
                            unique_resolved = list(set(all_placeholders_resolved))
                            logger.debug(
                                f"Resolved placeholders: {', '.join(unique_resolved)}",
                            )
                        if all_placeholders_unresolved:
                            unique_unresolved = list(set(all_placeholders_unresolved))
                            logger.debug(
                                f"Warning: Unresolved placeholders: {', '.join(unique_unresolved)}",
                            )
                else:
                    # Single prompt - existing behavior
                    resolved_prompt = load_single_prompt(
                        toml_path=prompt_path,
                        prompt_name=prompt,  # Now refers to prompt name in TOML
                        verbose=verbose,
                        **prompt_params,
                    )

                    actual_prompt = resolved_prompt.resolved

                    if verbose:
                        logger.debug(f"Loaded prompt '{prompt}' from {file_prompt}")
                        if resolved_prompt.placeholders_resolved:
                            logger.debug(
                                f"Resolved placeholders: {', '.join(resolved_prompt.placeholders_resolved)}",
                            )
                        if resolved_prompt.placeholders_unresolved:
                            logger.debug(
                                f"Warning: Unresolved placeholders: {', '.join(resolved_prompt.placeholders_unresolved)}",
                            )

            except Exception as e:
                logger.debug(f"Error loading prompt from file: {e}")
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
                logger.error("No model specified and no last-used model found.")
                logger.debug("Please specify a model with -m or --model_id")
                return
            if verbose:
                logger.debug(f"Using last-used model: {model_id}")

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
                f"Force reload requested, loading with context {in_ctx:,}",
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
                        f"Parsed out_ctx '{out_ctx}' as {parsed_out_ctx} tokens",
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
                        f"Parsed in_ctx '{in_ctx}' as {parsed_in_ctx} tokens",
                    )
                in_ctx = parsed_in_ctx
            except ValueError as e:
                logger.error(f"{e}")
                return

        manager = InferenceManager(registry=registry, verbose=verbose)

        # Handle streaming vs regular inference
        if stream:
            try:
                # Show status only in verbose mode
                if verbose:
                    print(f"\nStreaming inference on {model.id}...", file=sys.stderr)

                # Callback to print tokens to stdout as they arrive
                def print_token(token: str) -> None:
                    print(token, end="", flush=True, file=sys.stdout)

                # Stream the response
                for _token in manager.stream_infer(
                    model_id=model.id,  # Use the full ID for inference
                    prompt=actual_prompt,  # Use the resolved prompt
                    in_ctx=in_ctx,
                    out_ctx=out_ctx,
                    temperature=param_temp,
                    top_k=param_top_k,
                    top_p=param_top_p,
                    repeat_penalty=param_repeat,
                    min_p=param_min_p,
                    on_token=print_token,
                    stream_timeout=stream_timeout,
                ):
                    # Tokens are already printed by callback, just iterate
                    pass

                # Add newline after streaming completes
                print("", file=sys.stdout)

            except Exception as e:
                # Use stderr for error messages
                print(f"\nStreaming inference failed: {e}", file=sys.stderr)
        else:
            # Regular non-streaming inference
            # Show status only in verbose mode
            if verbose:
                with console.status(f"Running inference on {model.id}..."):
                    result = manager.infer(
                        model_id=model.id,  # Use the full ID for inference
                        prompt=actual_prompt,  # Use the resolved prompt
                        in_ctx=in_ctx,
                        out_ctx=out_ctx,
                        temperature=param_temp,
                        top_k=param_top_k,
                        top_p=param_top_p,
                        repeat_penalty=param_repeat,
                        min_p=param_min_p,
                    )
            else:
                result = manager.infer(
                    model_id=model.id,  # Use the full ID for inference
                    prompt=actual_prompt,  # Use the resolved prompt
                    in_ctx=in_ctx,
                    out_ctx=out_ctx,
                    temperature=param_temp,
                    top_k=param_top_k,
                    top_p=param_top_p,
                    repeat_penalty=param_repeat,
                    min_p=param_min_p,
                )

            if result["succeeded"]:
                if verbose:
                    # Use stderr for debug info to avoid parsing issues
                    print("\nModel Response:", file=sys.stderr)
                # Always output the actual response to stdout
                print(result["response"], file=sys.stdout)
            else:
                # Use stderr for error messages
                print(f"Inference failed: {result['error']}", file=sys.stderr)

    def check_health(self, verbose: bool = False) -> None:
        """Check database health and backup status."""
        setup_logging(verbose=verbose)

        models_file = get_default_models_file()
        logger.debug("[blue]Database Health Check[/blue]")
        logger.debug(f"Registry file: {models_file}")

        # Check if registry exists
        if not models_file.exists():
            logger.debug("✗ Registry file not found")
            return

        logger.success("✓ Registry file exist")

        # Check if registry is valid JSON
        try:
            with models_file.open() as f:
                json.load(f)
            logger.success("✓ Registry file is valid JSO")
        except json.JSONDecodeError as e:
            logger.debug(f"✗ Registry file is corrupted: {e}")

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
                    f"⚠ Found {len(invalid_models)} models with integrity issues",
                )
                if verbose:
                    for model_path in invalid_models:
                        logger.debug(f"  - {model_path}")
            else:
                logger.success("✓ All models pass integrity check")

        except (ModelRegistryError, OSError, json.JSONDecodeError) as e:
            logger.debug(f"✗ Failed to load registry: {e}")

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
                    status = "✗"

                logger.debug(
                    f"  {status} {backup_file.name} ({size_kb}KB, {mtime.strftime('%Y-%m-%d %H:%M')})",
                )

            if len(backup_files) > 5:
                logger.debug(f"  ... and {len(backup_files) - 5} more")
        else:
            logger.debug("No backup files found")

    def save_configs(self, flash: bool = False, verbose: bool = False) -> None:
        """Save tested context limits to LM Studio concrete config files."""
        setup_logging(verbose=verbose)

        # Load the model registry
        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        # Filter models with tested context
        models_with_context = [m for m in models if m.tested_max_context]

        if not models_with_context:
            logger.debug("No models with tested context limits found.")
            logger.debug("Run 'lmstrix test' to test model context limits first.")
            return

        logger.debug(
            f"[blue]Found {len(models_with_context)} models with tested context limits[/blue]",
        )

        # Get LM Studio path
        try:
            lms_path = get_lmstudio_path()
        except Exception as e:
            logger.debug(f"Failed to find LM Studio installation: {e}")
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
                f"✗ Failed to save {failed} model configurations",
            )

        if flash:
            gguf_count = sum(1 for m in models_with_context if str(m.path).endswith(".gguf"))
            if gguf_count > 0:
                logger.debug(
                    f"[blue]Flash attention enabled for {gguf_count} GGUF models[/blue]",
                )

    def show_help(self) -> None:
        """Show comprehensive help text."""
        console.print("[bold cyan]LMStrix - LM Studio Model Testing Toolkit[/bold cyan]")
        console.print("\n[cyan]Available commands:[/cyan]")
        console.print(
            "  [green]scan[/green]            Scan for LM Studio models and update registry",
        )
        console.print("    --failed          Re-scan only previously failed models")
        console.print("    --reset           Re-scan all models (clear test data)")
        console.print("    --verbose         Enable verbose output")
        console.print("")
        console.print(
            "  [green]list[/green]            List all models with their test status",
        )
        console.print(
            "    --sort id|ctx|dtx|size|smart  Sort by: id, tested context, declared context, size, smart",
        )
        console.print("    --show id|path|json     Output format")
        console.print("    --verbose         Enable verbose output")
        console.print("")
        console.print("  [green]test[/green]            Test model context limits")
        console.print("    MODEL_ID          Test specific model")
        console.print("    --all             Test all untested models")
        console.print("    --reset           Re-test all models")
        console.print("    --ctx SIZE        Test specific context size")
        console.print(
            "    --threshold SIZE  Max context for initial testing (default: 31744)",
        )
        console.print(
            "    --fast            Skip semantic verification (only test if inference completes)",
        )
        console.print("    --verbose         Enable verbose output")
        console.print("")
        console.print("  [green]infer[/green]           Run inference on a model")
        console.print("    PROMPT MODEL_ID   Required prompt and model")
        console.print(
            "    --out_ctx NUM|%   Maximum tokens to generate (e.g., 500 or '80%')",
        )
        console.print("    --in_ctx NUM      Context size for loading model")
        console.print("    --file_prompt PATH Load prompt from TOML file")
        console.print("    --dict PARAMS     Parameters as key=value pairs")
        console.print("    --temperature NUM Temperature for generation")
        console.print("    --reload          Force reload model")
        console.print("    --verbose         Enable verbose output")
        console.print("")
        console.print(
            "  [green]health[/green]          Check database health and backups",
        )
        console.print("    --verbose         Show detailed health information")
        console.print("")
        console.print(
            "  [green]save[/green]            Save tested contexts to LM Studio configs",
        )
        console.print("    --flash           Enable flash attention for GGUF models")
        console.print("    --verbose         Enable verbose output")
        console.print("")
        console.print("Examples:")
        console.print("  lmstrix scan --verbose")
        console.print("  lmstrix list --sort ctx")
        console.print("  lmstrix test --all")
        console.print("  lmstrix test my-model --ctx 8192")
        console.print('  lmstrix infer "Hello world" my-model')
        console.print("  lmstrix save --flash")
