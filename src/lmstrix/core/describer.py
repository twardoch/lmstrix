# this_file: src/lmstrix/core/describer.py
"""Model describer: uses LLM to generate model descriptions and keyword tags."""

from __future__ import annotations

import json
import re
import subprocess
from typing import TYPE_CHECKING

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from lmstrix.core.inference_manager import InferenceManager

DROID_TIMEOUT_SECS = 120

if TYPE_CHECKING:
    from lmstrix.core.models import Model, ModelRegistry

# Valid keyword vocabulary, grouped by category
KEYWORD_VOCAB: dict[str, list[str]] = {
    "arch": [
        "arch-dense",
        "arch-gguf",
        "arch-mlx",
        "arch-moe",
    ],
    "inp": [
        "inp-audio",
        "inp-image",
        "inp-instruct",
        "inp-multiling",
        "inp-speech",
    ],
    "outp": [
        "outp-audio",
        "outp-caption",
        "outp-chat",
        "outp-code",
        "outp-data",
        "outp-docstruct",
        "outp-image",
        "outp-ocr",
        "outp-speech",
        "outp-text",
        "outp-tldr",
        "outp-translat",
    ],
    "proc": [
        "proc-agentic",
        "proc-longctx",
        "proc-thinking",
    ],
}

ALL_KEYWORDS: set[str] = {kw for group in KEYWORD_VOCAB.values() for kw in group}

DESCRIBE_PROMPT_TEMPLATE = """\
You are a technical AI model analyst. Given a model's metadata, produce a JSON object with:

1. "id": a short lowercase kebab-case identifier for the model (e.g. "llama-3-8b-gguf")
2. "description": a detailed 2-4 sentence technical description covering architecture family, \
parameter count (if inferable from size), training focus, key strengths, and primary use cases.
3. "keywords": a list of 3-12 keyword tags from the EXACT vocabulary below. Assign 0-3 keywords \
from EACH category.

KEYWORD VOCABULARY (use ONLY these exact strings):
Architecture: arch-dense, arch-gguf, arch-mlx, arch-moe
Input: inp-audio, inp-image, inp-instruct, inp-multiling, inp-speech
Output: outp-audio, outp-caption, outp-chat, outp-code, outp-data, outp-docstruct, outp-image, \
outp-ocr, outp-speech, outp-text, outp-tldr, outp-translat
Processing: proc-agentic, proc-longctx, proc-thinking

KEYWORD ASSIGNMENT RULES:
- arch-gguf: if model path contains "gguf" or format is GGUF
- arch-mlx: if model path contains "mlx" or format is MLX
- arch-dense: standard transformer without mixture-of-experts
- arch-moe: mixture-of-experts architecture (e.g. Mixtral, DBRX, Grok)
- inp-image/inp-audio/inp-speech: if model has vision/audio/speech input capability
- inp-instruct: if model is instruction-tuned (most chat models)
- inp-multiling: if model supports multiple languages
- outp-chat: general conversational output
- outp-code: code generation or code-related tasks
- outp-text: general text generation
- proc-longctx: if context window >= 32768
- proc-thinking: if model name suggests chain-of-thought/reasoning (e.g. "think", "reasoning")
- proc-agentic: if model supports tool/function calling

MODEL METADATA:
- Model path: {model_path}
- Model ID: {model_id}
- Size: {size_gb:.2f} GB
- Has vision: {has_vision}
- Has tool calling: {has_tools}
- Context window: {ctx_in}

Respond with ONLY a valid JSON object (no markdown, no explanation):
{{"id": "...", "description": "...", "keywords": [...]}}
"""


def _build_prompt(model: Model) -> str:
    """Build the description prompt from model metadata."""
    size_gb = model.size / (1024**3) if model.size else 0.0
    return DESCRIBE_PROMPT_TEMPLATE.format(
        model_path=model.path,
        model_id=model.id,
        size_gb=size_gb,
        has_vision=model.has_vision,
        has_tools=model.has_tools,
        ctx_in=model.context_limit,
    )


