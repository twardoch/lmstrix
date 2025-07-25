---
title: How It Works
---

## How It Works: The Adaptive Context Optimizer

The core innovation in LMStrix is its ability to **automatically discover the maximum operational context length** for any model loaded in LM Studio.

It uses a sophisticated **adaptive testing algorithm** (enhanced in v1.1):

1. **Initial Verification**: Tests at 1,024 tokens to ensure the model loads properly
2. **Threshold Test**: Tests at min(threshold, declared_max) where threshold defaults to 102,400 tokens
   - This prevents system crashes from attempting very large context sizes
3. **Adaptive Search**:
   - If the threshold test succeeds and is below the declared max: incrementally increases by 10,240 tokens until failure
   - If the threshold test fails: performs binary search between 1,024 and the failed size
4. **Progress Tracking**: Saves results after each test, allowing resumption if interrupted

**Batch Testing Optimization** (new in v1.1):
When testing multiple models with `--all`, LMStrix now:
- Sorts models by declared context size (ascending)
- Tests in passes to minimize model loading/unloading
- Excludes failed models from subsequent passes
- Provides detailed progress with Rich table output

This gives you a reliable, empirical measurement of the model's true capabilities on your specific hardware, eliminating guesswork and ensuring your applications run with optimal performance.

### The `test` Command

The `test` command is the heart of the context optimization process. When you run `lmstrix test <model-id>`, it performs the binary search algorithm described above.

The command saves the results of the test to a local registry, so you only need to test each model once.
