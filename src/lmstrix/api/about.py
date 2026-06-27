# this_file: src/lmstrix/api/about.py

from rich.console import Console
from rich.table import Table

from lmstrix.core.describer import KEYWORD_VOCAB
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.utils import setup_logging

console = Console()


def about_command(verbose: bool = False) -> None:
    setup_logging(verbose=verbose)

    registry = load_model_registry(verbose=verbose)
    models = registry.list_models()

    total_models = len(models)
    tested_models = [m for m in models if m.context_test_status.value == "completed"]
    untested_models = [m for m in models if m.context_test_status.value == "untested"]
    failed_models = [m for m in models if m.context_test_status.value == "failed"]
    vision_models = [m for m in models if m.has_vision]
    tool_models = [m for m in models if m.has_tools]
    reasoning_models = [m for m in models if getattr(m, "has_reasoning", False)]

    all_keywords = set()
    keyword_counts: dict[str, int] = {}
    for model in models:
        if model.keywords:
            for kw in model.keywords:
                all_keywords.add(kw)
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    total_size_gb = sum((m.size for m in models if m.size), 0) / (1024**3)
    avg_context = sum((m.context_limit for m in models), 0) / total_models if total_models else 0
    avg_tested_context = (
        sum((m.tested_max_context for m in tested_models if m.tested_max_context), 0)
        / len(tested_models)
        if tested_models
        else 0
    )

    console.print("\n[bold cyan]LMStrix - LM Studio Model Testing Toolkit[/bold cyan]")
    console.print("")

    info_table = Table(show_header=False, box=None, expand=False)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    info_table.add_row("Models in registry", f"{total_models:,}")
    info_table.add_row("Tested models", f"{len(tested_models):,}")
    info_table.add_row("Untested models", f"{len(untested_models):,}")
    info_table.add_row("Failed models", f"{len(failed_models):,}")
    info_table.add_row("Vision-capable models", f"{len(vision_models):,}")
    info_table.add_row("Tool-calling models", f"{len(tool_models):,}")
    info_table.add_row("Reasoning-capable models", f"{len(reasoning_models):,}")
    info_table.add_row("Total size", f"{total_size_gb:.2f} GB")
    info_table.add_row("Avg declared context", f"{avg_context:,.0f} tokens")
    if tested_models:
        info_table.add_row("Avg tested context", f"{avg_tested_context:,.0f} tokens")
    console.print(info_table)
    console.print("")

    if all_keywords:
        console.print(
            f"[bold cyan]Keywords in registry[/bold cyan] ({len(all_keywords)} unique, {sum(keyword_counts.values())} total):"
        )
        console.print("")

        keyword_table = Table(show_header=True, box=None, expand=False)
        keyword_table.add_column("Category", style="cyan")
        keyword_table.add_column("Keywords", style="white")
        keyword_table.add_column("Count", justify="right", style="yellow")

        for category, keywords in KEYWORD_VOCAB.items():
            category_keywords_in_registry = [kw for kw in keywords if kw in all_keywords]
            if category_keywords_in_registry:
                sorted_kws = sorted(
                    category_keywords_in_registry,
                    key=lambda kw: (-keyword_counts[kw], kw),
                )
                keyword_table.add_row(
                    category,
                    ", ".join(f"`{kw}`" for kw in sorted_kws),
                    str(len(category_keywords_in_registry)),
                )

        console.print(keyword_table)
        console.print("")
    else:
        console.print("[yellow]No keywords found in registry.[/yellow]")
        console.print("Run 'lmstrix desc --all' to add keyword tags to models.")
        console.print("")

    if all_keywords:
        arch_keywords = {"arch-gguf", "arch-mlx", "arch-moe", "arch-dense"}
        arch_counts = {kw: keyword_counts.get(kw, 0) for kw in arch_keywords}
        console.print("[bold cyan]Architecture distribution:[/bold cyan]")
        for arch_kw, count in sorted(arch_counts.items(), key=lambda x: (-x[1], x[0])):
            if count > 0:
                console.print(f"  {arch_kw}: [yellow]{count}[/yellow] models")
        console.print("")
