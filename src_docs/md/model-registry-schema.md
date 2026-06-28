---
# this_file: src_docs/md/model-registry-schema.md
title: Model Registry Schema
description: JSON schema and field reference for the LMStrix model registry file
---

# Model Registry Schema

LMStrix stores everything it knows about your models in a single JSON file — the **model registry**. Your GPU told you a model supports 131 072 tokens; the registry tracks whether that claim survived contact with reality.

## File Location

By default the registry lives at:

| Platform | Path |
|---|---|
| macOS / Linux | `~/.lmstrix/lmstrix.json` |
| Windows | `%USERPROFILE%\.lmstrix\lmstrix.json` |

Override with the `LMSTRIX_MODELS_FILE` environment variable or the `--models-file` CLI flag.

---

## Top-Level Structure

```json
{
  "llms": {
    "<model-id>": { ... },
    "<model-id>": { ... }
  }
}
```

The single top-level key `"llms"` maps each model's string identifier to its record.

---

## Model Record Fields

### Identity

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique model identifier — the relative path from the LM Studio models directory (e.g. `"lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"`). |
| `path` | `string` | Absolute filesystem path to the model file or directory. |
| `size_bytes` | `integer` | On-disk size in bytes. |

### Context Limits

| Field | Type | Default | Description |
|---|---|---|---|
| `ctx_in` | `integer` | `4096` | **Declared** maximum input context (from model metadata or filename heuristic). This is what the model *says* it supports. |
| `ctx_out` | `integer` | `4096` | Maximum generation length (output tokens). |
| `tested_max_context` | `integer \| null` | `null` | **Empirically verified** maximum context — what the binary-search actually confirmed works end-to-end. `null` = not yet tested. |
| `last_known_good_context` | `integer \| null` | `null` | Highest context size that produced a successful inference response. |
| `last_known_bad_context` | `integer \| null` | `null` | Lowest context size that caused a load or inference failure. |

!!! note "Declared vs. tested"
    `ctx_in` is the number your GPU vendor printed on the box. `tested_max_context` is what actually works when you load the model and generate tokens. They frequently differ — sometimes by a factor of 4×.

### Test Status

| Field | Type | Values | Description |
|---|---|---|---|
| `context_test_status` | `string` | `"untested"`, `"testing"`, `"completed"`, `"failed"` | Current state of context-limit testing. |
| `context_test_date` | `string \| null` | ISO 8601 datetime | When the last test completed (or `null` if never tested). |

### Capabilities

| Field | Type | Description |
|---|---|---|
| `has_tools` | `boolean` | Whether the model was trained for function/tool calling. |
| `has_vision` | `boolean` | Whether the model accepts image inputs. |
| `capabilities` | `object` | Extended capabilities map from LM Studio metadata. May include `"vision"`, `"trained_for_tool_use"`, `"reasoning"` sub-objects. |

#### Reasoning sub-object (optional)

```json
"capabilities": {
  "reasoning": {
    "allowed_options": ["none", "default", "high"],
    "default": "default"
  }
}
```

### Performance Metrics

These fields are recorded from the most recent successful inference test.

| Field | Type | Description |
|---|---|---|
| `ttft_seconds` | `float \| null` | Time-to-first-token in seconds. Measures how long the model takes to start generating. |
| `tps` | `float \| null` | Tokens per second during generation. |

### Optional Metadata

| Field | Type | Description |
|---|---|---|
| `description` | `string \| null` | Human-readable model description (populated by the `describe` command or LM Studio metadata). |
| `keywords` | `list[string]` | Searchable tags (e.g. `["instruct", "code", "8b"]`). Used by `--key` filter. |

---

## Complete Example

```json
{
  "llms": {
    "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf": {
      "id": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
      "path": "/Users/alice/.cache/lm-studio/models/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
      "size_bytes": 4920753152,
      "ctx_in": 131072,
      "ctx_out": 4096,
      "has_tools": true,
      "has_vision": false,
      "capabilities": {
        "trained_for_tool_use": true,
        "vision": false
      },
      "tested_max_context": 32768,
      "last_known_good_context": 32768,
      "last_known_bad_context": 65536,
      "context_test_status": "completed",
      "context_test_date": "2026-06-28T14:23:11.042519",
      "ttft_seconds": 0.412,
      "tps": 38.7,
      "description": "Meta-Llama-3.1-8B fine-tuned for instruction following",
      "keywords": ["llama", "instruct", "8b", "meta"]
    }
  }
}
```

---

## How Fields Are Populated

```
lmstrix scan          →  id, path, size_bytes, ctx_in, ctx_out,
                          has_tools, has_vision, capabilities

lmstrix test          →  tested_max_context, last_known_good_context,
                          last_known_bad_context, context_test_status,
                          context_test_date, ttft_seconds, tps

lmstrix describe      →  description, keywords
```

---

## Registry File Management

```bash
# Show registry path
lmstrix list --show json | python -c "import sys,json; print('registry at ~/.lmstrix/lmstrix.json')"

# Export models to JSON
lmstrix list --show json > my-models.json

# Reset test data for one model (re-test from scratch)
lmstrix test --model-id "my-model" --reset

# Re-test all failed models
lmstrix test --all --failed
```

The registry is a plain JSON file — you can edit it by hand, diff it in git, or share it across machines. The only invariant is that each key in `"llms"` must equal the `"id"` field of its value.
