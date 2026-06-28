---
# this_file: src_docs/md/troubleshooting.md
title: Troubleshooting
description: Common LM Studio connection issues, context errors, and registry problems — with fixes
---

# Troubleshooting

Something went wrong. Here is what probably happened and how to fix it.

---

## LM Studio Connection

### "Connection refused" / "Cannot connect to LM Studio server"

LMStrix talks to LM Studio over its local REST API (default: `http://localhost:1234`).

**Check these in order:**

1. **LM Studio is running** — open the application; it must be fully launched.
2. **The local server is enabled** — in LM Studio go to **Local Server** (the `<->` tab) and click **Start Server**. The status indicator should turn green.
3. **Port is correct** — the default is `1234`. If you changed it, set `LMSTUDIO_HOST` and `LMSTUDIO_PORT`:

    ```bash
    export LMSTUDIO_HOST=localhost
    export LMSTUDIO_PORT=1234
    lmstrix list
    ```

4. **Firewall / VPN** — some VPNs block localhost traffic. Try disabling the VPN and retrying.

---

### "Model not found" during `scan`

LMStrix scans `~/.cache/lm-studio/models/` (macOS/Linux) or `%USERPROFILE%\.cache\lm-studio\models\` (Windows).

If your models are elsewhere:

```bash
export LMSTUDIO_MODELS_PATH=/path/to/your/models
lmstrix scan
```

LM Studio must also know about the path — set it in **LM Studio → Settings → Model Search Paths**.

---

### "Server returned 503" / model loads then immediately unloads

LM Studio enforces a one-model-at-a-time constraint by default. If another application (or another `lmstrix` process) already has a model loaded, new load requests may fail.

- Close other apps that use the LM Studio API.
- In LM Studio settings, raise the **Maximum loaded models** limit if your GPU has headroom.

---

## Context Testing

### `lmstrix test` reports a much lower context than the model's declared limit

This is expected — and the whole point. The model's declared `ctx_in` (e.g. 131 072) is the architectural maximum. At that size, most consumer GPUs run out of KV-cache memory. The binary-search finds the largest context that actually fits *and generates a coherent response*.

See `tested_max_context` vs `ctx_in` in the [Model Registry Schema](model-registry-schema.md).

---

### Context test keeps failing at all sizes

1. **The model needs more VRAM** — try a smaller quantization (Q4_K_M instead of Q8_0).
2. **LM Studio server not started** — see [Connection refused](#connection-refused--cannot-connect-to-lm-studio-server) above.
3. **Inference hangs** — the default inference timeout is 90 seconds. For very slow models, the test may time out before the model responds. Try `--fast` to skip semantic validation.
4. **Embedding models** — embedding models do not generate text and will always fail inference tests. LMStrix skips models whose ID contains `embed` or `embedding`. If yours has a different naming, skip it manually.

---

### Token count approximation warning

LMStrix uses [`tiktoken`](https://github.com/openai/tiktoken) with the `cl100k_base` encoding to estimate prompt token counts before sending requests. This is an **approximation**:

- **tiktoken uses the GPT-4 tokenizer** — other model families (Llama, Mistral, Gemma, Phi, etc.) have their own tokenizers that may produce different token counts for the same text.
- Counts can differ by ±5–15% depending on the vocabulary overlap.
- For context-limit testing this is fine — the binary search validates whether the model actually accepts the context, not whether our token count was exact.
- For production inference where you need precise control over prompt length, use the model's own tokenizer if available.

---

## Model Registry

### Registry file is missing or corrupt

```bash
# Re-create from scratch (re-scans all models)
lmstrix scan --reset

# Specify a different registry file
lmstrix --models-file /path/to/registry.json scan
```

### Model shows as "untested" after `lmstrix test`

The test command only runs models that are in the registry. Make sure you ran `lmstrix scan` first:

```bash
lmstrix scan        # discover models
lmstrix test --all  # test all untested models
```

### Registry shows stale models I deleted from disk

```bash
lmstrix scan  # removes models that no longer exist on disk
```

---

## CLI Errors

### `lmstrix: command not found`

The `lmstrix` entry point was not installed. Install with:

```bash
pip install lmstrix
# or
uv pip install lmstrix
```

If it is installed but not found, your Python scripts directory may not be on `PATH`. Try `python -m lmstrix` as a fallback.

---

### `ModuleNotFoundError: No module named 'lmstudio'`

The official LM Studio Python SDK (`lmstudio>=1.4.1`) is a required dependency. It should install automatically. If it did not:

```bash
pip install "lmstrix[dev]"
# or install the SDK directly
pip install "lmstudio>=1.4.1"
```

The SDK requires Python 3.11 or later and a running LM Studio server to function.

---

## Getting More Information

```bash
# Verbose mode shows all API calls and retry attempts
lmstrix --verbose scan

# Check what LM Studio server lmstrix is connecting to
lmstrix list --verbose 2>&1 | grep "Connecting"
```

For bugs, open an issue at <https://github.com/twardoch/lmstrix/issues> and include:

- Output of `lmstrix list --verbose`
- LM Studio version (`Help → About`)
- Python version (`python --version`)
- Operating system
