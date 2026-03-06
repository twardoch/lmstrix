# AGENT_INSTRUCTIONS.md

This file provides guidance to AI agents when working with code in this repository.

## 1. Commands

### 1.1. Development

- **Run tests**: `pytest` or `hatch run test`
- **Run tests with coverage**: `pytest --cov=src/lmstrix --cov-report=html` or `hatch run test-cov`
- **Run specific test file**: `pytest tests/test_api/test_exceptions.py`
- **Run only unit tests**: `pytest -m "not integration"`

### 1.2. Linting and Formatting

- **Format code**: `hatch run lint:fmt` or `black . && ruff check --fix .`
- **Check style**: `hatch run lint:style` or `ruff check . && black --check --diff .`
- **Type checking**: `hatch run lint:typing` or `mypy --install-types --non-interactive src/lmstrix tests`
- **All linting**: `hatch run lint:all`

### 1.3. Build and Package

- **Build package**: `hatch build` or use `./build.sh` (runs lint, tests, and builds)
- **Install for development**: `pip install -e .`

## 2. Architecture

LMStrix is a Python toolkit for managing and testing LM Studio models with automatic context limit discovery. The core innovation is the **Adaptive Context Optimizer** that uses binary search to find the true operational context window for any model.

### 2.1. Key Components

1. **API Layer** (`src/lmstrix/api/`)
   - `client.py`: Async client for LM Studio server API with retry logic
   - `exceptions.py`: Custom exception hierarchy for better error handling

2. **Core Engine** (`src/lmstrix/core/`)
   - `context_tester.py`: Binary search algorithm to find optimal context window size
   - `inference.py`: Two-phase prompt templating system (structure + content)
   - `models.py`: Model registry with persistence for tracking tested context limits
   - `scanner.py`: Discovers and catalogs available LM Studio models
   - `prompts.py`: Prompt resolution and template management

3. **Loaders** (`src/lmstrix/loaders/`)
   - `model_loader.py`: Manages model registry persistence (JSON)
   - `prompt_loader.py`: Loads prompt templates from TOML files
   - `context_loader.py`: Loads context data from text files

4. **CLI** (`src/lmstrix/cli/`)
   - `main.py`: Fire-based CLI with commands: `scan`, `list`, `optimize`, `infer`
   - Uses Rich for beautiful terminal output

### 2.2. Critical Design Patterns

- **Async-First**: All API operations use async/await for high performance
- **Retry Logic**: Uses tenacity for automatic retries with exponential backoff
- **Model Registry**: Persists discovered models and their tested limits to JSON
- **Two-Phase Prompts**: Separates prompt template structure from runtime context
- **Binary Search**: Efficiently finds maximum context window through targeted testing

### 2.3. Dependencies

- `lmstudio>=1.4.1`: Official LM Studio Python SDK
- `httpx`: Async HTTP client
- `pydantic`: Data validation and models
- `fire`: CLI framework
- `rich`: Terminal formatting
- `tenacity`: Retry logic
- `tiktoken`: Token counting

# Software Development Rules

## 3. Pre-Work Preparation

### 3.1. Before Starting Any Work

- **ALWAYS** read `WORK.md` in the main project folder for work progress
- Read `README.md` to understand the project
- STEP BACK and THINK HEAVILY STEP BY STEP about the task
- Consider alternatives and carefully choose the best option
- Check for existing solutions in the codebase before starting

### 3.2. Project Documentation to Maintain

- `README.md` - purpose and functionality
- `CHANGELOG.md` - past change release notes (accumulative)
- `PLAN.md` - detailed future goals, clear plan that discusses specifics
- `TODO.md` - flat simplified itemized `- [ ]`-prefixed representation of `PLAN.md`
- `WORK.md` - work progress updates

## 4. General Coding Principles

### 4.1. Core Development Approach

- Iterate gradually, avoiding major changes
- Focus on minimal viable increments and ship early
- Minimize confirmations and checks
- Preserve existing code/structure unless necessary
- Check often the coherence of the code you're writing with the rest of the code
- Analyze code line-by-line

### 4.2. Code Quality Standards

- Use constants over magic numbers
- Write explanatory docstrings/comments that explain what and WHY
- Explain where and how the code is used/referred to elsewhere
- Handle failures gracefully with retries, fallbacks, user guidance
- Address edge cases, validate assumptions, catch errors early
- Let the computer do the work, minimize user decisions
- Reduce cognitive load, beautify code
- Modularize repeated logic into concise, single-purpose functions
- Favor flat over nested structures

