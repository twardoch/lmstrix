# this_file: src/lmstrix/cli/main.py
"""Command-line interface for LMStrix."""

import asyncio

import fire
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from lmstrix import LMStrix
from lmstrix.core import ContextTester, ModelRegistry
from lmstrix.core.scanner import ModelScanner

console = Console()


class LMStrixCLI:
    """LMStrix command-line interface."""

    def __init__(self, endpoint: str = "http://localhost:1234/v1", verbose: bool = False):
        """Initialize the CLI.

        Args:
            endpoint: LM Studio API endpoint.
            verbose: Enable verbose output.
        """
        self.endpoint = endpoint
        self.verbose = verbose
        self.client = LMStrix(endpoint=endpoint, verbose=verbose)

    def scan(self):
        """Scan for models in LM Studio and update registry."""
        scanner = ModelScanner()
        registry = ModelRegistry()

        with console.status("Scanning for models..."):
            registry = scanner.update_registry(registry)

        models = registry.list_models()
        console.print(f"[green]Found {len(models)} models[/green]")

        # Show newly added models
        new_models = [m for m in models if m.context_test_status.value == "untested"]
        if new_models:
            console.print(f"[yellow]{len(new_models)} new models require context testing[/yellow]")

    def list(self):
        """List all models with their test status."""
        registry = ModelRegistry()
        models = registry.list_models()

        if not models:
            console.print(
                "[yellow]No models found. Run 'lmstrix scan' to scan for models.[/yellow]"
            )
            return

        table = Table(title="Available Models")
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Size", style="magenta")
        table.add_column("Declared", style="yellow")
        table.add_column("Tested", style="green")
        table.add_column("Status", style="blue")
        table.add_column("Features", style="dim")

        for model in models:
            # Format tested context
            if model.tested_max_context:
                tested = f"{model.tested_max_context:,}"
            else:
                tested = "-"

            # Format status with color
            status = model.context_test_status.value
            if status == "completed":
                status_str = "[green]✓ Tested[/green]"
            elif status == "testing":
                status_str = "[yellow]⟳ Testing[/yellow]"
            elif status == "failed":
                status_str = "[red]✗ Failed[/red]"
            else:
                status_str = "[dim]- Untested[/dim]"

            # Features
            features = []
            if model.supports_tools:
                features.append("Tools")
            if model.supports_vision:
                features.append("Vision")
            features_str = ", ".join(features) if features else "-"

            table.add_row(
                model.id,
                f"{model.size / (1024**3):.1f}GB",
                f"{model.context_limit:,}",
                tested,
                status_str,
                features_str,
            )

        console.print(table)

        # Show summary
        tested_count = len([m for m in models if m.context_test_status.value == "completed"])
        console.print(f"\n[dim]{tested_count}/{len(models)} models tested[/dim]")

    def test(self, model_id: str = None, all: bool = False):
        """Test context limits for models.

        Args:
            model_id: Specific model to test.
            all: Test all untested models.
        """
        registry = ModelRegistry()

        if all:
            models_to_test = [
                m
                for m in registry.list_models()
                if m.context_test_status.value in ["untested", "failed"]
            ]
            if not models_to_test:
                console.print("[green]All models have been tested![/green]")
                return
            console.print(f"[yellow]Testing {len(models_to_test)} models...[/yellow]")
        elif model_id:
            model = registry.get_model(model_id)
            if not model:
                console.print(f"[red]Model '{model_id}' not found[/red]")
                return
            models_to_test = [model]
        else:
            console.print("[red]Please specify a model ID or use --all[/red]")
            return

        # Run tests
        tester = ContextTester(self.client.client)

        for i, model in enumerate(models_to_test, 1):
            console.print(f"\n[bold]Testing {model.id} ({i}/{len(models_to_test)})[/bold]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Testing context limits for {model.id}...", total=None)

                # Run the test
                updated_model = asyncio.run(tester.test_model(model))

                # Update registry
                registry.update_model(model.id, updated_model)

                progress.update(task, completed=True)

            # Show results
            if updated_model.context_test_status.value == "completed":
                console.print(
                    f"[green]✓ Test completed[/green]\n"
                    f"  Declared: {updated_model.context_limit:,}\n"
                    f"  Loadable: {updated_model.loadable_max_context:,}\n"
                    f"  Working: {updated_model.tested_max_context:,}"
                )

                if updated_model.tested_max_context < updated_model.context_limit:
                    reduction = (
                        (updated_model.context_limit - updated_model.tested_max_context)
                        / updated_model.context_limit
                        * 100
                    )
                    console.print(
                        f"  [yellow]⚠ Actual limit is {reduction:.0f}% lower than declared[/yellow]"
                    )
            else:
                console.print(f"[red]✗ Test failed: {updated_model.error_msg}[/red]")

    def status(self):
        """Show testing progress and summary."""
        registry = ModelRegistry()
        models = registry.list_models()

        if not models:
            console.print("[yellow]No models found. Run 'lmstrix scan' first.[/yellow]")
            return

        # Count by status
        status_counts = {}
        for model in models:
            status = model.context_test_status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Show summary
        console.print("[bold]Context Testing Status[/bold]\n")

        total = len(models)
        for status, count in sorted(status_counts.items()):
            percentage = count / total * 100

            if status == "completed":
                console.print(f"[green]✓ Tested: {count} ({percentage:.0f}%)[/green]")
            elif status == "testing":
                console.print(f"[yellow]⟳ Testing: {count} ({percentage:.0f}%)[/yellow]")
            elif status == "failed":
                console.print(f"[red]✗ Failed: {count} ({percentage:.0f}%)[/red]")
            else:
                console.print(f"[dim]- Untested: {count} ({percentage:.0f}%)[/dim]")

        # Show models with significant discrepancies
        tested_models = [m for m in models if m.tested_max_context]
        if tested_models:
            console.print("\n[bold]Models with Context Limit Issues:[/bold]")

            issues = []
            for model in tested_models:
                if model.tested_max_context < model.context_limit * 0.8:  # >20% reduction
                    reduction = (
                        (model.context_limit - model.tested_max_context) / model.context_limit * 100
                    )
                    issues.append((model, reduction))

            if issues:
                issues.sort(key=lambda x: x[1], reverse=True)
                for model, reduction in issues[:10]:  # Top 10
                    console.print(
                        f"  {model.id}: "
                        f"{model.context_limit:,} → {model.tested_max_context:,} "
                        f"[red](-{reduction:.0f}%)[/red]"
                    )
            else:
                console.print("[green]All tested models work at declared limits![/green]")

    def models(self, action: str = "list", model_id: str = None):
        """Legacy models command - redirects to new commands."""
        if action == "list":
            self.list()
        elif action == "scan":
            self.scan()
        else:
            console.print(f"[yellow]Unknown action: {action}[/yellow]")

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
        """Legacy optimize command - redirects to test."""
        console.print(
            "[yellow]Note: 'optimize' command is deprecated. Use 'test' instead.[/yellow]"
        )
        self.test(model_id=model, all=all)


def main():
    """Main entry point for the CLI."""
    fire.Fire(LMStrixCLI)


if __name__ == "__main__":
    main()
