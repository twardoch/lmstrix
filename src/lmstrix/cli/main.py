"""Command-line interface for LMStrix."""

import json
import time
from datetime import datetime

import fire
from rich.console import Console
from rich.table import Table

from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference import InferenceEngine
from lmstrix.core.models import ContextTestStatus
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)
from lmstrix.utils import get_context_test_log_path, setup_logging

console = Console()


class LMStrixCLI:
    """A CLI for testing and managing LM Studio models."""

    def scan(self, failed: bool = False, all: bool = False, verbose: bool = False) -> None:
        """Scan for LM Studio models and update the local registry.

        Args:
            failed: Re-scan only models that previously failed.
            all: Re-scan all models (clear existing test data).
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        if failed and all:
            console.print("[red]Error: Cannot use --failed and --all together.[/red]")
            return

        with console.status("Scanning for models..."):
            scan_and_update_registry(rescan_failed=failed, rescan_all=all, verbose=verbose)
        console.print("[green]Model scan complete.[/green]")
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
        threshold: int = 102400,
        ctx: int | None = None,
        sort: str = "id",
        verbose: bool = False,
    ) -> None:
        """Test the context limits for models.

        Args:
            model_id: The specific model ID to test.
            all: Flag to test all untested or previously failed models.
            threshold: Maximum context size for initial testing (default: 102400).
                      Prevents system crashes from very large contexts.
            ctx: Test only this specific context value (skips if > declared context).
            sort: Sort order for --all. Options: id, idd, ctx, ctxd, dtx, dtxd, size, sized (d = descending).
            verbose: Enable verbose output.
        """
        # Configure logging based on verbose flag
        setup_logging(verbose=verbose)

        registry = load_model_registry(verbose=verbose)
        models_to_test = []

        if all:
            # Get all models that need testing based on --ctx option
            if ctx is not None:
                # With --ctx, test all models except those already tested (completed status)
                models_to_test = []
                for m in registry.list_models():
                    # Skip if already tested
                    if m.context_test_status.value == "completed":
                        continue
                    # Skip if ctx exceeds declared limit
                    if ctx > m.context_limit:
                        continue
                    # Skip if ctx is at or above last known bad context
                    if m.last_known_bad_context and ctx >= m.last_known_bad_context:
                        continue
                    models_to_test.append(m)

                if not models_to_test:
                    console.print(
                        "[yellow]No models to test at the specified context size.[/yellow]",
                    )
                    console.print(
                        "[dim]Models may already be tested or context exceeds their limits.[/dim]",
                    )
                    return
                console.print(f"Testing {len(models_to_test)} models at context size {ctx:,}...")
            else:
                # Normal --all behavior: test untested or failed models
                models_to_test = [
                    m for m in registry.list_models() if m.context_test_status.value != "completed"
                ]
                if not models_to_test:
                    console.print(
                        "[green]All models have already been successfully tested.[/green]",
                    )
                    return
                console.print(f"Testing {len(models_to_test)} models...")

            # Apply sorting
            sort_key = sort.lower()
            reverse = sort_key.endswith("d") and len(sort_key) > 1

            if sort_key in ("id", "idd"):
                models_to_test = sorted(models_to_test, key=lambda m: m.id, reverse=reverse)
            elif sort_key in ("ctx", "ctxd"):
                models_to_test = sorted(
                    models_to_test,
                    key=lambda m: m.tested_max_context or 0,
                    reverse=reverse,
                )
            elif sort_key in ("dtx", "dtxd"):
                models_to_test = sorted(
                    models_to_test,
                    key=lambda m: m.context_limit,
                    reverse=reverse,
                )
            elif sort_key in ("size", "sized"):
                models_to_test = sorted(models_to_test, key=lambda m: m.size, reverse=reverse)
            else:
                console.print(f"[red]Invalid sort option: {sort}. Using default (id).[/red]")
                models_to_test = sorted(models_to_test, key=lambda m: m.id)
        elif model_id:
            model = registry.find_model(model_id)
            if not model:
                console.print(f"[red]Error: Model '{model_id}' not found in registry.[/red]")
                return
            models_to_test.append(model)
        else:
            console.print("[red]Error: You must specify a model ID or use the --all flag.[/red]")
            return

        tester = ContextTester(verbose=verbose)

        # If --ctx is specified, use it for specific context testing
        if ctx is not None and not all:
            model = models_to_test[0]
            if ctx > model.context_limit:
                console.print(
                    f"[yellow]Warning: Specified context ({ctx:,}) exceeds model's declared limit ({model.context_limit:,}). Skipping test.[/yellow]",
                )
                return

            # Check against last_known_bad_context
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

            # Update model status
            model.context_test_status = ContextTestStatus.TESTING
            model.context_test_date = datetime.now()
            registry.update_model(model.id, model)
            save_model_registry(registry)

            # Test at specific context
            result = tester._test_at_context(model.id, ctx, log_path, model, registry)

            if result.load_success and result.inference_success:
                console.print(f"[green]✓ Test successful at context {ctx:,}[/green]")
                console.print(f"[dim]Response length: {len(result.response)} chars[/dim]")

                # Update model with successful test results
                model.last_known_good_context = ctx
                # Update tested_max_context if this is larger than previous
                if not model.tested_max_context or ctx > model.tested_max_context:
                    model.tested_max_context = ctx
                # Mark as completed since we successfully tested at this context
                model.context_test_status = ContextTestStatus.COMPLETED
                model.context_test_date = datetime.now()

                # Save the updated model
                registry.update_model(model.id, model)
                save_model_registry(registry)
            else:
                error_type = "load" if not result.load_success else "inference"
                console.print(f"[red]✗ Test failed at context {ctx:,} ({error_type} failed)[/red]")
                console.print(f"[dim]Error: {result.error}[/dim]")

                # Update model with failed test results
                model.last_known_bad_context = ctx
                model.context_test_status = ContextTestStatus.FAILED
                model.context_test_date = datetime.now()

                # Save the updated model
                registry.update_model(model.id, model)
                save_model_registry(registry)

            return

        if all:
            if ctx is not None:
                # Test all models at a specific context size
                console.print(
                    f"[bold]Testing {len(models_to_test)} models at context size {ctx:,}[/bold]\n",
                )

                updated_models = []
                for i, model in enumerate(models_to_test, 1):
                    print(f"[{i}/{len(models_to_test)}] Testing {model.id}...")

                    # Add delay between models
                    if i > 1:
                        print("  ⏳ Waiting 3 seconds before next model (resource cleanup)...")
                        time.sleep(3.0)

                    log_path = get_context_test_log_path(model.id)

                    # Update model status
                    model.context_test_status = ContextTestStatus.TESTING
                    model.context_test_date = datetime.now()
                    registry.update_model(model.id, model)
                    save_model_registry(registry)

                    # Test at specific context
                    result = tester._test_at_context(model.id, ctx, log_path, model, registry)

                    if result.load_success and result.inference_success:
                        console.print(f"  ✓ Success at context {ctx:,}")

                        # Update model with successful test results
                        model.last_known_good_context = ctx
                        # Update tested_max_context if this is larger than previous
                        if not model.tested_max_context or ctx > model.tested_max_context:
                            model.tested_max_context = ctx
                        # Don't mark as completed since we only tested one context
                        model.context_test_status = ContextTestStatus.TESTING
                    else:
                        error_type = "load" if not result.load_success else "inference"
                        console.print(f"  ✗ Failed at context {ctx:,} ({error_type} failed)")

                        # Update model with failed test results
                        model.last_known_bad_context = ctx
                        model.context_test_status = ContextTestStatus.FAILED

                    model.context_test_date = datetime.now()

                    # Save the updated model
                    registry.update_model(model.id, model)
                    save_model_registry(registry)
                    updated_models.append(model)
            else:
                # Use the optimized batch testing for multiple models
                console.print(
                    f"[bold]Starting optimized batch testing for {len(models_to_test)} models[/bold]",
                )
                console.print(f"[dim]Threshold: {threshold:,} tokens[/dim]\n")

                updated_models = tester.test_all_models(
                    models_to_test,
                    threshold=threshold,
                    registry=registry,
                )

            # Print final summary table
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
                status = (
                    "✓ Completed" if model.context_test_status.value == "completed" else "✗ Failed"
                )
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
        else:
            # Single model testing - use the original approach
            model = models_to_test[0]
            console.print(f"\n[bold cyan]Testing model: {model.id}[/bold cyan]")
            console.print(f"[dim]Declared context limit: {model.context_limit:,} tokens[/dim]")
            console.print(f"[dim]Threshold: {threshold:,} tokens[/dim]")

            # Use threshold to limit initial test size and prevent crashes
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


def main() -> None:
    """Main entry point for the CLI."""
    fire.Fire(LMStrixCLI)


if __name__ == "__main__":
    main()
