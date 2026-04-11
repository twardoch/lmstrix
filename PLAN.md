# LMStrix Refactor Plan: Enforce ≤300 LOC per Python File

## Goal

Refactor the Python codebase so that no single `.py` file exceeds 300 lines, while preserving:
- CLI behavior and argument signatures
- the current public Python API from `lmstrix.__init__`
- current inference, streaming, testing, and model-registry behavior

This plan is file-specific and sequenced to reduce risk. The first implementation wave should target low-coupling command methods in `src/lmstrix/api/main.py`, then move deeper into inference and registry internals.

## Ground Rules

1. Split by responsibility, not by arbitrary line count.
2. Preserve import compatibility at existing public entrypoints.
3. Keep `LMStrixService` in `src/lmstrix/api/main.py` as the CLI-facing facade used by `src/lmstrix/__main__.py`.
4. Keep `lmstrix.__init__` re-exports stable unless a compatibility shim is added.
5. Avoid redesigning domain models during the line-limit refactor.

## Current Oversized Files

### Production
- `src/lmstrix/api/main.py` — 1671
- `src/lmstrix/core/inference.py` — 603
- `src/lmstrix/api/client.py` — 541
- `src/lmstrix/core/inference_manager.py` — 479
- `src/lmstrix/core/describer.py` — 410
- `src/lmstrix/core/prompts.py` — 386
- `src/lmstrix/loaders/model_loader.py` — 366
- `src/lmstrix/core/models.py` — 343
- `src/lmstrix/core/context_tester.py` — 335

### Tests
- `tests/test_core/test_models.py` — 304

## Public API and Compatibility Constraints

### `src/lmstrix/__main__.py`
`LMStrixCLI` delegates directly to `LMStrixService` methods:
- `scan_models`
- `list_models`
- `describe_models`
- `test_models`
- `run_inference`
- `check_health`
- `save_configs`
- `about`
- `show_help`

These method names and signatures must remain stable.

### `src/lmstrix/__init__.py`
Current re-exports include:
- `ContextTester`
- `InferenceManager`
- `Model`
- `load_model_registry`
- `save_model_registry`
- `scan_and_update_registry`
- parsing utilities and logger

Module moves must preserve these import surfaces.

---

# File-by-File Plan

## 1. `src/lmstrix/api/main.py` (1671)

### Current responsibilities
- CLI service facade (`LMStrixService`)
- test helper functions
- list/describe/test/infer/health/save/about/help command implementations
- Rich rendering and output formatting

### Natural seams already present
- top-level testing helpers:
  - `_format_response_preview`
  - `_get_models_to_test`
  - `_sort_models`
  - `_test_single_model`
  - `_test_all_models_at_ctx`
  - `_test_all_models_optimized`
  - `_print_final_results`
- service methods:
  - `scan_models`
  - `list_models`
  - `describe_models`
  - `test_models`
  - `run_inference`
  - `check_health`
  - `save_configs`
  - `about`
  - `show_help`

### Target structure
- `src/lmstrix/api/main.py` — keep facade + shared test helpers only
- `src/lmstrix/api/listing.py` — `list_models` implementation
- `src/lmstrix/api/describe.py` — `describe_models` implementation
- `src/lmstrix/api/health.py` — `check_health` implementation
- `src/lmstrix/api/configs.py` — `save_configs` implementation
- `src/lmstrix/api/about.py` — `about` implementation
- `src/lmstrix/api/helptext.py` — `show_help` implementation
- later wave: `src/lmstrix/api/testing.py` — batch/single test orchestration
- later wave: `src/lmstrix/api/infer.py` — inference command flow

### Implementation order inside this file
#### Wave 1
Extract first because they are independent and low risk:
- `list_models`
- `describe_models`
- `check_health`
- `save_configs`
- `about`
- `show_help`

#### Wave 2
Extract test orchestration:
- `_test_all_models_at_ctx`
- `_test_all_models_optimized`
- `_print_final_results`
- possibly `_test_single_model`
- `test_models`

#### Wave 3
Extract inference command:
- prompt preparation
- model resolution / last-used-model fallback
- `in_ctx` / `out_ctx` parsing
- execution branch (streaming vs non-streaming)