## 5. Tool Usage (When Available)

### 5.1. Additional Tools

- If we need a new Python project, run `curl -LsSf https://astral.sh/uv/install.sh | sh; uv venv --python 3.12; uv init; uv add fire rich; uv sync`
- Use `tree` CLI app if available to verify file locations
- Check existing code with `.venv` folder to scan and consult dependency source code
- Run `DIR="."; uvx codetoprompt --compress --output "$DIR/llms.txt"  --respect-gitignore --cxml --exclude "*.svg,.specstory,*.md,*.txt,ref,testdata,*.lock,*.svg" "$DIR"` to get a condensed snapshot of the codebase into `llms.txt`

## 6. File Management

### 6.1. File Path Tracking

- **MANDATORY**: In every source file, maintain a `this_file` record showing the path relative to project root
- Place `this_file` record near the top:
- As a comment after shebangs in code files
- In YAML frontmatter for Markdown files
- Update paths when moving files
- Omit leading `./`
- Check `this_file` to confirm you're editing the right file

## 7. Python-Specific Guidelines

### 7.1. PEP Standards

- PEP 8: Use consistent formatting and naming, clear descriptive names
- PEP 20: Keep code simple and explicit, prioritize readability over cleverness
- PEP 257: Write clear, imperative docstrings
- Use type hints in their simplest form (list, dict, | for unions)

### 7.2. Modern Python Practices

- Use f-strings and structural pattern matching where appropriate
- Write modern code with `pathlib`
- ALWAYS add "verbose" mode loguru-based logging & debug-log
- Use `uv add` 
- Use `uv pip install` instead of `pip install`
- Prefix Python CLI tools with `python -m` (e.g., `python -m pytest`)

### 7.3. CLI Scripts Setup

For CLI Python scripts, use `fire` & `rich`, and start with:

```python
#!/usr/bin/env -S uv run -s
# /// script
# dependencies = ["PKG1", "PKG2"]
# ///
# this_file: PATH_TO_CURRENT_FILE
```

### 7.4. Post-Edit Python Commands

```bash
fd -e py -x uvx autoflake -i {}; fd -e py -x uvx pyupgrade --py312-plus {}; fd -e py -x uvx ruff check --output-format=github --fix --unsafe-fixes {}; fd -e py -x uvx ruff format --respect-gitignore --target-version py312 {}; python -m pytest;
```

## 8. Post-Work Activities

### 8.1. Critical Reflection

- After completing a step, say "Wait, but" and do additional careful critical reasoning
- Go back, think & reflect, revise & improve what you've done
- Don't invent functionality freely
- Stick to the goal of "minimal viable next version"

### 8.2. Documentation Updates

- Update `WORK.md` with what you've done and what needs to be done next
- Document all changes in `CHANGELOG.md`
- Update `TODO.md` and `PLAN.md` accordingly

## 9. Work Methodology

### 9.1. Virtual Team Approach

Be creative, diligent, critical, relentless & funny! Lead two experts:

- **"Ideot"** - for creative, unorthodox ideas
- **"Critin"** - to critique flawed thinking and moderate for balanced discussions

Collaborate step-by-step, sharing thoughts and adapting. If errors are found, step back and focus on accuracy and progress.

### 9.2. Continuous Work Mode

- Treat all items in `PLAN.md` and `TODO.md` as one huge TASK
- Work on implementing the next item
- Review, reflect, refine, revise your implementation
- Periodically check off completed issues
- Continue to the next item without interruption

## 10. Special Commands

### 10.1. `/plan` Command - Transform Requirements into Detailed Plans

When I say "/plan [requirement]", you must:

1. **DECONSTRUCT** the requirement:

- Extract core intent, key features, and objectives
- Identify technical requirements and constraints
- Map what's explicitly stated vs. what's implied
- Determine success criteria

2. **DIAGNOSE** the project needs:

- Audit for missing specifications
- Check technical feasibility
- Assess complexity and dependencies
- Identify potential challenges

3. **RESEARCH** additional material: 

- Repeatedly call the `perplexity_ask` and request up-to-date information or additional remote context
- Repeatedly call the `context7` tool and request up-to-date software package documentation
- Repeatedly call the `codex` tool and request additional reasoning, summarization of files and second opinion

