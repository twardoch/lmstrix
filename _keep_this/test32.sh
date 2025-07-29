for c in 40000 50000 55000 60000 70000 80000 85000 90000 100000 110000 120000; do
	for m in deepseek-moe-4x8b-r1-distill-llama-3.1-deep-thinker-uncensored-24b llama-3.2-4x3b-moe-hell-california-uncensored-10b llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b qwen3-128k-30b-a3b-neo-max-imatrix kernelllm openreasoning-nemotron-14b deepseek/deepseek-r1-0528-qwen3-8b deepseek-r1-0528-qwen3-8b deepseek-r1-distill-qwen-14b huihui-mistral-small-3.2-24b-instruct-2506-abliterated-llamacppfixed-i1 magistral-small-2507-rebased-vision-i1 qwen2.5-microsoft-nextcoder-brainstorm20x-128k-ctx-12b-i1 ultron-summarizer-8b llama-3.1-8b-sarcasm summllama3.1-8b qwen3-8b-128k qwen3-8b-256k-context-8x-grand-i1@q6_k qwen3-8b-320k-context-10x-massive llama-3-8b-instruct-gradient-1048k wemake-llama-3-8b-instruct-v41-1048k llama-3.1-1-million-ctx-deephermes-deep-reasoning-8b; do
		echo; echo; echo; echo ">>>>> $c $m"
		lmstrix test -c $c -m $m; 
	done;
done