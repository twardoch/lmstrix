#!/bin/bash
# this_file: examples/prompts_adam/demo_adam_prompts_cli.sh
#
# Demonstration of adam.toml with simplified CLI usage
# All prompts now only require {{text}} as input
#

set -e

cd "$(dirname "$0")" || exit

echo "### LMStrix CLI Demo - Simplified adam.toml ###"

MODEL_ID="$1" # <--- CHANGE THIS to match your model
PROMPT_FILE="adam.toml"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: $PROMPT_FILE not found!"
    exit 1
fi

echo -e "\nUsing prompt file: $PROMPT_FILE"
echo "Using model: $MODEL_ID"

# Example 1: Abstractive Proposition Segmentation using --text
echo -e "\n--- Example 1: APS with --text ---"
lmstrix infer aps --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text "The Internet was originally developed by DARPA in the 1960s as ARPANET. It was designed to create a decentralized communication network that could survive nuclear attacks." \
    --out_ctx "25%"

# Example 2: Text humanization using --text
echo -e "\n--- Example 2: Humanize with --text ---"
lmstrix infer humanize --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text "The implementation of artificial intelligence systems in corporate environments necessitates careful consideration of various factors including but not limited to data privacy."

# Example 3: Using --text_file for longer content
echo -e "\n--- Example 3: Summary using --text_file ---"
# Create a temporary file with text
cat >/tmp/sample_text.txt <<'EOF'
In the summer of 1922, Nick Carraway, a young man from Minnesota, moves to New York to learn about the bond business. He rents a house in the West Egg district of Long Island, next door to a mysterious millionaire named Jay Gatsby who throws extravagant parties every Saturday night. Nick's cousin Daisy lives across the bay with her wealthy but brutish husband Tom Buchanan. As the summer progresses, Nick becomes drawn into the world of his mysterious neighbor and learns that Gatsby is deeply in love with Daisy, whom he had met years before during the war.
EOF

lmstrix infer summary --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text_file /tmp/sample_text.txt

# Example 4: TTS optimization
echo -e "\n--- Example 4: TTS Optimize ---"
lmstrix infer tts_optimize --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text "The CEO announced that Q3 revenues increased by 42% year-over-year."

# Example 5: Song lyrics generation
echo -e "\n--- Example 5: Song Generation ---"
lmstrix infer song --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text "Write a folk song about a traveler who finds home in unexpected places, with themes of belonging and discovery" \
    --temperature 0.8

# Example 6: Code review
echo -e "\n--- Example 6: Code Review ---"
lmstrix infer code_review --verbose -m "$MODEL_ID" \
    --file_prompt "$PROMPT_FILE" \
    --text 'def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)'

# Example 7: Using prompt without file_prompt (direct prompt with --text)
echo -e "\n--- Example 7: Direct prompt with --text ---"
lmstrix infer "Explain the following concept: {{text}}" --verbose -m "$MODEL_ID" \
    --text "quantum entanglement"

# Cleanup
rm -f /tmp/sample_text.txt

echo -e "\n### Demo Complete ###"
echo -e "\nKey features demonstrated:"
echo "- Using --text for inline text content"
echo "- Using --text_file for file-based content"
echo "- All prompts now only require {{text}} placeholder"
echo "- Simplified prompt structure in adam.toml"
echo -e "\nTip: View $PROMPT_FILE to see all available prompts!"