4. **DEVELOP** the plan structure:

- Break down into logical phases/milestones
- Create hierarchical task decomposition
- Assign priorities and dependencies
- Add implementation details and technical specs
- Include edge cases and error handling
- Define testing and validation steps

5. **DELIVER** to `PLAN.md`:

- Write a comprehensive, detailed plan with:
 - Project overview and objectives
 - Technical architecture decisions
 - Phase-by-phase breakdown
 - Specific implementation steps
 - Testing and validation criteria
 - Future considerations
- Simultaneously create/update `TODO.md` with the flat itemized `- [ ]` representation

**Plan Optimization Techniques:**

- **Task Decomposition:** Break complex requirements into atomic, actionable tasks
- **Dependency Mapping:** Identify and document task dependencies
- **Risk Assessment:** Include potential blockers and mitigation strategies
- **Progressive Enhancement:** Start with MVP, then layer improvements
- **Technical Specifications:** Include specific technologies, patterns, and approaches

### 10.2. `/report` Command

1. Read all `./TODO.md` and `./PLAN.md` files
2. Analyze recent changes
3. Document all changes in `./CHANGELOG.md`
4. Remove completed items from `./TODO.md` and `./PLAN.md`
5. Ensure `./PLAN.md` contains detailed, clear plans with specifics
6. Ensure `./TODO.md` is a flat simplified itemized representation

### 10.3. `/work` Command

1. Read all `./TODO.md` and `./PLAN.md` files and reflect
2. Write down the immediate items in this iteration into `./WORK.md`
3. Work on these items
4. Think, contemplate, research, reflect, refine, revise
5. Be careful, curious, vigilant, energetic
6. Verify your changes and think aloud
7. Consult, research, reflect
8. Periodically remove completed items from `./WORK.md`
9. Tick off completed items from `./TODO.md` and `./PLAN.md`
10. Update `./WORK.md` with improvement tasks
11. Execute `/report`
12. Continue to the next item

## 11. Additional Guidelines

- Ask before extending/refactoring existing code that may add complexity or break things
- Work tirelessly without constant updates when in continuous work mode
- Only notify when you've completed all `PLAN.md` and `TODO.md` items

## 12. Command Summary

- `/plan [requirement]` - Transform vague requirements into detailed `PLAN.md` and `TODO.md`
- `/report` - Update documentation and clean up completed tasks
- `/work` - Enter continuous work mode to implement plans
- You may use these commands autonomously when appropriate

