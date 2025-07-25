"""Command-line interface for LMStrix."""

import asyncio

import fire
from rich.console import Console
from rich.table import Table

from lmstrix.core.context_tester import ContextTester
from lmstrix.core.inference import InferenceEngine
from lmstrix.loaders.model_loader import (
    load_model_registry,
    save_model_registry,
    scan_and_update_registry,
)

console = Console()


class LMStrixCLI:
    """A CLI for testing and managing LM Studio models."""

    def scan(self, verbose: bool = False) -> None:
        """Scan for LM Studio models and update the local registry."""
        with console.status("Scanning for models..."):
            scan_and_update_registry(verbose=verbose)
        console.print("[green]Model scan complete.[/green]")
        self.list()

    def list(self, verbose: bool = False) -> None:
        """List all models from the registry with their test status."""
        registry = load_model_registry(verbose=verbose)
        models = registry.list_models()

        if not models:
            console.print(
                "[yellow]No models found. Run 'lmstrix scan' to discover models.[/yellow]",
            )
            return

        table = Table(title="LM Studio Models")
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Size (GB)", style="magenta")
        table.add_column("Declared Ctx", style="yellow")
        table.add_column("Tested Ctx", style="green")
        table.add_column("Status", style="blue")

        for model in sorted(models, key=lambda m: m.id):
            tested_ctx = f"{model.tested_max_context:,}" if model.tested_max_context else "-"
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
                status,
            )
        console.print(table)

    def test(self, model_id: str | None = None, all: bool = False, verbose: bool = False) -> None:
        """Test the context limits for models.

        Args:
            model_id: The specific model ID to test.
            all: Flag to test all untested or previously failed models.
            verbose: Enable verbose output.
        """
        registry = load_model_registry(verbose=verbose)
        models_to_test = []

        if all:
            models_to_test = [
                m for m in registry.list_models() if m.context_test_status.value != "completed"
            ]
            if not models_to_test:
                console.print("[green]All models have already been successfully tested.[/green]")
                return
            console.print(f"Testing {len(models_to_test)} models...")
        elif model_id:
            model = registry.get_model(model_id)
            if not model:
                console.print(f"[red]Error: Model '{model_id}' not found in registry.[/red]")
                return
            models_to_test.append(model)
        else:
            console.print("[red]Error: You must specify a model ID or use the --all flag.[/red]")
            return

        tester = ContextTester()
        for model in models_to_test:
            updated_model = asyncio.run(tester.test_model(model))
            registry.update_model(
                updated_model.id, updated_model
            )  # Update the model in the registry
            save_model_registry(registry)  # Save after each test

            if updated_model.context_test_status.value == "completed":
                console.print(
                    f"[green]✓ Test for {model.id} complete. Optimal context: {updated_model.tested_max_context:,}[/green]",
                )
            else:
                console.print(f"[red]✗ Test for {model.id} failed. Check logs for details.[/red]")

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
        registry = load_model_registry(verbose=verbose)
        engine = InferenceEngine(model_registry=registry, verbose=verbose)

        with console.status(f"Running inference on {model_id}..."):
            result = asyncio.run(
                engine.infer(
                    model_id=model_id,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
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
