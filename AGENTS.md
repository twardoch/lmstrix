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
