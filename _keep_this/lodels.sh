#!/usr/bin/env bash
models=$(lms ls --llm --json | jq -r '.[].path' | sort)
for model in $models; do
    lms unload --all
    lms load --log-level debug -y --context-length 1024 "$model"
done
