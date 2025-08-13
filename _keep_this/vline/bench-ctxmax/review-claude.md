# LLM Marketing Email Benchmark Review

## Introduction

This comprehensive review analyzes the performance of 68 local language models on a marketing email generation task for Vexy Lines 1.0, a fictional vector graphics software. The models were tested on their ability to craft compelling marketing content based on a detailed 4000-token FAQ document. The results varied dramatically in both execution time (ranging from 7.8 seconds to over 35 minutes) and output quality (from complete failures to surprisingly creative marketing copy).

The task required models to synthesize technical product information into an emotive marketing email - a challenging blend of comprehension, creativity, and persuasive writing. What emerged was a fascinating spectrum of AI capabilities, from models that produced single nonsensical tokens to those that crafted professional-grade marketing materials complete with calls-to-action and strategic messaging.

## bling-qwen-mini-tool (7.84s) ⭐

This model wins the speed contest but delivers what amounts to a tweet rather than an email. With just 198 characters of output, it managed to compress the entire marketing message into "Try it free now!" - technically correct but hilariously insufficient. It's like asking for a gourmet meal and getting a fortune cookie. Still, points for efficiency!

## llama3.2-entity-1b (23.74s) ⭐⭐

This tiny 1B model surprised with meta-commentary about email writing rather than actually writing the email. It spent more time explaining how to write marketing emails than doing it, like a cooking show that never actually cooks anything. The example email it eventually provided was generic but at least coherent - a solid effort for such a small model running in under 30 seconds.

## llama3.2-entity (32.73s) ⭐⭐⭐

The 3B entity model showed marked improvement over its 1B sibling, delivering an actual marketing email with proper structure and relevant features. While it got a bit carried away with exclamation marks and hyperbole ("blow minds and printers' files!"), it demonstrated good comprehension of the product features and managed to create genuine enthusiasm. Impressive for a 32-second turnaround.

## slim-xsum-tool (37.49s) ⭐

This model apparently took "summarization" too literally and returned just "<classify> description </classify>" - a spectacular misunderstanding of the assignment. It's like showing up to a marathon wearing a tuxedo. Fast execution, zero comprehension.

## slim-sa-ner-tool (37.80s) ⭐

Another slim model that completely missed the point, returning only "{'sentiment': ['positive']}" - technically correct sentiment analysis but utterly useless for the task. It's the AI equivalent of answering "How was your day?" with "Noun."

## slim-extract-tool (39.58s) ⭐

Continuing the slim model tradition of spectacular failure, this one extracted exactly one piece of information: "{'VEXY_LINES_VERSION': ['Version 1.0']}". It understood extraction but forgot about the "marketing email" part entirely.

## slim-summary-tool (41.62s) ⭐⭐

At least this slim model tried to summarize something relevant, producing a one-sentence description of Vexy Lines. Still nowhere near a marketing email, but it showed basic comprehension of the source material, which is more than its slim siblings managed.

## mistral-7b-sarcasm-scrolls-v2 (41.95s) ⭐

"We'll send it out as a newsletter for you." That's it. That's the entire output. This model took sarcasm to a new level by essentially saying "yeah, whatever, we'll handle it" - peak passive-aggressive AI behavior.

## dragon-mistral-7b-v0 (42.14s) ⭐

Simply returned "Not Found." - the digital equivalent of a shrug. At least it was honest about its complete failure to engage with the task.

## slim-tags-3b-tool (42.87s) ⭐

Another extraction-focused model that pulled out file formats and software names but created no marketing content whatsoever. It's like being asked to write a love letter and responding with a list of paper types.

## kmdb-keyword-extraction (44.23s) ⭐

Hilariously, this keyword extraction model pivoted to newsletter signup spam: "Subscribe to our newsletter for updates and exclusive deals! 10% off your next purchase when you sign up today". Generic, unrelated to Vexy Lines, but at least it understood "marketing".

## mistralai_voxtral-mini-3b-2507 (48.41s) ⭐⭐⭐⭐

Finally, a model that delivered! In under a minute, this 3B model produced a fun, emoji-filled, casual marketing email that actually understood the product. The tone was perfect for social media marketing, with good feature highlights and appropriate enthusiasm. Proof that model size isn't everything.

