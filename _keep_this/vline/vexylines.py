#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["lmstrix", "rich", "fire"]
# ///
"""Vexy Lines: A tool for benchmarking prompts against LM-Studio models."""

# this_file: vexylines.py

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import lmstrix
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import fire
from rich.console import Console

from lmstrix.api.client import LMStudioClient
from lmstrix.core.inference_manager import InferenceManager
from lmstrix.loaders.model_loader import load_model_registry


class VexyLines:
    """A tool for benchmarking prompts against LM-Studio models."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize VexyLines.

        Args:
            verbose: Enable verbose logging.
        """
        self.console = Console()
        self.verbose = verbose

        self.registry = load_model_registry(verbose=verbose)
        self.client = LMStudioClient(verbose=verbose)
        self.inference_manager = InferenceManager(
            client=self.client, registry=self.registry, verbose=verbose
        )

    def _write_bench_record(self, record: dict, bench_file: Path) -> None:
        """Write a record to the benchmark JSONL file.

        Args:
            record: Dictionary containing benchmark data.
            bench_file: Path to the benchmark JSONL file.
        """
        with bench_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()  # Ensure immediate write

    def run(
        self, prompt_path: str, dry_run: bool = False, bench: str = ".", out: str = "out"
    ) -> None:
        """Run the benchmarking tool.

        Args:
            prompt_path: Path to the text file containing the prompt.
            dry_run: If True, only test the 2 smallest models.
            bench: Benchmark directory (creates if doesn't exist).
            out: Output directory for model responses (creates if doesn't exist).
        """
        # Create directories if they don't exist
        bench_dir = Path(bench)
        bench_dir.mkdir(exist_ok=True)

        output_dir = Path(out)
        output_dir.mkdir(exist_ok=True)

        bench_file = bench_dir / "bench.jsonl"

        try:
            prompt = Path(prompt_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            self.console.print(f"Error: Prompt file not found at {prompt_path}", style="red")
            sys.exit(1)

        models = self.registry.list_models()

        # Sort models by size (assuming size is stored in bytes)
        models.sort(key=lambda m: m.size if hasattr(m, "size") else 0)

        if dry_run:
            models = models[:2]  # Only test 2 smallest models
            self.console.print(f"[Dry Run] Testing {len(models)} smallest models.", style="yellow")
        else:
            self.console.print(f"Found {len(models)} models to benchmark.")

        for model in models:
            # Check if output already exists
            output_path = output_dir / f"{model.id.replace('/', '_')}.txt"
            if output_path.exists():
                self.console.print(f"Skipping {model.id}: output already exists", style="dim")
                continue

            self.console.print(f"Benchmarking model: {model.id}", style="cyan")

            # Record before starting inference
            start_record = {
                "model_id": model.id,
                "model_size": getattr(model, "size", None),
                "event": "start",
                "timestamp": datetime.now().isoformat(),
                "unix_time": time.time(),
            }
            self._write_bench_record(start_record, bench_file)

            start_time = time.time()

            result = self.inference_manager.infer(
                model_id=model.id,
                prompt=prompt,
                temperature=0.8,
            )

            end_time = time.time()
            duration = end_time - start_time

            # Record after inference completes
            end_record = {
                "model_id": model.id,
                "model_size": getattr(model, "size", None),
                "event": "end",
                "timestamp": datetime.now().isoformat(),
                "unix_time": end_time,
                "duration_seconds": duration,
                "succeeded": result["succeeded"],
            }

            if result["succeeded"]:
                output_path.write_text(result["response"], encoding="utf-8")
                self.console.print(f"  Success! Output saved to {output_path}", style="green")
                end_record["output_path"] = str(output_path)
                end_record["response_length"] = len(result["response"])
            else:
                self.console.print(f"  Failed: {result['error']}", style="red")
                end_record["error"] = result.get("error", "Unknown error")

            self._write_bench_record(end_record, bench_file)


if __name__ == "__main__":
    vl = VexyLines()
    fire.Fire(vl.run)