### Risks
- `scan_models` currently calls `self.list_models(...)`; wrapper must keep `_registry` behavior
- `show_help` is also used by `__main__.py` fallback path
- `run_inference` is behavior-dense and should not be changed in the first wave

### Success state
- `api/main.py` becomes a thin service facade plus a smaller set of shared helpers
- all extracted methods remain reachable through `LMStrixService`

---

## 2. `src/lmstrix/core/inference.py` (603)

### Current responsibilities
- `InferenceResult` type
- capability probing
- finding a working context after failure
- blocking inference
- streaming inference

### Target structure
- `src/lmstrix/core/inference_types.py`
- `src/lmstrix/core/inference_probe.py`
- `src/lmstrix/core/inference_recovery.py`
- `src/lmstrix/core/inference_engine.py`

### Planned split
- `InferenceResult` → `inference_types.py`
- `_test_inference_capability` → `inference_probe.py`
- `_find_working_context` → `inference_recovery.py`
- `infer` + `stream_infer` support logic → `inference_engine.py`

### Special caution
This file overlaps heavily with `src/lmstrix/core/inference_manager.py`. Do not fully split both in isolation; first define ownership and shared helpers.

---

## 3. `src/lmstrix/core/inference_manager.py` (479)

### Current responsibilities
- high-level inference orchestration
- model lookup / load / reuse logic
- OOM retry fallback
- blocking and streaming execution paths

### Target structure
- `src/lmstrix/core/inference_manager.py` — thin facade only
- `src/lmstrix/core/inference_session.py`
- `src/lmstrix/core/inference_loading.py`
- `src/lmstrix/core/inference_streaming.py`

### Planned split
- shared model loading and reuse logic → `inference_loading.py`
- shared fallback/retry logic → `inference_session.py`
- streaming-specific execution path → `inference_streaming.py`

### Coupling note
`ContextTester` currently depends on `InferenceEngine._test_inference_capability`. Consolidate shared probe logic before changing tester behavior.

---

## 4. `src/lmstrix/api/client.py` (541)

### Current responsibilities
- `CompletionResponse` type
- model discovery/load/unload methods
- blocking completion path
- streaming completion path
- config assembly and stats extraction

### Target structure
- `src/lmstrix/api/client_types.py`
- `src/lmstrix/api/client_models.py`
- `src/lmstrix/api/client_completion.py`
- `src/lmstrix/api/client_streaming.py`
- `src/lmstrix/api/client.py` — thin facade

### Planned split
- `CompletionResponse` → `client_types.py`
- model lifecycle methods → `client_models.py`
- `completion` → `client_completion.py`
- `stream_completion` → `client_streaming.py`
- shared config/logging helpers → private helper section or `client_common.py`

---

## 5. `src/lmstrix/core/describer.py` (410)

### Current responsibilities
- keyword vocabulary constants
- prompt building and response parsing
- droid/LLM description execution
- keyword filtering/sorting/markdown report rendering

### Target structure
- `src/lmstrix/core/describer_protocol.py`
- `src/lmstrix/core/describer_runner.py`
- `src/lmstrix/core/describer_views.py`

### Planned split
- constants + `_build_prompt` + `_parse_response` + `_has_description` → `describer_protocol.py`
- `describe_single_model_droid`, `describe_single_model`, `describe_models` → `describer_runner.py`
- `filter_models_by_keywords`, `sort_models_by_keywords`, `format_models_markdown` → `describer_views.py`

---

## 6. `src/lmstrix/core/prompts.py` (386)

### Current responsibilities
- `ResolvedPrompt`
- placeholder parsing
- internal/external resolution
- token counting and truncation
- context injection
- high-level template resolution

### Target structure
- `src/lmstrix/core/prompts_types.py`
- `src/lmstrix/core/prompts_parsing.py`
- `src/lmstrix/core/prompts_resolution.py`
- `src/lmstrix/core/prompts_tokens.py`
- `src/lmstrix/core/prompts_facade.py`

### Planned split
- type definitions → `prompts_types.py`
- placeholder and path helpers → `prompts_parsing.py`
- phase resolution logic → `prompts_resolution.py`
- token and truncation helpers → `prompts_tokens.py`
- public resolver facade → `prompts_facade.py`

---

## 7. `src/lmstrix/loaders/model_loader.py` (366)

