# LMStrix Development Plan - v1.0 MVP

## Project Vision

LMStrix v1.0 will be a minimal viable product focused on solving the critical problem with LM Studio: many models falsely declare higher maximum context lengths than they can actually handle. The tool will provide automated discovery of true operational context limits and maintain a reliable model registry.

## Core Problem Statement

LM Studio models often declare context limits (e.g., 128k tokens) that fail in practice:
1. Models may fail to load at declared context length
2. Models may load but produce gibberish output
3. Only below a certain "real" max context do models produce correct output

## Technical Approach

Use the native `lmstudio` Python package for all model operations:
- Model discovery: `lmstudio.list_downloaded_models()`
- Model loading: `lmstudio.llm(model_id, config={"contextLength": size})`
- Model info: `model.get_info()`
- Inference: `model.complete(prompt)`
- Unloading: `model.unload()`

This avoids the limitations and issues with `litellm` and provides direct integration with LM Studio.

## Current Implementation Status

### Completed Components
1. **Project Structure** ✓
   - Modern Python package with `src/` layout
   - Modular architecture: api/, core/, cli/, loaders/, utils/
   - Comprehensive pyproject.toml configuration

2. **Core Models & Registry** ✓
   - `Model` class with context testing fields
   - `ModelRegistry` with save/load functionality
   - `ModelScanner` for automatic discovery
   - `ContextTestStatus` enum for tracking

3. **Context Testing Framework** ✓
   - `ContextTester` class with binary search algorithm
   - `ContextTestResult` for logging attempts
   - Per-model logging system
   - Test status tracking and resumption

4. **CLI Interface** ✓
   - `lmstrix scan` - Discover models
   - `lmstrix list` - Show models with test status
   - `lmstrix test <model>` - Test specific model
   - `lmstrix test --all` - Batch testing
   - `lmstrix status` - Testing progress
   - Rich formatting with progress bars

5. **Utilities** ✓
   - Path detection for LM Studio directory
   - Data storage in proper system locations
   - Backward compatibility with lmsm.json

### Pending Critical Changes

**PRIORITY: Replace litellm with native lmstudio package**
- Current implementation uses litellm (inadequate for our needs)
- Must rewrite LMStudioClient to use native lmstudio APIs
- Update ContextTester to properly load/unload models
- Ensure real model metadata extraction

## Phase 1: Core Functionality Completion

### 1.1 LM Studio Native Integration (IMMEDIATE PRIORITY)
**Goal**: Replace litellm with native lmstudio package

**Tasks**:
1. Remove litellm dependency from pyproject.toml
2. Rewrite `LMStudioClient` class:
   ```python
   class LMStudioClient:
       async def load_model(self, model_id: str, context_length: int):
           return lmstudio.llm(model_id, config={"contextLength": context_length})
       
       async def complete(self, model, prompt: str):
           return await model.complete(prompt)
       
       async def unload_model(self, model):
           model.unload()
   ```

3. Update `ContextTester._test_at_context()`:
   - Use actual model loading instead of simulation
   - Properly handle load failures
   - Test with real completions
   - Unload models after each test

4. Update `ModelScanner`:
   - Use `lmstudio.list_downloaded_models()`
   - Extract real metadata with `model.get_info()`

### 1.2 Context Validation System Enhancement
**Goal**: Implement real context testing with proper model operations

**Implementation**:
```python
async def test_context_limits(model_id, min_ctx=32, max_ctx=None):
    # 1. Binary search for loadable context
    loadable_ctx = await find_max_loadable(model_id, min_ctx, max_ctx)
    
    # 2. Binary search for working context
    working_ctx = await find_max_working(model_id, min_ctx, loadable_ctx)
    
    # 3. Log all attempts with results
    # 4. Update registry with tested limits
    
async def find_max_loadable(model_id, min_ctx, max_ctx):
    # Binary search with actual model loading
    while left <= right:
        mid = (left + right) // 2
        try:
            model = lmstudio.llm(model_id, config={"contextLength": mid})
            model.unload()
            best = mid
            left = mid + 1
        except:
            right = mid - 1
    return best
    
async def find_max_working(model_id, min_ctx, max_ctx):
    # Binary search with inference testing
    while left <= right:
        mid = (left + right) // 2
        try:
            model = lmstudio.llm(model_id, config={"contextLength": mid})
            response = await model.complete("2+2=")
            model.unload()
            if response.strip() == "4":
                best = mid
                left = mid + 1
            else:
                right = mid - 1
        except:
            right = mid - 1
    return best
```