def _parse_response(response_text: str) -> dict | None:
    """Parse LLM JSON response, extracting from markdown code blocks if needed."""
    text = response_text.strip()
    # Strip markdown code fences if present
    md_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM response as JSON: {text[:200]}")
        return None

    if not isinstance(data, dict):
        logger.warning(f"LLM response is not a JSON object: {type(data)}")
        return None

    # Validate and filter keywords
    raw_keywords = data.get("keywords", [])
    if not isinstance(raw_keywords, list):
        raw_keywords = []
    valid_keywords = [kw for kw in raw_keywords if kw in ALL_KEYWORDS]
    if len(valid_keywords) != len(raw_keywords):
        invalid = set(raw_keywords) - ALL_KEYWORDS
        logger.debug(f"Filtered out invalid keywords: {invalid}")

    return {
        "id": data.get("id", ""),
        "description": data.get("description", ""),
        "keywords": valid_keywords,
    }


def _has_description(model: Model) -> bool:
    """Check if model already has a valid description."""
    desc = model.description
    if not desc or not desc.strip():
        return False
    # Skip placeholder descriptions starting with '['
    return not desc.strip().startswith("[")


def describe_single_model_droid(
    model: Model,
    *,
    verbose: bool = False,
) -> dict | None:
    """Use droid exec (subprocess) to generate description and keywords for a model.

    Fallback method when no LLM model ID is specified. Requires 'droid' CLI on PATH.
    Returns dict with id, description, keywords on success, None on failure.
    """
    prompt = _build_prompt(model)
    logger.debug(f"Describing model {model.id} via droid exec")

    try:
        result = subprocess.run(
            ["droid", "exec", prompt],
            capture_output=True,
            text=True,
            timeout=DROID_TIMEOUT_SECS,
        )
        response_text = result.stdout.strip()
        if not response_text and result.stderr.strip():
            logger.error(f"droid exec error for {model.id}: {result.stderr.strip()[:300]}")
            return None
        if not response_text:
            logger.error(f"droid exec returned empty response for {model.id}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"droid exec timed out for {model.id}")
        return None
    except FileNotFoundError:
        logger.error("'droid' CLI not found on PATH. Install it or use --model MODEL_ID.")
        return None
    except Exception as e:
        logger.error(f"droid exec failed for {model.id}: {e}")
        return None

    parsed = _parse_response(response_text)
    if parsed is None:
        logger.error(f"Failed to parse droid response for {model.id}")
        return None

    if verbose:
        logger.info(
            f"Described {model.id}: {len(parsed['keywords'])} keywords, "
            f"{len(parsed['description'])} chars"
        )

    return parsed


def describe_single_model(
    model: Model,
    inference_mgr: InferenceManager,
    describer_model_id: str,
    *,
    verbose: bool = False,
) -> dict | None:
    """Use LLM via InferenceManager to generate description and keywords for a model.

    Returns dict with id, description, keywords on success, None on failure.
    """
    prompt = _build_prompt(model)
    logger.debug(f"Describing model {model.id} using {describer_model_id}")

    result = inference_mgr.infer(
        model_id=describer_model_id,
        prompt=prompt,
        out_ctx=2048,
        temperature=0.3,
    )

    if not result.get("succeeded"):
        logger.error(f"LLM inference failed for {model.id}: {result.get('error')}")
        return None

    response_text = result.get("response", "")
    parsed = _parse_response(response_text)
    if parsed is None:
        logger.error(f"Failed to parse description for {model.id}")
        return None

    if verbose:
        logger.info(
            f"Described {model.id}: {len(parsed['keywords'])} keywords, "
            f"{len(parsed['description'])} chars"
        )

    return parsed


def describe_models(
    registry: ModelRegistry,
    describer_model_id: str | None = None,
    *,
    model_id: str | None = None,
    reset: bool = False,
    verbose: bool = False,
) -> int:
    """Describe models in the registry using an LLM or droid exec fallback.

    When describer_model_id is provided, uses InferenceManager to call that LLM.
    When describer_model_id is None, falls back to 'droid exec' subprocess.
    """
    console = Console()
    use_droid = describer_model_id is None

    inference_mgr = None
    if not use_droid:
        inference_mgr = InferenceManager(verbose=verbose)

    all_models = registry.list_models()
    if model_id:
        models_to_describe = [m for m in all_models if model_id in (m.id, m.path)]
        if not models_to_describe:
            console.print(f"[red]Model not found: {model_id}[/red]")
            return 0
    else:
        models_to_describe = all_models

    if not reset:
        models_to_describe = [m for m in models_to_describe if not _has_description(m)]

    if not models_to_describe:
        console.print(
            "[yellow]All models already have descriptions. Use --reset to re-describe.[/yellow]"
        )
        return 0

    total = len(models_to_describe)
    described = 0
    method_label = "droid exec" if use_droid else describer_model_id

    console.print(f"[bold]Describing {total} model(s) using [cyan]{method_label}[/cyan]...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Describing models...", total=total)

        for model in models_to_describe:
            progress.update(task, description=f"Describing {model.id}...")

            if use_droid:
                result = describe_single_model_droid(model, verbose=verbose)
            else:
                assert inference_mgr is not None
                assert describer_model_id is not None
                result = describe_single_model(
                    model,
                    inference_mgr,
                    describer_model_id,
                    verbose=verbose,
                )

            if result:
                model.description = result["description"]
                model.keywords = result["keywords"]
                if result.get("id"):
                    model.short_id = result["id"]
                registry.update_model_by_id(model)
                described += 1
                logger.info(f"Described {model.id} ({described}/{total})")
            else:
                logger.warning(f"Skipped {model.id} (description failed)")

            progress.advance(task)

    console.print(f"[bold green]Described {described}/{total} models.[/bold green]")
    return described


def filter_models_by_keywords(
    models: list[Model],
    keywords: list[str],
) -> list[Model]:
    """Filter models to only those matching ALL specified keywords."""
    if not keywords:
        return models
    keyword_set = set(keywords)
    return [m for m in models if keyword_set.issubset(set(m.keywords))]


def sort_models_by_keywords(
    models: list[Model],
    sort_key: str,
) -> list[Model]:
    """Sort models by keyword category count.

    Sort keys: arch, archd, inp, inpd, outp, outpd, proc, procd.
    'd' suffix means descending. Within tied groups, falls back to smart/smartd.
    """
    descending = sort_key.endswith("d")
    category = sort_key.rstrip("d")

    if category not in KEYWORD_VOCAB:
        logger.warning(f"Unknown keyword sort category: {category}")
        return models

    category_keywords = set(KEYWORD_VOCAB[category])

    def keyword_sort_key(model: Model) -> tuple:
        """Return (keyword_count, smart_sort_key) for sorting."""
        model_kws = set(model.keywords) if model.keywords else set()
        matching = model_kws & category_keywords
        # Sort alphabetically by the matched keywords for consistent ordering
        kw_str = ",".join(sorted(matching))
        # Smart sort fallback: size descending, then tested context descending
        size_val = model.size or 0
        tested_ctx = model.tested_max_context or 0
        return (len(matching), kw_str, size_val, tested_ctx)

    return sorted(models, key=keyword_sort_key, reverse=descending)


def format_models_markdown(models: list[Model]) -> str:
    """Format models as a Markdown report with descriptions and keywords."""
    lines: list[str] = []
    lines.append("# LMStrix Model Report\n")

    for model in models:
        size_gb = model.size / (1024**3) if model.size else 0.0
        lines.append(f"## {model.id}\n")
        lines.append(f"- **Short ID**: `{model.short_id}`")
        lines.append(f"- **Path**: `{model.path}`")
        lines.append(f"- **Size**: {size_gb:.2f} GB")
        lines.append(f"- **Context**: {model.context_limit}")
        if model.has_vision:
            lines.append("- **Vision**: Yes")
        if model.has_tools:
            lines.append("- **Tool calling**: Yes")
        if model.tested_max_context:
            lines.append(f"- **Tested context**: {model.tested_max_context}")
        if model.ttft_seconds is not None:
            lines.append(f"- **TTFT**: {model.ttft_seconds:.3f}s")
        if model.tps is not None:
            lines.append(f"- **TPS**: {model.tps:.1f}")

        if model.keywords:
            kw_str = ", ".join(f"`{kw}`" for kw in sorted(model.keywords))
            lines.append(f"- **Keywords**: {kw_str}")

        if model.description:
            lines.append(f"\n{model.description}\n")
        else:
            lines.append("\n*No description available.*\n")

        lines.append("---\n")

    return "\n".join(lines)
