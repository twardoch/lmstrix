#!/usr/bin/env -S uv run -s
# /// script
# dependencies = [
#   "fire>=0.5",
#   "rich>=13.9.4",
#   "lmstudio>=1.4.1",
#   "httpx>=0.24",
#   "loguru>=0.7",
#   "pydantic>=2.0",
#   "tiktoken>=0.5",
#   "toml>=0.10",
#   "tenacity>=8.5.0"
# ]
# ///
# this_file: _keep_this/model_load_tester.py

"""
Comprehensive LM Studio model loading tester.

This tool examines all possible ways to load and run inference on LM Studio models
to find the optimal approach that works consistently across different identifier types.
"""

import sys
import traceback
from pathlib import Path

import fire
import lmstudio
from loguru import logger
from rich.console import Console
from rich.table import Table

# Add the src directory to Python path to import lmstrix
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import builtins
import contextlib

from lmstrix.loaders.model_loader import load_model_registry

console = Console()


class ModelLoadTester:
    """Test different ways to load and run inference on LM Studio models."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the tester."""
        self.verbose = verbose
        if verbose:
            logger.enable("lmstrix")
        else:
            logger.disable("lmstrix")

    def list_all_model_info(self) -> None:
        """List all available model information from different sources."""
        console.print("[bold cyan]📋 COMPREHENSIVE MODEL INFORMATION[/bold cyan]\n")

        # 1. LM Studio downloaded models
        console.print("[bold]1. LM Studio Downloaded Models:[/bold]")
        try:
            models = lmstudio.list_downloaded_models()
            if not models:
                console.print("[yellow]No downloaded models found[/yellow]")
            else:
                for i, model in enumerate(models):
                    console.print(f"\n[cyan]Model {i + 1}:[/cyan]")
                    info = model.info

                    # Display all available attributes
                    console.print(f"  Raw model object: {type(model)}")
                    console.print(f"  Info object: {type(info)}")
                    console.print(f"  Available attributes: {dir(info)}")

                    # Try to get key identifiers
                    attrs_to_check = [
                        "model_key",
                        "modelKey",
                        "id",
                        "name",
                        "display_name",
                        "displayName",
                        "path",
                        "file_path",
                        "filePath",
                        "architecture",
                        "type",
                        "max_context_length",
                        "maxContextLength",
                        "context_length",
                        "size_bytes",
                        "sizeBytes",
                        "vision",
                        "trainedForToolUse",
                    ]

                    for attr in attrs_to_check:
                        try:
                            value = getattr(info, attr, None)
                            if value is not None:
                                console.print(f"  {attr}: {value}")
                        except Exception as e:
                            console.print(f"  {attr}: [red]Error: {e}[/red]")

        except Exception as e:
            console.print(f"[red]Error listing LM Studio models: {e}[/red]")
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

        # 2. LMStrix registry models
        console.print("\n[bold]2. LMStrix Registry Models:[/bold]")
        try:
            registry = load_model_registry(verbose=self.verbose)
            models = registry.list_models()

            if not models:
                console.print("[yellow]No models in registry[/yellow]")
            else:
                for i, model in enumerate(models[:5]):  # Show first 5
                    console.print(f"\n[cyan]Registry Model {i + 1}:[/cyan]")
                    console.print(f"  ID: {model.id}")
                    console.print(f"  Short ID: {model.get_short_id()}")
                    console.print(f"  Path: {model.path}")
                    console.print(f"  Context Limit: {model.context_limit}")
                    console.print(f"  Tested Max Context: {model.tested_max_context}")

                if len(models) > 5:
                    console.print(f"\n[dim]... and {len(models) - 5} more models[/dim]")

        except Exception as e:
            console.print(f"[red]Error loading LMStrix registry: {e}[/red]")
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

    def test_model_loading_methods(self, test_model_index: int = 0) -> None:
        """Test different methods to load a specific model."""
        console.print("[bold cyan]🧪 TESTING MODEL LOADING METHODS[/bold cyan]\n")

        try:
            models = lmstudio.list_downloaded_models()
            if not models:
                console.print("[red]No downloaded models found[/red]")
                return

            if test_model_index >= len(models):
                console.print(
                    f"[red]Model index {test_model_index} out of range. Available: 0-{len(models) - 1}[/red]",
                )
                return

            test_model = models[test_model_index]
            info = test_model.info

            console.print(
                f"[green]Testing with model {test_model_index}: {getattr(info, 'display_name', 'Unknown')}[/green]\n",
            )

            # Collect all possible identifiers for this model
            identifiers = {}

            # Try to extract different identifier types
            id_attrs = ["model_key", "modelKey", "id", "path", "display_name", "displayName"]
            for attr in id_attrs:
                try:
                    value = getattr(info, attr, None)
                    if value:
                        identifiers[attr] = str(value)
                except:
                    pass

            console.print("[cyan]Available identifiers:[/cyan]")
            for key, value in identifiers.items():
                console.print(f"  {key}: {value}")
            console.print()

            # Test different loading methods
            methods_to_test = [
                ("lmstudio.llm(path)", lambda: lmstudio.llm(identifiers.get("path", ""))),
                (
                    "lmstudio.llm(model_key)",
                    lambda: lmstudio.llm(
                        identifiers.get("model_key", identifiers.get("modelKey", "")),
                    ),
                ),
                ("lmstudio.llm(id)", lambda: lmstudio.llm(identifiers.get("id", ""))),
                (
                    "lmstudio.llm(display_name)",
                    lambda: lmstudio.llm(
                        identifiers.get("display_name", identifiers.get("displayName", "")),
                    ),
                ),
            ]

            successful_methods = []

            for method_name, method_func in methods_to_test:
                console.print(f"[yellow]Testing {method_name}...[/yellow]")
                try:
                    llm = method_func()
                    if llm:
                        console.print(f"[green]✓ {method_name} succeeded[/green]")
                        successful_methods.append((method_name, llm))

                        # Try basic inference
                        try:
                            result = llm.completion("Hello, respond with just 'Hi!'")
                            console.print(
                                f"  Inference test: [green]✓ '{result.content.strip()}'[/green]",
                            )
                        except Exception as e:
                            console.print(f"  Inference test: [red]✗ {e}[/red]")

                        # Unload the model
                        with contextlib.suppress(builtins.BaseException):
                            llm.unload()
                    else:
                        console.print(f"[red]✗ {method_name} returned None[/red]")

                except Exception as e:
                    console.print(f"[red]✗ {method_name} failed: {e}[/red]")

                console.print()

            # Summary
            console.print("[bold cyan]Summary:[/bold cyan]")
            if successful_methods:
                console.print(f"[green]✓ {len(successful_methods)} methods succeeded:[/green]")
                for method_name, _ in successful_methods:
                    console.print(f"  - {method_name}")
            else:
                console.print("[red]✗ No methods succeeded[/red]")

        except Exception as e:
            console.print(f"[red]Error in model loading test: {e}[/red]")
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

    def test_registry_to_lmstudio_mapping(self) -> None:
        """Test mapping between LMStrix registry models and LM Studio models."""
        console.print("[bold cyan]🔗 TESTING REGISTRY TO LM STUDIO MAPPING[/bold cyan]\n")

        try:
            # Get both sets of models
            lms_models = lmstudio.list_downloaded_models()
            registry = load_model_registry(verbose=self.verbose)
            reg_models = registry.list_models()

            console.print(f"LM Studio models: {len(lms_models)}")
            console.print(f"Registry models: {len(reg_models)}")
            console.print()

            # Create mapping table
            table = Table(title="Registry to LM Studio Mapping")
            table.add_column("Registry ID", style="cyan")
            table.add_column("Registry Short ID", style="blue")
            table.add_column("Registry Path", style="green")
            table.add_column("LM Studio Match", style="yellow")
            table.add_column("Load Status", style="magenta")

            for reg_model in reg_models[:10]:  # Test first 10
                # Try to find matching LM Studio model
                lms_match = None
                for lms_model in lms_models:
                    info = lms_model.info
                    # Check if paths match or IDs match
                    if (
                        str(reg_model.path) in str(getattr(info, "path", ""))
                        or reg_model.id == getattr(info, "model_key", getattr(info, "modelKey", ""))
                        or reg_model.get_short_id()
                        == getattr(info, "display_name", getattr(info, "displayName", ""))
                    ):
                        lms_match = info
                        break

                # Test loading
                load_status = "Not tested"
                if lms_match:
                    try:
                        # Try loading with the matched identifier
                        identifier = getattr(
                            lms_match,
                            "model_key",
                            getattr(lms_match, "modelKey", ""),
                        )
                        if identifier:
                            llm = lmstudio.llm(identifier, config={"contextLength": 4096})
                            if llm:
                                load_status = "[green]✓ Success[/green]"
                                llm.unload()
                            else:
                                load_status = "[red]✗ None returned[/red]"
                        else:
                            load_status = "[yellow]? No identifier[/yellow]"
                    except Exception as e:
                        load_status = f"[red]✗ {str(e)[:30]}[/red]"
                else:
                    load_status = "[red]✗ No match[/red]"

                table.add_row(
                    reg_model.id[:50] + ("..." if len(reg_model.id) > 50 else ""),
                    reg_model.get_short_id(),
                    str(reg_model.path)[:50] + ("..." if len(str(reg_model.path)) > 50 else ""),
                    (
                        getattr(lms_match, "model_key", getattr(lms_match, "modelKey", "No match"))
                        if lms_match
                        else "No match"
                    ),
                    load_status,
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Error in mapping test: {e}[/red]")
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

    def find_optimal_loading_strategy(self) -> None:
        """Find the optimal strategy for loading models that works across different identifier types."""
        console.print("[bold cyan]🎯 FINDING OPTIMAL LOADING STRATEGY[/bold cyan]\n")

        try:
            lms_models = lmstudio.list_downloaded_models()
            registry = load_model_registry(verbose=self.verbose)

            strategies = []

            # Strategy 1: Use model_key/modelKey directly
            def strategy_model_key(reg_model):
                for lms_model in lms_models:
                    info = lms_model.info
                    key = getattr(info, "model_key", getattr(info, "modelKey", None))
                    if key and (key == reg_model.id or key in str(reg_model.path)):
                        return lmstudio.llm(
                            key,
                            config={
                                "contextLength": reg_model.tested_max_context
                                or reg_model.context_limit,
                            },
                        )
                return None

            # Strategy 2: Use path matching
            def strategy_path_match(reg_model):
                for lms_model in lms_models:
                    info = lms_model.info
                    if str(reg_model.path) in str(getattr(info, "path", "")):
                        key = getattr(info, "model_key", getattr(info, "modelKey", None))
                        if key:
                            return lmstudio.llm(
                                key,
                                config={
                                    "contextLength": reg_model.tested_max_context
                                    or reg_model.context_limit,
                                },
                            )
                return None

            # Strategy 3: Use short_id matching with display_name
            def strategy_short_id_match(reg_model):
                short_id = reg_model.get_short_id()
                for lms_model in lms_models:
                    info = lms_model.info
                    display_name = getattr(info, "display_name", getattr(info, "displayName", ""))
                    if short_id == display_name:
                        key = getattr(info, "model_key", getattr(info, "modelKey", None))
                        if key:
                            return lmstudio.llm(
                                key,
                                config={
                                    "contextLength": reg_model.tested_max_context
                                    or reg_model.context_limit,
                                },
                            )
                return None

            strategies = [
                ("Model Key Direct", strategy_model_key),
                ("Path Matching", strategy_path_match),
                ("Short ID Matching", strategy_short_id_match),
            ]

            # Test strategies on a sample of models
            reg_models = registry.list_models()[:5]  # Test first 5

            results = {}
            for strategy_name, strategy_func in strategies:
                results[strategy_name] = {"success": 0, "total": 0, "errors": []}

                console.print(f"[yellow]Testing strategy: {strategy_name}[/yellow]")

                for reg_model in reg_models:
                    results[strategy_name]["total"] += 1
                    try:
                        llm = strategy_func(reg_model)
                        if llm:
                            # Test basic inference
                            response = llm.completion("Hello")
                            if response and response.content:
                                results[strategy_name]["success"] += 1
                                console.print(f"  ✓ {reg_model.get_short_id()}")
                            else:
                                results[strategy_name]["errors"].append(
                                    f"{reg_model.get_short_id()}: No response",
                                )
                                console.print(f"  ✗ {reg_model.get_short_id()}: No response")
                            llm.unload()
                        else:
                            results[strategy_name]["errors"].append(
                                f"{reg_model.get_short_id()}: Load failed",
                            )
                            console.print(f"  ✗ {reg_model.get_short_id()}: Load failed")
                    except Exception as e:
                        results[strategy_name]["errors"].append(f"{reg_model.get_short_id()}: {e}")
                        console.print(f"  ✗ {reg_model.get_short_id()}: {e}")

                console.print()

            # Show results
            console.print("[bold cyan]Strategy Results:[/bold cyan]")
            for strategy_name, result in results.items():
                success_rate = (
                    (result["success"] / result["total"]) * 100 if result["total"] > 0 else 0
                )
                console.print(
                    f"[cyan]{strategy_name}:[/cyan] {result['success']}/{result['total']} ({success_rate:.1f}%)",
                )

                if result["errors"] and self.verbose:
                    console.print("  Errors:")
                    for error in result["errors"][:3]:  # Show first 3 errors
                        console.print(f"    - {error}")

        except Exception as e:
            console.print(f"[red]Error in strategy testing: {e}[/red]")
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")

    def run_comprehensive_test(self) -> None:
        """Run all tests to get a complete picture."""
        console.print("[bold green]🚀 COMPREHENSIVE LM STUDIO MODEL LOADING TEST[/bold green]\n")

        self.list_all_model_info()
        console.print("\n" + "=" * 80 + "\n")

        self.test_model_loading_methods()
        console.print("\n" + "=" * 80 + "\n")

        self.test_registry_to_lmstudio_mapping()
        console.print("\n" + "=" * 80 + "\n")

        self.find_optimal_loading_strategy()


def main() -> None:
    """Main entry point."""
    fire.Fire(ModelLoadTester)


if __name__ == "__main__":
    main()