### 1.3 Data Storage & Registry
**Goal**: Proper system-aware data storage

**Implementation**:
- Model registry: `{lm_studio_path}/lmstrix/models.json`
- Context test logs: `{lm_studio_path}/lmstrix/context_tests/{model_id}_context_test.log`
- Maintain backward compatibility with existing `lmsm.json`
- Never store data in package directory

### 1.4 Python API Completion
**Goal**: Complete the high-level API

**Implementation**:
```python
class LMStrix:
    async def test_context_limits(self, model_id: str, min_context: int = 32):
        """Test and return real context limits for a model."""
        tester = ContextTester(self.client)
        model = self.registry.get_model(model_id)
        if not model:
            raise ModelNotFoundError(model_id)
        
        updated_model = await tester.test_model(model, min_context)
        self.registry.update_model(model_id, updated_model)
        
        return {
            "declared": model.context_limit,
            "loadable": updated_model.loadable_max_context,
            "working": updated_model.tested_max_context,
            "reduction": (1 - updated_model.tested_max_context / model.context_limit) * 100
        }
    
    def get_tested_context_limit(self, model_id: str) -> Optional[int]:
        """Get the tested working context limit for a model."""
        model = self.registry.get_model(model_id)
        return model.tested_max_context if model else None
```

## Phase 2: Testing & Quality Assurance

### 2.1 Unit Tests
**Goal**: Test core functionality

**Priority Tests**:
- Path detection and directory creation
- Model discovery and registry operations
- Context binary search algorithm
- Log file writing and parsing
- CLI command parsing

### 2.2 Integration Tests
**Goal**: Test with real LM Studio

**Tests**:
- Real model loading/unloading
- Actual inference with context sizes
- Interrupted test resumption
- Batch testing operations

## Phase 3: Documentation & Release

### 3.1 Essential Documentation
**Goal**: Clear usage instructions

**Deliverables**:
- Updated README.md with real examples
- Context testing methodology explanation
- Troubleshooting guide for common issues
- API reference with code examples

### 3.2 Package Release
**Goal**: v1.0.0 on PyPI

**Steps**:
1. Remove litellm, ensure lmstudio dependency
2. Test with real LM Studio instance
3. Update version to 1.0.0
4. Build and test distribution
5. Publish to PyPI

## Success Criteria for v1.0

1. **Functional**:
   - Uses native lmstudio package for all operations
   - Accurately discovers real context limits
   - Properly loads/unloads models
   - Saves results in system-appropriate location

2. **Reliable**:
   - Handles model loading failures gracefully
   - Resumes interrupted tests
   - Provides clear error messages
   - Doesn't leave models loaded in memory

3. **Usable**:
   - Simple CLI commands work reliably
   - Progress indication during long tests
   - Clear reporting of context limit issues
   - Helpful documentation

## Out of Scope for v1.0

- Advanced optimization algorithms beyond binary search
- Streaming support
- Multi-model parallel testing
- Web interface
- Plugin system
- Docker/Kubernetes support

## Implementation Notes

### Critical Path for MVP
1. Replace litellm with lmstudio package (BLOCKER)
2. Implement real model loading/unloading
3. Complete context testing with actual inference
4. Ensure proper data persistence
5. Test with real LM Studio instance
6. Package and release

### Error Handling
- Graceful handling of model load failures
- Clear error messages for connection issues
- Automatic retry with exponential backoff
- Save partial results on interruption
- Proper cleanup (unload models) on errors

### Performance Considerations
- Unload models immediately after testing to free VRAM
- Cache results to avoid retesting
- Binary search minimizes test attempts
- Progress indication for user feedback