## granite-4.0-tiny-preview (63.84s) ⭐⭐⭐⭐⭐

Despite being labeled "tiny", this model produced one of the most comprehensive and professional marketing emails in the entire test. Well-structured with clear sections, compelling copy, and proper CTAs. The 64-second execution time delivered exceptional value - this is how you punch above your weight class!

## llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b (64.25s) ⭐⭐⭐⭐

This model with the unnecessarily dramatic name delivered a clean, professional email with good structure and a 14-day trial offer. The "dark champion" branding didn't result in any edgy content - just solid marketing copy in about a minute.

## llama-3.2-4x3b-moe-hell-california-uncensored-10b (67.98s) ⭐⭐⭐⭐

Another dramatically named model that delivered professional results. Clear benefit-focused messaging, good understanding of the product, and appropriate tone. The "hell california uncensored" naming seems purely for shock value as the output was entirely wholesome.

## mistral-7b-pii-entity-extractor (86.20s) ⭐⭐⭐

This PII extractor pivoted successfully to marketing, producing a decent email with clear structure and appropriate business tone. Not the most creative, but solid and professional for 86 seconds of processing.

## slim-extract-qwen-0.5b (92.45s) ⭐

Absolute disaster. This model had a complete meltdown, producing nothing but exclamation marks and incrementing version numbers. It's like watching an AI have a stroke in real-time. The 92-second execution time was spent generating pure gibberish.

## llama-3-soliloquy-8b-v1.5-64k-i (97.29s) ⭐⭐⭐

Produced a somewhat generic but competent marketing email with decent structure. The "soliloquy" name is apt - it sounds like it's talking to itself about features rather than engaging with customers, but the output was serviceable.

## meta-llama-3.1-8b-instruct-summarizer (98.96s) ⭐⭐⭐⭐

Well-formatted email with good structure, clear CTAs, and professional tone. The summarizer background helped it distill key features effectively. Nearly 100 seconds well spent.

## llama-3.1-8b-sarcasm (113.26s) ⭐⭐⭐⭐

Surprisingly unsarcastic! Delivered a comprehensive email with bonus section on improvement ideas. The "sarcasm" model played it straight and professional - perhaps the ultimate sarcasm?

## slim-extract-qwen-1.5b (117.31s) ⭐

Another slim-extract disaster, generating broken template variables and cascading into ampersand apocalypse. 117 seconds of processing to produce complete garbage - a masterclass in how not to finetune a model.

## qwen3-coder-30b-a3b-instruct-1m (127.59s) ⭐⭐⭐⭐⭐

Excellent output with professional structure and even self-aware commentary about avoiding deceptive marketing. This coder model showed strong writing abilities and ethical considerations. The 2-minute wait was worth it.

## mistral-7b-instruct-v0.3-196k-dq68-mlx (137.08s) ⭐⭐⭐

Decent but uninspired output. The 196k context window wasn't utilized, and the mlx quantization didn't seem to affect quality significantly. Solid but forgettable.

## deepseek-r1-entity-8b-quantized-v2.0 (141.87s) ⭐⭐⭐

Reasonable output with good structure but somewhat generic messaging. The entity extraction background didn't translate into particularly insightful marketing copy.

## deepseek-r1-distill-qwen-14b (145.71s) ⭐⭐⭐

Surprisingly brief output for a 14B model. Clean and professional but lacking the depth expected from 2.5 minutes of processing. Efficient but underwhelming.

## pixtral-12b-i1 (150.15s) ⭐⭐⭐

The vision-language model produced text-only output that was competent but unremarkable. No attempt to describe visual elements despite its multimodal training.

## openai_gpt-oss-20b (176.50s) ⭐⭐⭐⭐

Strong performance from this OpenAI model, with well-structured content and good messaging. The 3-minute processing time yielded professional-quality output.

## magistral-small-2507-rebased-vision-i1 (210.60s) ⭐⭐

Brief and generic output that didn't justify the 3.5-minute wait. The "vision" capabilities weren't evident in the text generation.

