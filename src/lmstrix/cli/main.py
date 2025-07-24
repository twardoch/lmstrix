# this_file: src/lmstrix/cli/main.py
"""Command-line interface for LMStrix."""

import asyncio

import fire
from rich.console import Console
from rich.table import Table

from lmstrix import LMStrix

console = Console()


class LMStrixCLI:
    """LMStrix command-line interface."""

    def __init__(
        self, endpoint: str = "http://localhost:1234/v1", verbose: bool = False
    ):
        """Initialize the CLI.

        Args:
            endpoint: LM Studio API endpoint.
            verbose: Enable verbose output.
        """
        self.endpoint = endpoint
        self.verbose = verbose
        self.client = LMStrix(endpoint=endpoint, verbose=verbose)

    def models(self, action: str = "list", model_id: str = None):
        """Manage models.

        Args:
            action: Action to perform (list, scan, load).
            model_id: Model ID for specific actions.
        """
        if action == "list":
            self._list_models()
        elif action == "scan":
            console.print("[yellow]Model scanning not yet implemented[/yellow]")
        elif action == "load" and model_id:
            console.print(
                f"[yellow]Loading model {model_id} not yet implemented[/yellow]"
            )
        else:
            console.print("[red]Invalid action or missing model_id[/red]")

    def _list_models(self):
        """List all available models."""
        models = asyncio.run(self.client.list_models())

        if not models:
            console.print(
                "[yellow]No models found. Run 'lmstrix models scan' to scan for models.[/yellow]"
            )
            return

        table = Table(title="Available Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Size", style="magenta")
        table.add_column("Context", style="green")
        table.add_column("Tools", style="yellow")
        table.add_column("Vision", style="blue")

        for model in models:
            table.add_row(
                model.id,
                f"{model.size / (1024**3):.1f} GB",
                f"{model.context_limit:,}",
                "✓" if model.supports_tools else "✗",
                "✓" if model.supports_vision else "✗",
            )

        console.print(table)

    def infer(
        self,
        prompt: str,
        model: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """Run inference on a model.

        Args:
            prompt: The prompt text.
            model: Model ID to use (if not specified, uses first available).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        """
        if not model:
            models = asyncio.run(self.client.list_models())
            if not models:
                console.print("[red]No models available[/red]")
                return
            model = models[0].id
            console.print(f"[dim]Using model: {model}[/dim]")

        with console.status(f"Running inference on {model}..."):
            result = asyncio.run(
                self.client.infer(
                    model_id=model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            )

        if result.succeeded:
            console.print("\n[green]Response:[/green]")
            console.print(result.response)
            console.print(
                f"\n[dim]Tokens: {result.tokens_used}, Time: {result.inference_time:.2f}s[/dim]"
            )
        else:
            console.print(f"[red]Inference failed: {result.error}[/red]")

    def optimize(self, model: str, all: bool = False):
        """Run context optimization for models.

        Args:
            model: Model ID to optimize.
            all: Optimize all models.
        """
        if all:
            console.print("[yellow]Optimizing all models not yet implemented[/yellow]")
        elif model:
            with console.status(f"Optimizing context for {model}..."):
                result = asyncio.run(self.client.optimize_context(model))

            if result.succeeded:
                console.print(
                    f"[green]Optimal context for {model}: {result.optimal_context:,} tokens[/green]"
                )
                console.print(
                    f"[dim]Reduction from declared: {result.declared_limit:,} → {result.optimal_context:,}[/dim]"
                )
            else:
                console.print(f"[red]Optimization failed: {result.error}[/red]")
        else:
            console.print("[red]Please specify a model ID or use --all[/red]")


def main():
    """Main entry point for the CLI."""
    fire.Fire(LMStrixCLI)


if __name__ == "__main__":
    main()
