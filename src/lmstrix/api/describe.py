# this_file: src/lmstrix/api/describe.py

from rich.console import Console

from lmstrix.core.describer import describe_models as run_describe_models
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.utils import setup_logging

console = Console()


def describe_models_command(
    model_id: str | None = None,
    desc_all: bool = False,
    describer_model_id: str | None = None,
    reset: bool = False,
    verbose: bool = False,
) -> None:
    setup_logging(verbose=verbose)
    registry = load_model_registry(verbose=verbose)
    if not registry.list_models():
        console.print("[red]No registry found. Run 'scan' first.[/red]")
        return

    if not model_id and not desc_all:
        console.print("[yellow]Specify a model ID or --all to describe models.[/yellow]")
        return

    method = describer_model_id or "droid exec"
    console.print(f"[bold]Using [cyan]{method}[/cyan] for descriptions.[/bold]")

    count = run_describe_models(
        registry=registry,
        describer_model_id=describer_model_id,
        model_id=model_id,
        reset=reset,
        verbose=verbose,
    )
    console.print(f"\n[green]Described {count} model(s).[/green]")