## r3-qwen3-14b-skywork-i1 (226.69s) ⭐⭐⭐⭐

Good quality output with creative elements and strong structure. Nearly 4 minutes of processing produced thoughtful, engaging copy.

## huihui-mistral-small-3.2-24b-instruct-2506-abliterated-llamacppfixed-i1 (244.43s) ⭐⭐⭐

Despite the complex name suggesting multiple modifications, output was standard and professional. 4 minutes for average results.

## qwen2.5-coder-3b-instruct-extract-entity (251.34s) ⭐⭐

Massive overgeneration with repetitive content. This 3B model took over 4 minutes to produce quantity over quality.

## qwen3-14b-mlx (261.86s) ⭐⭐⭐

Decent output but not exceptional for 4+ minutes of processing. The mlx optimization didn't seem to impact quality significantly.

## huihui-qwen3-14b-abliterated-v2 (294.24s) ⭐⭐⭐

Nearly 5 minutes for standard marketing copy. The "abliterated" modification didn't result in any notable improvements.

## mistral-small-24b-instruct-2501-writer-i1 (298.71s) ⭐⭐⭐⭐

The "writer" specialization showed with polished, professional copy. 5 minutes well spent for quality output.

## qwen3-128k-30b-a3b-neo-max-imatrix (319.76s) ⭐⭐

Overlong and repetitive despite the sophisticated name. 5+ minutes for mediocre results.

## slim-sa-ner-phi-3 (359.69s) ⭐

6 minutes to produce classification gibberish. The Phi-3 base didn't help this slim variant at all.

## slim-xsum-phi-3 (360.53s) ⭐

Another 6-minute disaster from the slim-phi series. Completely failed to understand the task.

## slim-summary-phi-3 (364.16s) ⭐

6 minutes for a brief summary, not a marketing email. Pattern recognition: slim + phi-3 = failure.

## slim-extract-phi-3 (365.42s) ⭐

Continued the slim-phi tradition of 6-minute failures with extraction-only output.

## slim-qa-gen-phi-3-tool (366.91s) ⭐

Generated questions instead of marketing copy. 6 minutes of missing the point entirely.

## slim-q-gen-phi-3-tool (373.38s) ⭐

More question generation instead of email writing. The slim-phi models are consistently terrible.

## slim-boolean-phi-3 (383.42s) ⭐

Over 6 minutes to produce boolean classification output. Spectacular failure.

## qwen3-30b-a3b-thinking-2507 (386.50s) ⭐⭐⭐⭐

The "thinking" variant showed thoughtful output with good structure, though 6.5 minutes is quite long.

## qwen/qwen2.5-vl-7b (404.58s) ⭐⭐⭐

Vision-language model produced standard text output in nearly 7 minutes. Acceptable but not exceptional.

## qwen2.5-vl-7b-instruct@q4_k_m (409.89s) ⭐⭐⭐

Similar performance to the base model despite quantization. Nearly 7 minutes for average results.

## smoothie-qwen3-14b-i1 (465.90s) ⭐⭐⭐

The "smoothie" branding didn't result in particularly smooth output. 7.5 minutes for standard copy.

## qwen3-4b (479.93s) ⭐⭐

8 minutes for a 4B model to produce verbose but mediocre output. Poor time-to-quality ratio.

## qwen3-32b-uncensored-i1@iq2_xs (524.81s) ⭐⭐

Extreme quantization (iq2_xs) resulted in degraded output quality despite 8.5 minutes of processing.

## qwen3-30b-a3b-instruct-2507 (534.31s) ⭐⭐⭐

Nearly 9 minutes for standard output. The large model size didn't translate to proportional quality.

## longwriter-qwen2.5-7b-instruct (546.88s) ⭐⭐⭐

The "longwriter" lived up to its name with verbose output in 9 minutes, but length didn't equal quality.

## qwen3-8b-320k-context-10x-massive (552.18s) ⭐⭐

The massive context window wasn't utilized, and 9 minutes produced standard output.

## deepseek-r1-0528-qwen3-8b (552.99s) ⭐⭐⭐

Over 9 minutes for the reasoning model to produce decent but not exceptional output.

