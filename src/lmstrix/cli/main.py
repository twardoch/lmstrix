"""Command-line interface for LMStrix."""

import json
import time
from datetime import datetime

import fire
from rich.console import Console
from rich.table import Table

from lmstrix.api.exceptions import APIConnectionError, ModelRegistryError
from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference import InferenceEngine
from lmstrix.core.models import ContextTestStatus, Model, ModelRegistry
from lmstrix.loaders.model_loader import (
    load_model_registry,
    scan_and_update_registry,
)
from lmstrix.utils import get_context_test_log_path, setup_logging
from lmstrix.utils.paths import get_default_models_file

console = Console()


def _get_models_to_test(
    registry: ModelRegistry,
    test_all: bool,
    ctx: int | None,
    model_id: str | None,
    reset: bool = False,
) -> list[Model]:
    """Filter and return a list of models to be tested."""
    tester = ContextTester()  # Create a temporary tester for _is_embedding_model

    if not test_all:
        if not model_id:
            console.print("[red]Error: You must specify a model ID or use the --all flag.[/red]")
            return []
        model = registry.find_model(model_id)
        if not model:
            console.print(f"[red]Error: Model '{model_id}' not found in registry.[/red]")
            return []
        if tester._is_embedding_model(model):
            console.print(
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
        console.print(
            f"[yellow]Excluded {skipped_embedding} embedding models from testing.[/yellow]",
        )

    if not models_to_test:
        if ctx is not None:
            console.print(
                "[yellow]No LLM models found to test at the specified context size.[/yellow]",
            )
            console.print(
                "[dim]Models may already be tested or context exceeds their limits.[/dim]",
            )
        elif reset:
            console.print(
                "[yellow]No models found to test (check model availability).[/yellow]",
            )
        else:
            console.print(
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
        console.print(f"[red]Invalid sort option: {sort_by}. Using default (id).[/red]")
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
        console.print(
            f"[yellow]Warning: Specified context ({ctx:,}) exceeds model's declared limit ({model.context_limit:,}). Skipping test.[/yellow]",
        )
        return

    if model.last_known_bad_context and ctx >= model.last_known_bad_context:
        max_safe_context = int(model.last_known_bad_context * 0.75)
        console.print(
            f"[red]Error: Specified context ({ctx:,}) is at or above the last known bad context ({model.last_known_bad_context:,}).[/red]",
        )
        console.print(
            f"[yellow]The maximum safe context to test is {max_safe_context:,} (75% of last bad).[/yellow]",
        )
        return

    console.print(
        f"\n[bold cyan]Testing model: {model.id} at specific context: {ctx:,}[/bold cyan]",
    )
    console.print(f"[dim]Declared context limit: {model.context_limit:,} tokens[/dim]")

    log_path = get_context_test_log_path(model.id)

    model.context_test_status = ContextTestStatus.TESTING
    model.context_test_date = datetime.now()
    registry.update_model_by_id(model)

    result = tester._test_at_context(model.id, ctx, log_path, model, registry)

    if result.load_success and result.inference_success:
        console.print(f"[green]✓ Test successful at context {ctx:,}[/green]")
        console.print(f"[dim]Response length: {len(result.response)} chars[/dim]")
        model.last_known_good_context = ctx
        if not model.tested_max_context or ctx > model.tested_max_context:
            model.tested_max_context = ctx
        model.context_test_status = ContextTestStatus.COMPLETED
    else:
        error_type = "load" if not result.load_success else "inference"
        console.print(f"[red]✗ Test failed at context {ctx:,} ({error_type} failed)[/red]")
        console.print(f"[dim]Error: {result.error}[/dim]")
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
    console.print(
        f"[bold]Testing {len(models_to_test)} models at context size {ctx:,}[/bold]\n",
    )

    updated_models = []
    for i, model in enumerate(models_to_test, 1):
        print(f"[{i}/{len(models_to_test)}] Testing {model.id}...")

        if i > 1:
            print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
            time.sleep(3.0)

        log_path = get_context_test_log_path(model.id)

        model.context_test_status = ContextTestStatus.TESTING
        model.context_test_date = datetime.now()
        registry.update_model_by_id(model)

        result = tester._test_at_context(model.id, ctx, log_path, model, registry)

        if result.load_success and result.inference_success:
            console.print(f"  ✓ Success at context {ctx:,}")
            model.last_known_good_context = ctx
            if not model.tested_max_context or ctx > model.tested_max_context:
                model.tested_max_context = ctx
            model.context_test_status = ContextTestStatus.TESTING
        else:
            error_type = "load" if not result.load_success else "inference"
            console.print(f"  ✗ Failed at context {ctx:,} ({error_type} failed)")
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
    console.print(
        f"[bold]Starting optimized batch testing for {len(models_to_test)} models[/bold]",
    )
    console.print(f"[dim]Threshold: {threshold:,} tokens[/dim]\n")

    return tester.test_all_models(
        models_to_test,
        threshold=threshold,
        registry=registry,
    )


def _print_final_results(updated_models: list[Model]) -> None:
    """Print the final results table."""
    print(f"\n{'=' * 60}")
    print("Final Results:")
    print(f"{'=' * 60}\n")

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

    console.print(table)


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
            console.print("[red]Error: Cannot use --failed and --all together.[/red]")
            return

        try:
            with console.status("Scanning for models..."):
                registry = scan_and_update_registry(
                    rescan_failed=failed,
                    rereset=reset,
                    verbose=verbose,
                )

            console.print("[green]✓ Model scan complete.[/green]")

            # Show summary of what was found
            models = registry.list_models()
            if models:
                console.print(f"[blue]Found {len(models)} models in registry[/blue]")
            else:
                console.print(
                    "[yellow]No models found. Make sure LM Studio is running "
                    "and has models downloaded.[/yellow]",
                )

        except (APIConnectionError, ModelRegistryError, OSError) as e:
            console.print(f"[red]✗ Scan failed: {e}[/red]")
            console.print("[yellow]Check that LM Studio is running and accessible.[/yellow]")
            if verbose:
                console.print(f"[dim]Error details: {e}[/dim]")
            return

        self.list()

    def list(self, sort: str = "id", show: str | None = None, verbose: bool = False) -> None:
        """List all models from the registry with their test status.

        Args:
            sort: Sort order. Options: id, idd, ctx, ctxd, dtx, dtxd, size, sized (d = descending).
            show: Output format. Options: id (plain IDs), path (relative paths), json (JSON array).
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        if not models:
            console.print(
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
        else:
            console.print(f"[red]Invalid sort option: {sort}. Using default (id).[/red]")
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
                console.print(f"[red]Invalid show option: {show}. Options: id, path, json.[/red]")
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
        console.print(table)

    def test(
        self,
        model_id: str | None = None,
        all: bool = False,
        reset: bool = False,
        threshold: int = 31744,
        ctx: int | None = None,
        sort: str = "id",
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
            verbose: Enable verbose output.
        """
        setup_logging(verbose=verbose)
        registry = load_model_registry(verbose=verbose)

        # Handle both --all and --test_all flags
        test_all_models = all

        if test_all_models and model_id:
            console.print("[red]Error: Cannot use --all and specify a model ID together.[/red]")
            return

        models_to_test = _get_models_to_test(registry, test_all_models, ctx, model_id, reset)
        if not models_to_test:
            return

        # If reset flag is used, clear test results for all models being tested
        if reset:
            console.print("[yellow]Resetting test results for selected models...[/yellow]")
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
            console.print(f"[green]Reset {len(models_to_test)} models for re-testing.[/green]")

        if test_all_models:
            # Filter out embedding models for --all flag
            tester = ContextTester(verbose=verbose)
            models_to_test = tester._filter_models_for_testing(models_to_test)
            if not models_to_test:
                console.print(
                    "[yellow]No LLM models found to test after filtering embedding models.[/yellow]",
                )
                return
            # Custom sorting for optimal testing: size_bytes + context_limit*100000
            # This prioritizes smaller models first, then lower context within similar sizes
            models_to_test = sorted(
                models_to_test,
                key=lambda m: m.size + (m.context_limit * 100_000),
            )
            console.print(
                "[cyan]Sorting models by optimal testing order (size + context priority).[/cyan]",
            )

        tester = ContextTester(verbose=verbose)

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
            console.print(f"\n[bold cyan]Testing model: {model.id}[/bold cyan]")
            console.print(f"[dim]Declared context limit: {model.context_limit:,} tokens[/dim]")
            console.print(f"[dim]Threshold: {threshold:,} tokens[/dim]")

            max_test_context = min(threshold, model.context_limit)
            updated_model = tester.test_model(
                model,
                max_context=max_test_context,
                registry=registry,
            )

            if updated_model.context_test_status.value == "completed":
                console.print(
                    f"[green]✓ Test complete. Optimal context: {updated_model.tested_max_context:,}[/green]",
                )
            else:
                error_msg = getattr(updated_model, "error_msg", "Unknown error")
                console.print(f"[red]✗ Test failed: {error_msg}[/red]")

    def infer(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = -1,
        temperature: float = 0.7,
        verbose: bool = False,
    ) -> None:
        """Run inference on a specified model.

        Args:
            prompt: The text prompt to send to the model.
            model_id: The ID of the model to use for inference.
            max_tokens: Maximum tokens to generate (-1 for unlimited).
            temperature: The sampling temperature.
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        registry = load_model_registry(verbose=verbose)
        model = registry.find_model(model_id)
        if not model:
            console.print(f"[red]Error: Model '{model_id}' not found in registry.[/red]")
            return

        engine = InferenceEngine(model_registry=registry, verbose=verbose)

        with console.status(f"Running inference on {model.id}..."):
            result = engine.infer(
                model_id=model.id,  # Use the full ID for inference
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        if result.succeeded:
            console.print("\n[green]Model Response:[/green]")
            console.print(result.response)
            console.print(
                f"\n[dim]Tokens: {result.tokens_used}, Time: {result.inference_time:.2f}s[/dim]",
            )
        else:
            console.print(f"[red]Inference failed: {result.error}[/red]")

    def health(self, verbose: bool = False) -> None:
        """Check database health and backup status.

        Args:
            verbose: Enable verbose output.
        """
        setup_logging(verbose=verbose)

        models_file = get_default_models_file()
        console.print("[blue]Database Health Check[/blue]")
        console.print(f"Registry file: {models_file}")

        # Check if registry exists
        if not models_file.exists():
            console.print("[red]✗ Registry file not found[/red]")
            return

        console.print("[green]✓ Registry file exists[/green]")

        # Check if registry is valid JSON
        try:
            with models_file.open() as f:
                json.load(f)
            console.print("[green]✓ Registry file is valid JSON[/green]")
        except json.JSONDecodeError as e:
            console.print(f"[red]✗ Registry file is corrupted: {e}[/red]")

        # Load with validation
        try:
            registry = load_model_registry(verbose=verbose)
            model_count = len(registry)
            console.print(f"[green]✓ Successfully loaded {model_count} models[/green]")

            # Check for validation issues
            invalid_models = []
            for model_path, model in registry.models.items():
                if not model.validate_integrity():
                    invalid_models.append(model_path)

            if invalid_models:
                console.print(
                    f"[yellow]⚠ Found {len(invalid_models)} models with integrity issues[/yellow]",
                )
                if verbose:
                    for model_path in invalid_models:
                        console.print(f"  - {model_path}")
            else:
                console.print("[green]✓ All models pass integrity checks[/green]")

        except (ModelRegistryError, OSError, json.JSONDecodeError) as e:
            console.print(f"[red]✗ Failed to load registry: {e}[/red]")

        # Check backup files
        backup_pattern = f"{models_file.stem}.backup_*"
        backup_files = list(models_file.parent.glob(backup_pattern))

        if backup_files:
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            console.print(f"[blue]Found {len(backup_files)} backup files:[/blue]")

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

                console.print(
                    f"  {status} {backup_file.name} ({size_kb}KB, {mtime.strftime('%Y-%m-%d %H:%M')})",
                )

            if len(backup_files) > 5:
                console.print(f"  ... and {len(backup_files) - 5} more")
        else:
            console.print("[yellow]No backup files found[/yellow]")


def main() -> None:
    """Main entry point for the CLI."""
    fire.Fire(LMStrixCLI)


if __name__ == "__main__":
    main()