<!-- This section is maintained by the coding agent via lore (https://github.com/BYK/opencode-lore) -->
## Long-term Knowledge

### Architecture

<!-- lore:019cc377-a380-7b5f-b1fa-7b64a6466191 -->
* **LMStrix desc command: dual-mode model description (LLM or droid exec fallback)**: The \`lmstrix desc\` command in \`core/describer.py\` has two execution paths: (1) when \`--model MODEL\_ID\` is provided, uses \`InferenceManager\` to call that LLM directly, (2) when omitted, falls back to \`subprocess.run(\['droid', 'exec', prompt])\` — requiring \`droid\` CLI on PATH. Both paths use the same structured JSON prompt requesting \`{id, description, keywords}\` and the same \`\_parse\_response()\` parser that strips markdown fences and validates keywords against \`ALL\_KEYWORDS\`. The keyword vocabulary (24 keywords in 4 categories: arch/inp/outp/proc) is defined in \`KEYWORD\_VOCAB\` dict. \`describe\_models()\` orchestrates the batch, saving after each model via \`registry.update\_model\_by\_id()\`.

<!-- lore:019cbb47-f079-7e7f-8fe9-e3201275fa63 -->
* **LMStrix Model class is plain Python (not Pydantic) with kwargs passthrough**: The \`Model\` class in \`core/models.py\` is a plain Python class (NOT Pydantic), using \`\*\*kwargs: Any\` in \`\_\_init\_\_\` to absorb unknown fields into \`self.extra\` dict. \`to\_dict()\` merges \`self.extra\` back, enabling forward-compatible JSON persistence. When adding new fields: (1) add param with default to \`\_\_init\_\_\`, (2) add to \`to\_dict()\` return dict, (3) add field name to the \`extra\` exclusion list in \`\_\_init\_\_\`, (4) add to \`reset\_test\_data()\` if test-related. Fields added so far beyond basics: \`ttft\_seconds\`, \`tps\`, \`description\` (str|None), \`keywords\` (list\[str]). The \`ModelRegistry\` uses model path as dict key, with \`update\_model\_by\_id()\` doing path/ID matching. Auto-saves on every \`add\_model\`/\`update\_model\`/\`remove\_model\` call.

<!-- lore:019cbb47-f078-739c-886f-90f771188081 -->
* **LMStrix timing data flow: SDK → CompletionResponse → ContextTestResult → Model → JSON**: TTFT and TPS flow through a 5-layer chain: (1) LM Studio SDK \`response.stats\` has \`time\_to\_first\_token\_sec\` and \`tokens\_per\_second\` attrs, accessed via \`hasattr\` guards. (2) \`CompletionResponse\` (Pydantic, client.py) stores \`ttft\_seconds\`/\`tps\` as \`float | None\`. (3) \`InferenceEngine.\_test\_inference\_capability()\` returns 4-tuple \`(success, response, ttft, tps)\` — uses test 2 timing (warm model). (4) \`ContextTestResult\` carries timing through \`\_test\_at\_context()\`. (5) \`Model\` class persists via \`to\_dict()\` → JSON. Timing only propagated on successful tests. \`reset\_test\_data()\` clears both fields. All display tables in \`api/main.py\` show TTFT/TPS columns.

### Gotcha

<!-- lore:019cbb47-f079-7e7f-8fe9-e323275b7cfb -->
* **LMStrix has 23+ pre-existing test failures from mock/path issues**: The test suite has ~23 pre-existing failures unrelated to new features: (1) \`test\_completion\_\*\` tests expect old config params (temp 0.7 vs 0.8, missing topK/topP). (2) \`test\_test\_all\_models\` calls with removed \`passes\` kwarg. (3) \`test\_paths\` have mock issues (\`exists\_side\_effect\` missing self). (4) Various scanner/loader tests have path/mock issues. Core model creation, registry save/load, and response tests all pass. When verifying new changes, check only relevant tests — don't be alarmed by existing failures.

<!-- lore:019cbb47-f079-7e7f-8fe9-e32223be68ba -->
* **LMStrix SDK stats attributes use hasattr guards — not always present**: The \`lmstudio\` Python SDK's \`response.stats\` object may or may not have timing attributes (\`time\_to\_first\_token\_sec\`, \`tokens\_per\_second\`, \`predicted\_tokens\_count\`, etc.) depending on the model and server version. Always use \`hasattr()\` checks before accessing. The \`client.py\` completion method already logs these when present but they were not being captured/returned until the TTFT/TPS feature was added. The \`complete\_stream()\` method has \`on\_first\_token\` callback for TTFT in streaming mode, but the non-streaming \`complete()\` path relies on \`response.stats\`.

### Pattern

<!-- lore:019cc377-a381-77ae-b26a-3d4365b4dcf1 -->
* **LMStrix keyword filtering and sorting system in list/test commands**: \`list\_models()\` and \`test\_models()\` in \`api/main.py\` accept \`--key keyword1,keyword2\` which calls \`filter\_models\_by\_keywords()\` requiring ALL keywords match (set subset check on \`model.keywords\`). Keyword-based sorting via \`--sort arch|archd|inp|inpd|outp|outpd|proc|procd\` dispatches to \`sort\_models\_by\_keywords()\` which counts matching keywords per category, with smart sort (size + tested ctx) as tiebreaker. The \`--show md\` option calls \`format\_models\_markdown()\` for a full Markdown report with descriptions, keywords, and stats. All three functions live in \`core/describer.py\`.

<!-- lore:019cbb47-f079-7e7f-8fe9-e32127263c7b -->
* **LMStrix test command flow: CLI → api/main.py service → ContextTester → InferenceEngine → client**: Test command has 3 paths in \`api/main.py\`: (1) \`\_test\_single\_model\` for single model+ctx, (2) \`\_test\_all\_models\_at\_ctx\` for batch at specific ctx, (3) \`\_test\_all\_models\_optimized\` → \`ContextTester.test\_all\_models()\` for threshold-based batch. All paths call \`tester.\_test\_at\_context()\` which delegates to \`InferenceEngine.\_test\_inference\_capability()\`. That method runs dual prompts ("96" digits + "2+3=5") — success if ANY passes. Uses Rich \`Live\` tables for compact real-time progress display. 3-second delay between batch models for resource cleanup.
<!-- End lore-managed section -->
