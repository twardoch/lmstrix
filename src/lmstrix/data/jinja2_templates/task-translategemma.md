Read @translategemma-orig.jinja2

Write @translategemma.jinja2 that in addition to plain-text prompts will also accept a JSON prompt which conforms to the structure: 

```json
{
    "input": "en", 
    "output": "pl", 
    "vocab": {"typeface": "krój pisma", "font": "font"}, 
    "context": "Some information before", 
    "text": "FontLab 8 is an integrated font editor for Mac and Windows that helps you create fonts from start to finish, from a simple design to a complex project, and brings a spark of magic into type design. Try FontLab 8 for free for 10 days, and start making fonts today!"
}
```

@translategemma.jinja2 should build upon @translategemma-orig.jinja2 but inject the OPTIONAL vocabulary into the prompt sent to the model, and inject the OPTIONAL context into the prompt sent to the model. 

Put the modified chat template into `/Volumes/Falstaff4T/RomeoData2/lmstudio/models/mlx-community/translategemma-4b-it-8bit/chat_template.jinja` and use LMStudio to perform test inference on the `translategemma-4b-it-8bit` model, like: 

You can load the model with `lms unload -a; lms load translategemma-4b-it-8bit`

Then run inference with the equivalent of: 

```
curl http://localhost:1234/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "translategemma-4b-it-8bit",
    "system_prompt": "",
    "input": "HERE COMES THE PROMPT SENT TO THE MODEL"
}'
```

Remember: LMStudio must send to the model the 'TranslateGemma prompt' that adheres strictly to @translategemma-orig.jinja2 rules.

I want to supply to LMStudio a STRING prompt that’s formatted LIKE A JSON and looks like this:

```
{"input": "en", "output": "pl", "vocab": {"typeface": "krój pisma", "font": "font"}, "context": "Some information before", "text": "FontLab 8
  is an integrated font editor for Mac and Windows that helps you create fonts from start to finish, from a simple design to a complex
project, and brings a spark of magic into type design. Try FontLab 8 for free for 10 days, and start making fonts today!"}
```

where `vocab` and `context` are optional. Only `input`, `output` and `text` are mandatory. 

The Jinja template must transform that into the 'TranslateGemma prompt' format. You must encapsulate all logic inside the Jinja template. 

Write a small tool that will help you iterate to resolve this perfectly. 

