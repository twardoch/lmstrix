# this_file: src/lmstrix/api/infer.py

import sys
from pathlib import Path

from rich.console import Console

from lmstrix.core.inference_manager import InferenceManager
from lmstrix.loaders.model_loader import load_model_registry
from lmstrix.loaders.prompt_loader import load_single_prompt
from lmstrix.utils import setup_logging
from lmstrix.utils.context_parser import get_model_max_context, parse_out_ctx
from lmstrix.utils.logging import logger
from lmstrix.utils.state import StateManager

console = Console()


def run_inference_command(
    prompt: str,
    model_id: str | None = None,
    out_ctx: int | str = -1,
    in_ctx: int | str | None = None,
    reload: bool = False,
    file_prompt: str | None = None,
    dict_params: str | None = None,
    text: str | None = None,
    text_file: str | None = None,
    param_temp: float = 0.8,
    param_top_k: int = 40,
    param_top_p: float = 0.95,
    param_repeat: float = 1.1,
    param_min_p: float = 0.05,
    stream: bool = False,
    stream_timeout: int = 120,
    verbose: bool = False,
) -> None:
    setup_logging(verbose=verbose)

    if not out_ctx:
        out_ctx = -1

    if not file_prompt and (text or text_file):
        if text_file:
            try:
                text_path = Path(text_file).expanduser()
                if not text_path.exists():
                    logger.error(f"Text file not found: {text_file}")
                    return
                text_content = text_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.debug(f"Error reading text file: {e}")
                return
        else:
            text_content = text or ""

        actual_prompt = prompt.replace("{{text}}", text_content)
    elif file_prompt:
        prompt_params = {}
        if dict_params:
            pairs = dict_params.split(",") if "," in dict_params else dict_params.split(",")

            for pair in pairs:
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    prompt_params[key.strip()] = value.strip()
                else:
                    logger.debug(
                        f"Warning: Invalid parameter format '{pair}'. Expected 'key=value'.",
                    )

        if text_file:
            try:
                text_path = Path(text_file).expanduser()
                if not text_path.exists():
                    logger.error(f"Text file not found: {text_file}")
                    return
                prompt_params["text"] = text_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.debug(f"Error reading text file: {e}")
                return
        elif text:
            prompt_params["text"] = text

        try:
            prompt_path = Path(file_prompt).expanduser()
            if not prompt_path.exists():
                logger.error(f"Prompt file not found: {file_prompt}")
                return

            if "," in prompt:
                prompt_names = [name.strip() for name in prompt.split(",") if name.strip()]
                concatenated_prompts = []
                all_placeholders_resolved = []
                all_placeholders_unresolved = []

                if verbose:
                    logger.debug(f"Loading multiple prompts: {', '.join(prompt_names)}")

                for prompt_name in prompt_names:
                    resolved_prompt = load_single_prompt(
                        toml_path=prompt_path,
                        prompt_name=prompt_name,
                        verbose=verbose,
                        **prompt_params,
                    )
                    concatenated_prompts.append(resolved_prompt.resolved)
                    all_placeholders_resolved.extend(
                        resolved_prompt.placeholders_resolved,
                    )
                    all_placeholders_unresolved.extend(
                        resolved_prompt.placeholders_unresolved,
                    )

                    if verbose:
                        logger.debug(f"Loaded prompt '{prompt_name}' from {file_prompt}")

                actual_prompt = "\n\n".join(concatenated_prompts)

                if verbose:
                    logger.debug(f"Concatenated {len(prompt_names)} prompts")
                    if all_placeholders_resolved:
                        unique_resolved = list(set(all_placeholders_resolved))
                        logger.debug(
                            f"Resolved placeholders: {', '.join(unique_resolved)}",
                        )
                    if all_placeholders_unresolved:
                        unique_unresolved = list(set(all_placeholders_unresolved))
                        logger.debug(
                            f"Warning: Unresolved placeholders: {', '.join(unique_unresolved)}",
                        )
            else:
                resolved_prompt = load_single_prompt(
                    toml_path=prompt_path,
                    prompt_name=prompt,
                    verbose=verbose,
                    **prompt_params,
                )

                actual_prompt = resolved_prompt.resolved

                if verbose:
                    logger.debug(f"Loaded prompt '{prompt}' from {file_prompt}")
                    if resolved_prompt.placeholders_resolved:
                        logger.debug(
                            f"Resolved placeholders: {', '.join(resolved_prompt.placeholders_resolved)}",
                        )
                    if resolved_prompt.placeholders_unresolved:
                        logger.debug(
                            f"Warning: Unresolved placeholders: {', '.join(resolved_prompt.placeholders_unresolved)}",
                        )

        except Exception as e:
            logger.debug(f"Error loading prompt from file: {e}")
            return
    else:
        actual_prompt = prompt

    state_manager = StateManager()

    if not model_id:
        model_id = state_manager.get_last_used_model()
        if not model_id:
            logger.error("No model specified and no last-used model found.")
            logger.debug("Please specify a model with -m or --model_id")
            return
        if verbose:
            logger.debug(f"Using last-used model: {model_id}")

    registry = load_model_registry(verbose=verbose)
    model = registry.find_model(model_id)
    if not model:
        logger.error(f"Model '{model_id}' not found in registry.")
        return

    state_manager.set_last_used_model(model_id)

    if reload and in_ctx is None:
        in_ctx = model.tested_max_context or model.context_limit
        logger.debug(f"Force reload requested, loading with context {in_ctx:,}")

    if isinstance(out_ctx, str) and out_ctx != "-1":
        try:
            max_context = get_model_max_context(model, use_tested=True)
            if not max_context:
                max_context = model.context_limit
            parsed_out_ctx = parse_out_ctx(out_ctx, max_context)
            if verbose:
                logger.debug(f"Parsed out_ctx '{out_ctx}' as {parsed_out_ctx} tokens")
            out_ctx = parsed_out_ctx
        except ValueError as e:
            logger.error(f"{e}")
            return

    if isinstance(in_ctx, str):
        try:
            max_context = get_model_max_context(model, use_tested=True)
            if not max_context:
                max_context = model.context_limit
            parsed_in_ctx = parse_out_ctx(in_ctx, max_context)
            if verbose:
                logger.debug(f"Parsed in_ctx '{in_ctx}' as {parsed_in_ctx} tokens")
            in_ctx = parsed_in_ctx
        except ValueError as e:
            logger.error(f"{e}")
            return

    resolved_out_ctx: int = -1 if out_ctx == "-1" else int(out_ctx)

    manager = InferenceManager(registry=registry, verbose=verbose)

    if stream:
        try:
            if verbose:
                print(f"\nStreaming inference on {model.id}...", file=sys.stderr)

            def print_token(token: str) -> None:
                print(token, end="", flush=True, file=sys.stdout)

            for _token in manager.stream_infer(
                model_id=model.id,
                prompt=actual_prompt,
                in_ctx=in_ctx,
                out_ctx=resolved_out_ctx,
                temperature=param_temp,
                top_k=param_top_k,
                top_p=param_top_p,
                repeat_penalty=param_repeat,
                min_p=param_min_p,
                on_token=print_token,
                stream_timeout=stream_timeout,
            ):
                pass

            print("", file=sys.stdout)

        except Exception as e:
            print(f"\nStreaming inference failed: {e}", file=sys.stderr)
    else:
        if verbose:
            with console.status(f"Running inference on {model.id}..."):
                result = manager.infer(
                    model_id=model.id,
                    prompt=actual_prompt,
                    in_ctx=in_ctx,
                    out_ctx=resolved_out_ctx,
                    temperature=param_temp,
                    top_k=param_top_k,
                    top_p=param_top_p,
                    repeat_penalty=param_repeat,
                    min_p=param_min_p,
                )
        else:
            result = manager.infer(
                model_id=model.id,
                prompt=actual_prompt,
                in_ctx=in_ctx,
                out_ctx=resolved_out_ctx,
                temperature=param_temp,
                top_k=param_top_k,
                top_p=param_top_p,
                repeat_penalty=param_repeat,
                min_p=param_min_p,
            )

        if result["succeeded"]:
            if verbose:
                print("\nModel Response:", file=sys.stderr)
            print(result["response"], file=sys.stdout)
        else:
            print(f"Inference failed: {result['error']}", file=sys.stderr)
