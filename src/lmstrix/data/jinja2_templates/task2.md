

## TranslateGemma

- Description: @hy-mt1.5-text.md 

- Model in my LMStudio: `translategemma-4b-it-8bit` 

- Chat template (MiniJinja, not Jinja2!): `/Volumes/Falstaff4T/RomeoData2/lmstudio/models/mlx-community/translategemma-4b-it-8bit/chat_template.jinja`
  - Original chat template: ./translategemma-orig.jinja2 
  - Our working copy that we test by copying into the 'RomeoData2' location: ./translategemma.jinja2 
- Load the model in shell: `lms unload -a; lms load translategemma-4b-it-8bit`
- Run inference with the equivalent of: 

```
curl http://localhost:1234/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "translategemma-4b-it-8bit",
    "system_prompt": "",
    "input": "HERE COMES THE PROMPT SENT TO THE MODEL"
}'
```

- Test tool: ./translategemma_test.py 

## HY-MT1.5

- Description: @hy-mt1.5-text.md 

- Model in my LMStudio: `hy-mt1.5-7b` 

- Chat template: `/Volumes/Falstaff4T/RomeoData2/lmstudio/models/mlx-community/HY-MT1.5-7B-8bit/chat_template.jinja`
  - Original chat template: ./hy-mt1.5-orig.jinja2 
  - Our working copy that we test by copying into the 'RomeoData2' location: ./hy-mt1.5.jinja2 
- Load the model in shell: `lms unload -a; lms load hy-mt1.5-7b`
- Run inference with the equivalent of: 

```
curl http://localhost:1234/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hy-mt1.5-7b",
    "system_prompt": "",
    "input": "HERE COMES THE PROMPT SENT TO THE MODEL"
}'
```

## TASK

Let’s change our implementation. 

Right now both `hy-mt1.5.jinja2` and `translategemma.jinja2` both attempt to parse a JSON-like structure in the MiniJinja templates, and translate it into the 'Chinese HY-MT prompt' (see @hy-mt1.5-text.md) and 'TranslateGemma prompt' (see @translategemma-text.md) prompt format, respectively. 

Instead of parsing a JSON-like structure in the MiniJinja templates, both MiniJinja templates should parse this format: 

```
translate: 
input: en
output: pl
vocab: typeface,krój pisma
vocab: font,font
context: Some information before
text: FontLab 8 is an integrated font editor for Mac and Windows that
  helps you create fonts from start to finish, from a simple design to
  a complex project, and brings a spark of magic into type design. Try
  FontLab 8 for free for 10 days, and start making fonts today!
```

and this: 

```
translate:;input:en;output:pl;vocab:typeface,krój pisma;vocab:font,font;context: Some information before;text: FontLab 8 is an integrated font editor for Mac and Windows that helps you create fonts from start to finish, from a simple design to a complex project, and brings a spark of magic into type design. Try FontLab 8 for free for 10 days, and start making fonts today!
```

It must start with the string 'translate:'. The order of the records should be arbitrary, 'vocab' can appear multiple times, and uses comma to separate input,output. Records can be separated with ';' or newline (mixing of these is allowed). Whitespace before keys, between keys and values, and after values is irrelevant. 

I hope this is a simple format that can be parsed with MiniJinja constructs. 

Adjust the templates. The adjust the @translategemma-test.py and @hy-mt1.5-test.py scripts so they: 

- copy the templates into the 'RomeoData2' location
- load the models
- test the inference using the examples given above
- report the translation results 

Run the tools, analyze the results, report your findings, and iterate to improve the templates until we’re fully successful. 