### Current responsibilities
- registry load/save
- discovered model validation
- registry sync/update helpers
- reset maintenance

### Target structure
- `src/lmstrix/loaders/model_registry_io.py`
- `src/lmstrix/loaders/model_registry_sync.py`
- `src/lmstrix/loaders/model_registry_maintenance.py`

### Planned split
- `load_model_registry`, `save_model_registry` → `model_registry_io.py`
- discovery/update/remove helpers + `scan_and_update_registry` → `model_registry_sync.py`
- `reset_test_data` → `model_registry_maintenance.py`

---

## 8. `src/lmstrix/core/models.py` (343)

### Current responsibilities
- `ContextTestStatus`
- `Model`
- `ModelRegistryError`
- `ModelRegistry`

### Target structure
- `src/lmstrix/core/model_types.py`
- `src/lmstrix/core/model_entity.py`
- `src/lmstrix/core/model_registry.py`

### Planned split
- `ContextTestStatus` → `model_types.py`
- `Model` → `model_entity.py`
- `ModelRegistryError` + `ModelRegistry` → `model_registry.py`

### Caution
`Model` has compatibility-heavy hand-rolled serialization and `extra` passthrough behavior. Move it without redesign.

---

## 9. `src/lmstrix/core/context_tester.py` (335)

### Current responsibilities
- `ContextTestResult`
- single-context probe execution
- embedding-model filtering
- batch threshold testing
- per-model binary search testing

### Target structure
- `src/lmstrix/core/context_test_types.py`
- `src/lmstrix/core/context_test_runner.py`
- `src/lmstrix/core/context_test_batch.py`

### Planned split
- `ContextTestResult` → `context_test_types.py`
- `_test_at_context`, `_is_embedding_model`, `_filter_models_for_testing`, `test_model` → `context_test_runner.py`
- `test_all_models`, `test_model_by_id` → `context_test_batch.py`

---

## 10. `tests/test_core/test_models.py` (304)

### Current responsibilities
- mixed tests for both `Model` and `ModelRegistry`

### Target structure
- `tests/test_core/test_model_entity.py`
- `tests/test_core/test_model_registry.py`

### Planned split
Separate tests by unit under test rather than fixture grouping.

---

# Implementation Waves

## Wave 1 — Immediate, low-risk extraction from `api/main.py`
- Extract `list_models` to `src/lmstrix/api/listing.py`
- Extract `describe_models` to `src/lmstrix/api/describe.py`
- Extract `check_health` to `src/lmstrix/api/health.py`
- Extract `save_configs` to `src/lmstrix/api/configs.py`
- Extract `about` to `src/lmstrix/api/about.py`
- Extract `show_help` to `src/lmstrix/api/helptext.py`
- Replace method bodies in `LMStrixService` with delegating wrappers

## Wave 2 — Reduce `api/main.py` further
- Move test orchestration helpers into `src/lmstrix/api/testing.py`
- Keep only tiny wrappers and shared utilities in `main.py`

## Wave 3 — Resolve inference duplication safely
- Extract shared loading/retry helpers used by `InferenceEngine` and `InferenceManager`
- Then split the two modules into smaller files

## Wave 4 — Split remaining core and loader modules
- `api/client.py`
- `core/describer.py`
- `core/prompts.py`
- `loaders/model_loader.py`
- `core/models.py`
- `core/context_tester.py`

## Wave 5 — Tests and cleanup
- split oversized test files
- run focused tests per subsystem
- run full suite and note pre-existing unrelated failures

---

# Immediate Implementation Checklist

## For the work starting now
- [ ] Rewrite `PLAN.md` with this file-by-file plan
- [ ] Extract low-coupling command methods from `src/lmstrix/api/main.py`
- [ ] Keep `LMStrixService` signatures unchanged
- [ ] Run diagnostics on changed files
- [ ] Run targeted tests or repo checks relevant to the extracted API command methods
- [ ] Recount Python LOC and confirm whether `api/main.py` meaningfully shrank

## Definition of Done for the overall refactor
- [ ] Every `.py` file is at or below 300 LOC
- [ ] CLI behavior remains unchanged
- [ ] Public imports remain stable
- [ ] Tests pass or only known pre-existing failures remain
- [ ] No new diagnostics are introduced
