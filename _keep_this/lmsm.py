#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["lmstudio", "pydantic", "rich", "fire"]
# ///
# this_file: lmsm.py

import json
from pathlib import Path
from typing import Any

import fire
import lmstudio as lms
from pydantic import BaseModel, Field
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Table


class LmsMInfo(BaseModel):
    id: str
    path: Path
    size_bytes: int
    ctx_in: int
    ctx_out: int
    has_tools: bool
    has_vision: bool
    failed: bool = False
    error_msg: str = ""

    def to_table_row(self, base_path: Path) -> list[str]:
        try:
            # Make path relative to base_path/models
            models_path = base_path / "models"
            rel_path = self.path.relative_to(models_path)
        except ValueError:
            rel_path = self.path

        return [
            str(rel_path),
            f"{self.size_bytes / 1024 / 1024 / 1024:.1f}GB",
            f"{self.ctx_in / 1024:.0f}k",
            f"{self.ctx_out / 1024:.0f}k",
            "✅" if self.has_tools else "❌",
            "✅" if self.has_vision else "❌",
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "ctx_in": self.ctx_in,
            "ctx_out": self.ctx_out,
            "has_tools": self.has_tools,
            "has_vision": self.has_vision,
            "failed": self.failed,
            "error_msg": self.error_msg,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LmsMInfo":
        # Ensure path is a Path object
        if isinstance(data.get("path"), str):
            data["path"] = Path(data["path"])
        return cls(**data)


class LmsM(BaseModel):
    path: Path
    llms: dict[str, LmsMInfo] = Field(default_factory=dict)

    @classmethod
    def load_or_create(cls, lms_path: Path) -> "LmsM":
        json_path = lms_path / "lmsm.json"
        if json_path.exists():
            data = json.loads(json_path.read_text())
            # Convert the llms dict to use LmsMInfo objects
            if "llms" in data:
                data["llms"] = {
                    k: LmsMInfo.from_dict(
                        {
                            "id": v["id"],
                            "path": v["path"],
                            "size_bytes": v["size_bytes"],
                            "ctx_in": v["ctx_in"],
                            "ctx_out": v["ctx_out"],
                            "has_tools": v["has_tools"],
                            "has_vision": v["has_vision"],
                            "failed": v.get(
                                "failed",
                                False,
                            ),  # Handle older JSON files without these fields
                            "error_msg": v.get("error_msg", ""),
                        },
                    )
                    for k, v in data["llms"].items()
                }
            if isinstance(data.get("path"), str):
                data["path"] = Path(data["path"])
            return cls(**data)
        return cls(path=lms_path)

    def save(self) -> None:
        # Sort models by ID
        sorted_llms = dict(sorted(self.llms.items()))
        self.llms = sorted_llms

        # Convert to serializable dict
        data = {
            "path": str(self.path),
            "llms": {k: v.to_dict() for k, v in self.llms.items()},
        }

        # Save to JSON with indentation
        json_path = self.path / "lmsm.json"
        json_str = json.dumps(data, indent=2)
        json_path.write_text(json_str)

    def update_model(self, model_key: str, model_info: LmsMInfo) -> None:
        """Update a model in the cache and save"""
        new_llms = dict(self.llms)
        new_llms[model_key] = model_info
        self.llms = new_llms  # This triggers Pydantic validation
        self.save()

    def remove_model(self, model_key: str) -> None:
        """Remove a model from the cache and save"""
        if model_key in self.llms:
            new_llms = {k: v for k, v in self.llms.items() if k != model_key}
            self.llms = new_llms  # This triggers Pydantic validation
            self.save()

    def clear_models(self) -> None:
        """Clear all models from the cache and save"""
        self.llms = {}  # This triggers Pydantic validation
        self.save()

    def create_table(self) -> Table:
        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Path", style="blue")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Ctx In", justify="right", style="yellow")
        table.add_column("Ctx Out", justify="right", style="yellow")
        table.add_column("Tools", justify="center")
        table.add_column("Vision", justify="center")
        table.add_column("Status", justify="center")  # Add status column
        return table

    def create_error_table(self, title: str) -> Table:
        table = Table(
            title=title,
            box=box.ROUNDED,
            show_header=True,
            header_style="bold red",
        )
        table.add_column("Model ID", style="red")
        table.add_column("Error", style="yellow")
        return table

    def update_from_lmstudio(
        self,
        all_rescan: bool = False,
        failed_rescan: bool = False,
    ) -> None:
        console = Console()

        # Get current models from LMStudio
        result = lms.list_downloaded_models("llm")
        current_models = {
            llm.model_key: llm
            for llm in result
            if all(ss not in llm.model_key for ss in ["bge", "embed"])
        }

        # Track failed models and processing state
        failed_models: list[tuple[str, str]] = []
        current_processing: str = ""

        def render_table() -> Table:
            table = self.create_table()

            # Add all cached/completed models
            for model_id, model_info in dict(self.llms).items():
                row = model_info.to_table_row(self.path)
                # Add status column
                status = "[red]Failed[/red]" if model_info.failed else "[green]OK[/green]"
                table.add_row(model_id, *row, status)

            # Add processing model if any
            if current_processing:
                table.add_row(
                    f"[yellow]{current_processing}[/yellow]",
                    "...",
                    "...",
                    "...",
                    "...",
                    "...",
                    "...",
                    "[yellow]Scanning...[/yellow]",
                )

            return table

        with Live(render_table(), console=console, refresh_per_second=4) as live:
            # Remove non-existent models first
            models_to_remove = set(dict(self.llms).keys()) - set(current_models.keys())
            if models_to_remove:
                for model_key in models_to_remove:
                    self.remove_model(model_key)
                    live.update(render_table())

            # Determine which models to process
            if all_rescan:
                models_to_update = set(current_models.keys())
                # Clear status for all models we're about to rescan
                console.print(
                    f"\n[yellow]Rescanning all {len(models_to_update)} models...[/yellow]\n",
                )
                self.clear_models()
                live.update(render_table())

            elif failed_rescan:
                # Get list of previously failed models from our saved state
                failed_model_keys = {
                    k for k, v in self.llms.items() if v.failed and k in current_models
                }
                models_to_update = failed_model_keys

                if failed_model_keys:
                    console.print(
                        f"\n[yellow]Rescanning {len(failed_model_keys)} previously failed models...[/yellow]\n",
                    )
                    # Remove failed models from cache so they're fully rescanned
                    for model_key in failed_model_keys:
                        self.remove_model(model_key)
                    live.update(render_table())
                else:
                    console.print(
                        "\n[green]No failed models found to rescan.[/green]\n",
                    )
            else:
                # Only process new models
                models_to_update = set(current_models.keys()) - set(self.llms.keys())
                if models_to_update:
                    console.print(
                        f"\n[yellow]Scanning {len(models_to_update)} new models...[/yellow]\n",
                    )

            for model_key in models_to_update:
                try:
                    # Show processing status
                    current_processing = model_key
                    live.update(render_table())

                    # Get model info
                    llm = lms.llm(model_key)
                    lli = llm.get_info()

                    # Create new model info
                    model_info = LmsMInfo(
                        id=model_key,
                        path=self.path / "models" / getattr(lli, "path", ""),
                        size_bytes=getattr(lli, "size_bytes", 0),
                        ctx_in=getattr(lli, "max_context_length", 0),
                        ctx_out=getattr(lli, "context_length", 0),
                        has_tools=getattr(lli, "trained_for_tool_use", False),
                        has_vision=getattr(lli, "vision", False),
                        failed=False,
                        error_msg="",
                    )

                    # Add to internal state
                    self.update_model(model_key, model_info)

                    # Clear processing status
                    current_processing = ""
                    live.update(render_table())

                except RuntimeError as e:
                    error_msg = str(e)
                    failed_models.append((model_key, error_msg))

                    # Update model info to mark as failed
                    model_info = LmsMInfo(
                        id=model_key,
                        path=self.path / "models" / model_key,  # Use model_key as fallback path
                        size_bytes=0,
                        ctx_in=0,
                        ctx_out=0,
                        has_tools=False,
                        has_vision=False,
                        failed=True,
                        error_msg=error_msg,
                    )
                    self.update_model(model_key, model_info)

                    # Clear processing status
                    current_processing = ""
                    live.update(render_table())

        # Show failed models if any
        if failed_models:
            console.print(
                "\n[bold red]Failed Models (Consider removing from LMStudio):[/bold red]",
            )
            error_table = self.create_error_table("Failed Models")
            for model_key, error in failed_models:
                error_table.add_row(model_key, error)
            console.print(error_table)


class LmsmCLI:
    """LMStudio Model Manager CLI"""

    def __init__(self) -> None:
        # Get LMStudio path
        self.lms_path = Path(
            Path(Path.home() / ".lmstudio-home-pointer").read_text().splitlines()[0].strip(),
        )
        self.lmsm = LmsM.load_or_create(self.lms_path)

    def list(self, all_rescan: bool = False, failed_rescan: bool = False) -> None:
        """List all models in LMStudio

        Args:
            all_rescan: Rescan all models, including previously scanned ones
            failed_rescan: Rescan only previously failed models
        """
        self.lmsm.update_from_lmstudio(
            all_rescan=all_rescan,
            failed_rescan=failed_rescan,
        )


if __name__ == "__main__":
    cli = LmsmCLI()
    fire.Fire(cli.list)
