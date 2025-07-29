#!/usr/bin/env bash
for m in "mistralai/magistral-small" "kernelllm" "acereason-nemotron-1.1-7b-i1" "skywork-or1-7b-i1" "skywork-critic-llama-3.1-8b" "llama-3-8b-instruct-gradient-1048k" "llama-3.1-1-million-ctx-deephermes-deep-reasoning-8b" "qwen3-128k-30b-a3b-neo-max-imatrix" "qwen3-30b-a1.5b-64k-high-speed-neo-imatrix-max" "openreasoning-nemotron-14b" "baidu/ernie-4.5-21b-a3b" "ernie-4.5-21b-a3b-pt" "r3-qwen3-14b-skywork-i1" "minicpm-o-2_6" "exaone-deep-7.8b-i1@iq4_nl" "exaone-deep-7.8b-i1@q6_k"; do
    for c in 30000 40000 60000 80000 100000 120000; do
        echo "$c $m"
        lmstrix test -m "$m" -c "$c"
    done
done
