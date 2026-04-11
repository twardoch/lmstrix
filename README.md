# lmstrix

Manage, test, and run local language models through [LM Studio](https://lmstudio.ai/) from the command line. Its centrepiece is a binary-search algorithm that finds the true maximum context window of any model — so you stop guessing and stop crashing.

## Background: what a context window is

A language model can only "see" a fixed number of tokens at once. This is its context window. Feed it more tokens than it can handle and it either crashes, silently truncates your input, or runs out of GPU memory mid-inference.

Every model has a theoretical maximum stated in its documentation. That number is often optimistic. The real limit depends on your hardware, quantisation level, and the LM Studio version. The only way to know for certain is to test it.

## What lmstrix does

- **Scans** your LM Studio models directory and builds a registry of available models
- **Tests** models using binary search to find their actual maximum context window
- **Persists** the results to a JSON registry so you never re-test a model you already know
- **Runs inference** via LM Studio's local API with configurable prompts and context sizes
- **Reports** test results and model metadata in formatted terminal tables

## Install

```bash
pip install lmstrix
# or
uv pip install lmstrix
```

Requires LM Studio installed and running on `localhost:1234` (the default).

## Quick start

```bash
# Discover all models in your LM Studio directory
lmstrix scan

# List discovered models and their tested context limits
lmstrix list

# Find the true context limit for a specific model
lmstrix test "llama-3.2-3b-instruct"

# Run inference at a specific context size
lmstrix infer "llama-3.2-3b-instruct" --prompt "Explain quantum entanglement" --context 8192
```

## How the context test works

Testing all possible context sizes would take hours. Binary search cuts that down to logarithmic time.

1. Start with the model's stated maximum (e.g. 131072 tokens).
2. Try loading the model at that size and running two simple inference checks: "Write 'ninety-six' as a number" and "2+3=".
3. If it succeeds, record that size as the working maximum.
4. If it fails (OOM, crash, timeout, zero tokens returned), halve the search space.
5. Repeat until the boundary is found within a small tolerance.

The test uses dual prompts because a single "say hello" prompt can succeed even when the model is misconfigured — it is too short to stress the context allocation. The two prompts require the model to produce specific, verifiable output.

Results include time-to-first-token (TTFT) and tokens-per-second (TPS) from the successful test run.

## The model registry

Scan results and test results are persisted to a JSON file (default: `~/.local/share/lmstrix/models.json` on Linux, similar paths on macOS/Windows). Subsequent `scan` runs update the registry without discarding test results. `list` reads from the registry without touching LM Studio.

## CLI reference

```
lmstrix scan              Scan LM Studio models directory and update registry
lmstrix list              List all models with context limits and test status
lmstrix test <model-id>   Binary-search for true maximum context window
lmstrix infer <model-id>  Run inference; options: --prompt, --context, --max-tokens
```

## Python API

```python
from lmstrix.api import LMStudioClient
from lmstrix.core.context_tester import ContextTester
from lmstrix.core.scanner import ModelScanner

client = LMStudioClient()
scanner = ModelScanner()
registry = scanner.scan()

tester = ContextTester(client=client, verbose=True)
model = registry.get_model("llama-3.2-3b-instruct")
updated_model = tester.test_model(model, max_context=32768, registry=registry)

print(f"Max working context: {updated_model.tested_max_context}")
print(f"TTFT: {updated_model.ttft_seconds:.2f}s")
print(f"TPS: {updated_model.tps:.1f}")
```

## LM Studio setup

LM Studio must be running with its local API server enabled (Settings → Local Server → Start Server). The default address is `http://localhost:1234`. Set `LMSTUDIO_BASE_URL` to override.

## License

MIT
