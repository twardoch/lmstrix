#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///
# this_file: lmsmodsearch.py
"""Read lmstrix.json, use droid exec to describe each model, output lmstrix-desc.json."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MAX_WORKERS = 4
TIMEOUT_SECS = 120
INPUT_FILE = "lmstrix.json"
OUTPUT_FILE = "lmstrix-desc.json"


def describe_model(model_key: str, model_data: dict) -> tuple[str, str]:
    """Run droid exec to search for and describe a model."""
    model_id = model_data.get("id", "")
    model_path = model_data.get("path", model_key)
    size_gb = model_data.get("size_bytes", 0) / (1024**3)
    has_vision = model_data.get("has_vision", False)
    has_tools = model_data.get("has_tools", False)
    ctx_in = model_data.get("ctx_in", 0)

    prompt = (
        f"Search for information about the AI/LLM model: {model_path} "
        f"(id: {model_id}). "
        f"Known facts: {size_gb:.1f}GB, context window {ctx_in} tokens, "
        f"vision={'yes' if has_vision else 'no'}, tool use={'yes' if has_tools else 'no'}. "
        f"Describe: what this model is, its architecture family, parameter count, "
        f"training focus, strengths, and typical use cases. "
        f"Output ONLY a concise 2-4 sentence description, nothing else."
    )

    try:
        result = subprocess.run(
            ["droid", "exec", prompt],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECS,
        )
        desc = result.stdout.strip()
        if not desc and result.stderr.strip():
            return model_key, f"[error] {result.stderr.strip()[:300]}"
        return model_key, desc or "[no description returned]"
    except subprocess.TimeoutExpired:
        return model_key, "[error] droid timed out"
    except FileNotFoundError:
        print("Error: 'droid' not found on PATH. Install it first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        return model_key, f"[error] {e}"


def load_existing(output_path: Path) -> dict:
    """Load existing output JSON if present."""
    if output_path.exists():
        with open(output_path) as f:
            return json.load(f)
    return {}


def has_description(model_entry: dict) -> bool:
    """Check if a model already has a valid (non-error) description."""
    desc = model_entry.get("description", "")
    return bool(desc) and not desc.startswith("[")


def save_output(data: dict, results: dict, output_path: Path) -> None:
    """Write current results to output JSON."""
    extended = dict(data)
    extended_llms = {}
    for key, val in data.get("llms", {}).items():
        entry = dict(val)
        if key in results:
            entry["description"] = results[key]
        extended_llms[key] = entry
    extended["llms"] = extended_llms
    with open(output_path, "w") as f:
        json.dump(extended, f, indent=2, ensure_ascii=False)


def main() -> None:
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    llms = data.get("llms", {})
    total = len(llms)

    # Load existing output and collect already-described models
    existing = load_existing(output_path)
    existing_llms = existing.get("llms", {})
    results: dict[str, str] = {}
    for key in llms:
        if key in existing_llms and has_description(existing_llms[key]):
            results[key] = existing_llms[key]["description"]

    skipped = len(results)
    todo = {k: v for k, v in llms.items() if k not in results}
    print(f"Found {total} models total, {skipped} already described, {len(todo)} to do.\n")

    if not todo:
        print("Nothing to do — all models already described.")
        return

    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(describe_model, key, val): key for key, val in todo.items()}

        for future in as_completed(futures):
            model_key, description = future.result()
            results[model_key] = description
            completed += 1

            model_id = llms[model_key].get("id", model_key)
            short = llms[model_key].get("short_id", model_key[:40])
            status = "ok" if not description.startswith("[error]") else "FAIL"

            print(f"\n[{completed}/{len(todo)}] {status}  {short}")
            print(f"  id: {model_id}")
            desc_preview = description[:300] + ("..." if len(description) > 300 else "")
            print(f"  {desc_preview}")

            # Update output file after each completion
            save_output(data, results, output_path)

    ok_count = sum(1 for d in results.values() if not d.startswith("[error]"))
    fail_count = total - ok_count
    print(
        f"\nDone. {ok_count} described ({skipped} prior + {ok_count - skipped} new), {fail_count} failed."
    )
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
