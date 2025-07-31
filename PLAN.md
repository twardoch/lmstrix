# LMStrix Current Development Plan


## Current Status
### Problem Description
When running inference with `--verbose`, loguru was outputting the prompt and model response through its handlers, causing:
1. **Logging errors**: KeyError and ValueError exceptions in loguru handlers
2. **Output pollution**: Model responses were mixed with loguru formatting
3. **User requirement violation**: User explicitly stated to NEVER pass prompt or model output through loguru

### Root Cause
- In `api/client.py`, the prompt and model response were being logged via loguru
- Loguru was trying to format the output, causing issues with special characters like `</translation-instructions>`
- This violated the requirement to use `sys.stderr` for prompts and `sys.stdout` for model output


## CRITICAL: Issue #302 - Inference Output Mismatch

### Problem Description
When running the same translation prompt through LM Studio GUI vs lmstrix CLI, we get drastically different results:
- **LM Studio GUI**: Produces proper Polish translation (639 tokens)
- **lmstrix CLI**: Only outputs `</translate>` (4 tokens)

### Root Cause Analysis

#### Configuration Differences Found
1. **Temperature**: GUI uses 0.8, CLI uses 0.7
2. **top_k**: GUI uses 20, CLI uses 40  
3. **Context Length**: GUI uses full 131072, CLI uses 65536 (reduced)
4. **max_predict**: GUI uses -1 (unlimited), CLI calculates 117964
5. **Sampling Parameters**: Multiple differences in repeat_penalty, min_p, etc.

#### Potential Issues
1. **Early Stop Token**: Model might be hitting a stop token immediately
2. **Prompt Format**: The prompt might be wrapped or modified differently
3. **Chat Template**: Possible incorrect chat template application
4. **Parameter Mismatch**: Inference parameters not matching LM Studio defaults

## Immediate Priorities

### 1. Fix Issue #302 - Inference Output Mismatch
**Priority: CRITICAL - NOW TOP PRIORITY**
- This is blocking proper inference functionality
- Users cannot get correct model outputs
- Model only outputs `</translation>` instead of full translation

#### Implementation Steps:

##### Step 1: Add Diagnostic Logging
- Log the exact prompt being sent (with escape sequences visible)
- Log all inference parameters in detail
- Log stop tokens being used
- Add comparison with LM Studio expected values

##### Step 2: Parameter Alignment
- Change default temperature from 0.7 to 0.8
- Add CLI parameters for all inference settings
- Remove or make optional the maxTokens calculation

##### Step 3: Context Length Fix
- Fix context reduction from 131072 to 65536
- Use full model context unless explicitly limited
- Add warning when context is reduced

##### Step 4: Stop Token Investigation  
- Check why model stops at `</translate>`
- Verify stop token configuration
- Test with stop tokens disabled