## longwriter-v-7b-dpo-i1 (553.67s) ⭐⭐⭐

DPO training didn't significantly improve output quality for the 9-minute wait.

## deepseek/deepseek-r1-0528-qwen3-8b (554.94s) ⭐⭐⭐

Nearly identical to the non-namespaced version in both time and quality.

## internlm3-8b-instruct (593.16s) ⭐⭐⭐

10 minutes for standard marketing copy. The InternLM model didn't show particular strengths.

## longwriter-v-7b-i1 (612.22s) ⭐⭐⭐

Over 10 minutes for verbose but not particularly insightful output.

## llama3.1-8b-reasoning-summarizer (681.37s) ⭐⭐

11 minutes of "reasoning" produced overly verbose and repetitive content.

## darkidol-longwriter-v13-8b-uncensored-1048k (682.39s) ⭐⭐⭐

The dramatic "darkidol uncensored" branding resulted in perfectly normal marketing copy after 11 minutes.

## qwen3-8b-256k-context-8x-grand (737.00s) ⭐⭐

Over 12 minutes for standard output. The grand context window was completely unnecessary.

## summllama3.1-8b (765.08s) ⭐⭐

Nearly 13 minutes for a summarization model to produce verbose, unfocused output.

## qwen3-jan-nano-128k-6b-brainstorm20x-i1 (769.10s) ⭐⭐

The "brainstorm20x" modification resulted in scattered, unfocused output after 13 minutes.

## qwen3-8b-64k-josiefied-uncensored-neo-max (837.08s) ⭐⭐

14 minutes for the "josiefied neo max" version to produce standard output. The modifications added time, not quality.

## mlabonne_qwen3-14b-abliterated (1039.48s) ⭐⭐

Over 17 minutes for verbose but mediocre output. The "abliterated" modification was counterproductive.

## deepseek-r1-qwen-2.5-32b-ablated-i1 (1055.69s) ⭐⭐⭐

17.5 minutes of processing for decent but not exceptional output from this 32B model.

## deepseek-moe-4x8b-r1-distill-llama-3.1-deep-thinker-uncensored-24b (1499.24s) ⭐⭐

25 minutes for this dramatically named MoE model to produce mediocre output. The "deep thinking" was not evident.

## rombo-llm-v2.5-qwen-32b-i1 (1945.48s) ⭐⭐

Over 32 minutes(!) for standard marketing copy. Absolutely terrible time-to-quality ratio.

## qwq-32b-abliterated-i1 (2037.19s) ⭐⭐

Nearly 34 minutes for the QwQ reasoning model to produce verbose but unfocused output.

## qwen3-32b-uncensored-i1@q2_k_s (2111.42s) ⭐⭐

Over 35 minutes - the longest execution time - for mediocre output. The extreme quantization destroyed both speed and quality.

## Summary

The benchmark revealed several surprising insights:

**Winners (Definitely Keep):**
- **granite-4.0-tiny-preview** - Best overall value (64s, excellent quality)
- **mistralai_voxtral-mini-3b-2507** - Best small model (48s, great quality)
- **bling-qwen-mini-tool** - Fastest execution (8s, if you need speed over quality)
- **qwen3-coder-30b-a3b-instruct-1m** - Best large model output (128s, excellent)
- **llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b** - Best MoE performance (64s, very good)

**Acceptable (Keep for specific use cases):**
- Models in the 100-300s range with 3-4 star ratings
- Specialized extractors/summarizers if you need those functions
- Vision-language models for multimodal tasks

**Drop Immediately:**
- All slim-phi-3 variants (consistent failures)
- Models taking >500s (poor time-to-quality ratio)
- Extreme quantizations (iq2_xs, q2_k_s)
- Models producing <100 character outputs
- The ultra-slow giants (rombo, qwq-32b taking 30+ minutes)

The sweet spot appears to be well-tuned models in the 3B-14B range, executing in 30-300 seconds. Larger models and extreme context windows showed diminishing returns, while tiny models under 1B generally failed to understand the task complexity. Quantization quality matters more than model size - a well-quantized 7B model outperforms a poorly quantized 32B model.