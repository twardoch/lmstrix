#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["httpx", "rich", "fire"]
# ///
# this_file: src/lmstrix/data/jinja2_templates/hy-mt1.5-test.py
"""End-to-end test tool for the HY-MT1.5 LM Studio chat template."""

from __future__ import annotations

import subprocess
from pathlib import Path

import fire
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

MODEL_ID = "hy-mt1.5-7b"
LMSTUDIO_URL = "http://localhost:1234/api/v1/chat"
LOCAL_TEMPLATE_DIR = Path(__file__).parent
LIVE_TEMPLATE_PATH = Path(
    "/Volumes/Falstaff4T/RomeoData2/lmstudio/models/mlx-community/HY-MT1.5-7B-8bit/chat_template.jinja"
)

EXAMPLES = {
    "multiline": """translate:
input: en
output: pl
vocab: typeface,krój pisma
vocab: font,font
context: Some information before
text: FontLab 8 is an integrated font editor for Mac and Windows that
  helps you create fonts from start to finish, from a simple design to
  a complex project, and brings a spark of magic into type design. Try
  FontLab 8 for free for 10 days, and start making fonts today!""",
    "singleline": "translate:;input:en;output:pl;vocab:typeface,krój pisma;vocab:font,font;context: Some information before;text: FontLab 8 is an integrated font editor for Mac and Windows that helps you create fonts from start to finish, from a simple design to a complex project, and brings a spark of magic into type design. Try FontLab 8 for free for 10 days, and start making fonts today!",
}


def deploy(template_file: str = "hy-mt1.5.jinja2") -> Path:
    src = LOCAL_TEMPLATE_DIR / template_file
    LIVE_TEMPLATE_PATH.write_text(src.read_text())
    console.print(f"[green]Copied {src} -> {LIVE_TEMPLATE_PATH}[/green]")
    return LIVE_TEMPLATE_PATH


def load_model(model_id: str = MODEL_ID) -> None:
    command = f"lms unload -a; lms load {model_id}"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.stdout:
        console.print(Panel(result.stdout.strip(), title="lms stdout", border_style="blue"))
    if result.stderr:
        console.print(Panel(result.stderr.strip(), title="lms stderr", border_style="yellow"))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _extract_translation(data: object) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        parts = [_extract_translation(item) for item in data]
        return "\n".join(part for part in parts if part).strip()
    if isinstance(data, dict):
        for key in ("output", "response", "text", "content"):
            if key in data:
                value = _extract_translation(data[key])
                if value:
                    return value
        if isinstance(data.get("choices"), list) and data["choices"]:
            value = _extract_translation(data["choices"][0])
            if value:
                return value
        if data.get("type") == "message" and "content" in data:
            value = _extract_translation(data["content"])
            if value:
                return value
        if "message" in data:
            value = _extract_translation(data["message"])
            if value:
                return value
    return ""


def infer(example: str = "multiline", timeout: float = 120.0) -> str:
    prompt = EXAMPLES[example]
    payload = {
        "model": MODEL_ID,
        "system_prompt": "",
        "input": prompt,
    }
    response = httpx.post(LMSTUDIO_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    translation = _extract_translation(data)

    console.print(Panel(prompt, title=f"Prompt: {example}", border_style="cyan"))
    console.print(Panel(translation or str(data), title="Translation", border_style="green"))
    return translation or str(data)


def run(template_file: str = "hy-mt1.5.jinja2", timeout: float = 120.0) -> None:
    deploy(template_file)
    load_model(MODEL_ID)

    table = Table(title=f"{MODEL_ID} translation results")
    table.add_column("Example", style="cyan")
    table.add_column("Translation", style="green")

    for name in EXAMPLES:
        translation = infer(example=name, timeout=timeout)
        table.add_row(name, translation.strip())

    console.print(table)


if __name__ == "__main__":
    fire.Fire(
        {
            "deploy": deploy,
            "load": load_model,
            "infer": infer,
            "run": run,
        }
    )