### 2. Issue #105 - Adam.toml Simplification
**Priority: High** (after Issue #302)
- Simplify adam.toml structure to use flat format instead of nested groups
- Add --text and --text_file parameters to infer command for direct text input
- Update all prompt examples to use simplified approach
- Ensure backward compatibility with existing TOML files

## NEW FEATURES: Issues #306 & #307 - Streaming & Batch Processing

### Issue #307: Streaming Inference Support
**Priority: HIGH** - Modern inference capability

#### Problem Statement
Current lmstrix only supports synchronous inference via `llm.complete()`, which:
- Blocks until entire response is complete
- Provides no real-time feedback during generation
- Cannot handle interrupted inference gracefully
- Missing modern streaming UX that users expect

#### Technical Requirements
1. **Async Streaming API**: Integrate lmstudio SDK's `complete_stream()` capability
2. **Backward Compatibility**: Maintain existing sync API while adding streaming
3. **CLI Integration**: Add `--stream` flag to inference commands
4. **Error Handling**: Robust streaming error recovery and cancellation
5. **Performance**: Efficient token-by-token processing without blocking

#### Implementation Architecture

##### Core Components:
1. **StreamingInferenceManager** - Async counterpart to InferenceManager
2. **LMStudioClient.stream_completion()** - Async streaming method  
3. **CLI streaming support** - `--stream` flag with real-time output
4. **Error resilience** - Handle network interruptions, model failures
5. **Token callbacks** - Extensible handler system for streaming tokens

##### API Design:
```python
# Async streaming interface
async def stream_infer(
    model_id: str, 
    prompt: str,
    on_token: Callable[[str], None] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """Stream inference tokens as they arrive"""
    
# CLI usage
lmstrix infer translate --stream -m model-id --text "Hello world"
```

### Issue #306: Batch Processing Tool (adamall.py)
**Priority: HIGH** - Essential automation tool

#### Problem Statement
Users need to efficiently run multiple prompts across multiple models:
- Manual inference is time-consuming and error-prone
- Need to process 6 specific prompts against all available models
- Must avoid unnecessary model loading/unloading
- Require robust error handling and progress tracking
- Output organization for downstream processing

#### Technical Requirements
1. **Smart Model Management**: Load models only when needed, reuse when possible
2. **Prompt Processing**: Handle multiple prompts from adam.toml efficiently
3. **File Organization**: Safe output naming with pathvalidate sanitization
4. **Skip Existing**: Don't regenerate outputs that already exist
5. **Error Recovery**: Capture errors in output files, continue processing
6. **Progress Tracking**: Clear feedback on processing status

#### Implementation Architecture

##### Core Components:
1. **BatchProcessor** - Main orchestration class
2. **ModelManager** - Efficient model loading/unloading
3. **PromptRunner** - Individual prompt execution with error handling
4. **OutputManager** - File naming, existence checking, error capture
5. **ProgressTracker** - Status reporting and logging

##### Workflow Design:
```python
# Processing strategy
1. Load all models from registry, sort by "smart" method
2. Load all required prompts from adam.toml  
3. Build execution matrix (model × prompt combinations)
4. Filter out existing outputs to skip redundant work
5. Group by model to minimize loading operations
6. Execute with comprehensive error handling
7. Progress reporting throughout
```

##### Target Prompts:
- `think,aps`
- `think,humanize` 
- `think,tldr`
- `think,tts_optimize`
- `translate`
- `tldr`

#### File Management Strategy:
- **Input**: `_keep_this/adam/fontlab8.md`
- **Output Pattern**: `_keep_this/adam/out/{safe_prompt_name}--{safe_model_id}.txt`
- **Safety**: Use pathvalidate for filename sanitization
- **Existence Check**: Skip files that already exist
- **Error Capture**: Write error messages to output files on failure

## Detailed Technical Implementation

### Issue #307: Streaming Implementation Breakdown

#### Phase 1: Core Infrastructure (Day 1-2)
1. **LMStudioClient Async Methods**:
   ```python
   async def stream_completion(
       self, llm, prompt: str, 
       on_token: Callable[[str], None] = None,
       **kwargs
   ) -> AsyncGenerator[str, None]:
       """Stream tokens from lmstudio SDK async API"""
   ```

2. **StreamingInferenceManager Class**:
   ```python
   class StreamingInferenceManager:
       async def stream_infer(self, model_id: str, prompt: str, **kwargs):
           """Async streaming counterpart to InferenceManager.infer()"""
   ```

3. **Integration Points**:
   - Extend existing InferenceManager with async methods
   - Maintain backward compatibility with sync interface
   - Use asyncio for event loop management

#### Phase 2: CLI Integration (Day 2-3)
1. **Command Line Interface**:
   - Add `--stream` flag to `lmstrix infer` command
   - Real-time token display to stdout
   - Handle Ctrl+C gracefully for cancellation

2. **Error Handling**:
   - Network interruption recovery
   - Model loading failures during streaming
   - Graceful degradation to sync mode if streaming fails

#### Phase 3: Testing & Polish (Day 3-5)
1. **Unit Tests**: Async streaming functionality
2. **Integration Tests**: CLI streaming with real models
3. **Performance Tests**: Compare streaming vs sync performance
4. **Documentation**: Usage examples and API documentation

### Issue #306: Batch Tool Implementation Breakdown

#### Phase 1: Core Architecture (Day 1-2)
1. **BatchProcessor Class**:
   ```python
   class BatchProcessor:
       def __init__(self, adam_toml_path, fontlab_md_path, output_dir):
           self.models = self.load_and_sort_models()
           self.prompts = self.load_prompts()
           self.matrix = self.build_execution_matrix()
   ```

2. **Smart Model Management**:
   ```python
   class ModelManager:
       def __init__(self, inference_manager):
           self.current_model = None
           self.inference_manager = inference_manager
           
       async def ensure_model_loaded(self, model_id: str, context_size: int):
           """Load model only if not already loaded"""
   ```

3. **Output Management**:
   ```python
   class OutputManager:
       def __init__(self, output_dir: Path):
           self.output_dir = output_dir
           
       def get_output_path(self, prompt_name: str, model_id: str) -> Path:
           """Generate safe output path using pathvalidate"""
           
       def should_skip(self, output_path: Path) -> bool:
           """Check if output already exists"""
   ```

#### Phase 2: Execution Engine (Day 2-3)
1. **Execution Matrix**:
   - Build combinations of models × prompts
   - Filter existing outputs to avoid redundant work
   - Group by model to minimize loading overhead

2. **Progress Tracking**:
   ```python
   class ProgressTracker:
       def __init__(self, total_tasks: int):
           self.completed = 0
           self.total = total_tasks
           self.start_time = time.time()
           
       def update(self, prompt_name: str, model_id: str, status: str):
           """Update progress and display to user"""
   ```

3. **Error Resilience**:
   - Wrap each inference in try/except
   - Write error messages to output files
   - Continue processing despite individual failures
   - Log all errors for debugging

#### Phase 3: Integration & Testing (Day 3-4)
1. **CLI Tool Creation**: `_keep_this/adam/adamall.py`
2. **Integration**: Use existing lmstrix components
3. **Memory Management**: [[memory:4463738]] Unload models between tests
4. **Context Management**: [[memory:4875704]] Use ctx_out from registry
5. **Testing**: End-to-end validation with real models and prompts

#### Target Integration Points:
- **Model Registry**: `src/lmstrix/core/models.py` for model listing and smart sorting
- **Prompt Loader**: `src/lmstrix/loaders/prompt_loader.py` for adam.toml processing  
- **Inference Manager**: `src/lmstrix/core/inference_manager.py` for actual inference
- **Logging**: `src/lmstrix/utils/logging.py` for consistent logging

#### Execution Strategy:
```python
# Pseudo-code for batch execution
for model in sorted_models:
    for prompt_name in target_prompts:
        output_path = get_safe_output_path(prompt_name, model.id)
        if output_path.exists():
            continue  # Skip existing
            
        try:
            ensure_model_loaded(model.id, context_size=int(model.context_limit * 0.5))
            resolved_prompt = load_prompt(prompt_name, text=fontlab8_content)
            result = inference_manager.infer(
                model_id=model.id,
                prompt=resolved_prompt.resolved,
                out_ctx=int(model.context_out * 0.9)  # Use 90% of max context
            )
            write_output(output_path, result.response)
        except Exception as e:
            write_error(output_path, str(e))
        finally:
            progress_tracker.update(prompt_name, model.id, "completed")
```

## Implementation Order

1. **Issue #302 - Inference Fix** (NOW TOP PRIORITY):
   - Align parameters with LM Studio
   - Fix context length handling
   - Investigate stop token issue

### Phase 1: New Features Implementation (After Issue #302)
1. **Issue #307 - Streaming Inference** (3-5 days):
   - Implement async streaming infrastructure
   - Add CLI streaming support
   - Comprehensive testing
   
2. **Issue #306 - Batch Processing Tool** (3-4 days):
   - Build adamall.py with smart model management
   - Integrate with existing prompt/model systems
   - Output management and error handling

### Phase 2: Normal Development (After new features)
- Continue with Issue #105 and other planned improvements

## Key Design Decisions & Risk Mitigation

### Issue #307: Streaming Implementation Decisions
1. **Async-First Approach**: Use Python asyncio for true non-blocking streaming
2. **Backward Compatibility**: Keep existing sync API unchanged, add streaming as enhancement
3. **Error Resilience**: Graceful fallback to sync mode if streaming fails
4. **Memory Management**: Stream tokens without buffering entire response
5. **CLI Integration**: Simple `--stream` flag, no breaking changes to existing commands

### Issue #306: Batch Tool Design Decisions  
1. **Smart Model Loading**: Minimize model loading overhead by grouping operations by model
2. **Idempotent Execution**: Skip existing outputs to support resumable batch processing
3. **Error Isolation**: Individual task failures don't stop entire batch
4. **Memory Safety**: [[memory:4463738]] Always unload models between major operations
5. **Context Optimization**: [[memory:4875704]] Use model-specific ctx_out values for optimal performance
6. **File Safety**: Use pathvalidate for cross-platform filename sanitization

### Risk Assessment & Mitigation
1. **Memory Pressure**: Batch tool could exhaust system memory
   - *Mitigation*: Explicit model unloading, memory monitoring
2. **Long Processing Times**: Large batch jobs could take hours
   - *Mitigation*: Progress tracking, resumable execution, early skip existing
3. **Network Failures**: Streaming could be interrupted
   - *Mitigation*: Graceful degradation, retry logic, fallback to sync
4. **File System Issues**: Output file conflicts or permission errors
   - *Mitigation*: Safe filename generation, directory creation, error capture

### Performance Considerations
1. **Streaming**: Real-time token display vs sync waiting
2. **Batch Processing**: Model reuse vs loading overhead
3. **Memory Usage**: Stream buffering vs batch model loading
4. **I/O Efficiency**: File existence checking vs redundant processing

## Future Development Phases

### Phase A: Core Simplification (2-3 weeks)
1. **Configuration Unification**
   - Create utils/config.py for centralized configuration handling
   - Consolidate path handling functions
   - Remove redundant configuration code

2. **Error Handling Standardization**
   - Review and simplify custom exception hierarchy
   - Standardize error messages across codebase
   - Implement consistent logging patterns

### Phase B: CLI Enhancement (1-2 weeks)
1. **Command Improvements**
   - Enhance `scan` command with better progress reporting
   - Improve `list` command with filtering and sorting options
   - Add `reset` command for clearing model test data

2. **User Experience**
   - Better error messages with helpful suggestions
   - Improved help text and documentation
   - Enhanced progress indicators for long-running operations

### Phase C: Testing & Documentation (1 week)
1. **Test Suite Completion**
   - Ensure >90% test coverage maintained
   - Add integration tests for new features
   - Performance benchmarking of improvements

2. **Documentation Updates**
   - Update README.md with latest features
   - Create comprehensive CLI reference
   - Update examples to demonstrate new capabilities

## Success Metrics

- **Functionality**: All existing CLI commands work without regression
- **Performance**: Model loading and inference speed improvements
- **Usability**: Cleaner, more informative user interface
- **Maintainability**: Reduced complexity, better code organization
- **Documentation**: Up-to-date and comprehensive user guides

## NEW DEVELOPMENT PRIORITIES

### Issue #307 - Implement LM Studio Streaming Inference
**Priority: High** (Modern SDK capability)

#### Problem Analysis
- Current lmstrix uses synchronous `llm.complete()` which blocks until full response
- LM Studio SDK 1.4+ supports `llm.complete_stream()` with real-time token streaming
- Streaming enables: real-time progress feedback, automatic hang detection, better UX

#### Implementation Strategy

##### Phase 1: Core Streaming Migration
- Replace `llm.complete()` with `llm.complete_stream()` in `LMStudioClient.completion()`
- Implement progress callbacks: `on_prediction_fragment`, `on_first_token`
- Add no-progress timeout watchdog to abort stalled generations
- Maintain backward compatibility with existing response format

##### Phase 2: CLI Enhancement
- Add `--stream-timeout` flag (default 120s) for hang detection
- Add `--show-progress` flag for real-time token display
- Update inference logging to show streaming status

##### Phase 3: Advanced Features
- Implement token-by-token display in verbose mode
- Add streaming statistics (tokens/second, time to first token)
- Enable streaming cancellation via Ctrl+C

### Issue #306 - Batch Inference Tool (adamall.py)
**Priority: Medium** (User productivity tool)

#### Requirements Analysis
- Batch process multiple models × multiple prompts
- Smart model loading/unloading to minimize operations
- Output management with safe filename generation
- Error handling and recovery

#### Implementation Strategy

##### Phase 1: Core Infrastructure
- Create `_keep_this/adam/adamall.py` using lmstrix API
- Implement smart model state detection and caching
- Add pathvalidate-based safe filename generation
- Configure batch prompts: `think,aps`, `think,humanize`, `think,tldr`, `think,tts_optimize`, `translate`, `tldr`

##### Phase 2: Output Management
- Implement file existence checking to skip completed inference
- Generate output paths: `f"_keep_this/adam/out/{safe_prompt_name}--{safe_model_id}.txt"`
- Add error message capture to output files on failure

##### Phase 3: Performance Optimization
- Sort models by "smart" method (as in `lmstrix list`)
- Load models with 50% input context, inference with 90% max context
- Minimize model loading/unloading through intelligent scheduling

## Long-term Vision

The goal is to make LMStrix the most user-friendly and efficient tool for managing and testing LM Studio models, with:
- Real-time streaming inference with progress feedback and hang detection
- Intuitive CLI interface with beautiful, informative output
- Smart model management with automatic optimization
- Batch processing capabilities for productivity workflows
- Comprehensive testing capabilities with clear results
- Excellent developer experience with clean, well-documented code