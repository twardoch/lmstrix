---
title: How It Works
---

## How It Works: The Adaptive Context Optimizer

The core innovation in LMStrix is its ability to **automatically discover the maximum operational context length** for any model loaded in LM Studio.

It uses a sophisticated **binary search algorithm**:
1.  It starts with a wide range for the possible context size.
2.  It sends a specially crafted prompt to the model, progressively increasing the amount of "filler" text.
3.  It analyzes the model's response (or lack thereof) to see if it successfully processed the context.
4.  By repeatedly narrowing the search range, it quickly pinpoints the precise token count where the model's performance degrades or fails.

This gives you a reliable, empirical measurement of the model's true capabilities on your specific hardware, eliminating guesswork and ensuring your applications run with optimal performance.

### The `test` Command

The `test` command is the heart of the context optimization process. When you run `lmstrix test <model-id>`, it performs the binary search algorithm described above.

The command saves the results of the test to a local registry, so you only need to test each model once.
