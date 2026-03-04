#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["orjson", "rich", "fire"]
# ///
# this_file: benchread.py

"""
Reads bench.jsonl and writes benchtimes.txt with lines:
<duration_seconds> <model_id>
sorted by duration ascending.

The parser is defensive and will try multiple common keys for duration
and model identifiers so it can operate across slightly different logs.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import orjson as json
except Exception:  # pragma: no cover - tiny fallback
    import json  # type: ignore[misc]

import fire
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from collections.abc import Iterable

console = Console()


DURATION_KEYS = (
    "duration_seconds",
    "duration",
    "elapsed",
    "time_sec",
    "runtime_s",
    "seconds",
    "time",
    "latency_s",
)

MODEL_KEYS = (
    "model_id",
    "model",
    "id",
    "name",
    "modelName",
)


def coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if s.endswith("ms"):
            return float(s[:-2].strip()) / 1000.0
        if s.endswith("s"):
            return float(s[:-1].strip())
        return float(s)
    except Exception:
        return None


def extract_kv(obj: dict[str, Any]) -> tuple[float | None, str | None]:
    dur = None
    for k in DURATION_KEYS:
        if k in obj:
            dur = coerce_float(obj.get(k))
            if dur is not None:
                break

    mid = None
    for k in MODEL_KEYS:
        if k in obj and obj.get(k):
            mid = str(obj.get(k)).strip()
            if mid:
                break
    return dur, mid


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("rb") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except Exception as e:  # pragma: no cover
                console.print(f"[yellow]Skipping invalid JSON on line {i}: {e}")


def main(bench: str = ".", out: str | None = None) -> int:
    """Process benchmark data from JSONL file and generate timing report.

    Args:
        bench: Benchmark directory containing bench.jsonl (creates if doesn't exist)
        out: Output directory for benchtimes.txt (defaults to bench directory if not provided)
    """
    bench_dir = Path(bench)
    bench_dir.mkdir(exist_ok=True)

    if out is None:
        out_dir = bench_dir
    else:
        out_dir = Path(out)
        out_dir.mkdir(exist_ok=True)

    bench_path = bench_dir / "bench.jsonl"
    out_path = out_dir / "benchtimes.txt"

    if not bench_path.exists():
        console.print(f"[red]bench.jsonl not found at {bench_path}")
        return 2

    rows: list[tuple[float, str]] = []
    missing: int = 0
    for rec in read_jsonl(bench_path):
        # Only process "end" events to avoid duplicates
        if rec.get("event") != "end":
            continue
        dur, mid = extract_kv(rec)
        if dur is None or not mid:
            missing += 1
            continue
        rows.append((dur, mid))

    rows.sort(key=lambda x: x[0])
    out_path.write_text("\n".join(f"{d:.6f} {m}" for d, m in rows) + ("\n" if rows else ""))

    table = Table(title="benchtimes summary", show_lines=False)
    table.add_column("rank", justify="right")
    table.add_column("seconds", justify="right")
    table.add_column("model")
    for i, (d, m) in enumerate(rows, 1):
        table.add_row(str(i), f"{d:.3f}", m)

    console.print(table)
    console.print(
        f"[green]Wrote {len(rows)} rows to {out_path}[/green]"
        + (f"; skipped {missing} incomplete lines" if missing else "")
    )
    return 0


if __name__ == "__main__":
    fire.Fire(main)
