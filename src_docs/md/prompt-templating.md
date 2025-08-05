---
# this_file: src_docs/md/prompt-templating.md
title: Prompt Templating Guide
description: Master advanced prompt engineering with TOML templates, variable substitution, and reusable prompt libraries
---

# Prompt Templating Guide

LMStrix's prompt templating system enables sophisticated prompt engineering through TOML-based templates, variable substitution, conditional logic, and reusable prompt libraries. This guide covers everything from basic templates to advanced prompt engineering patterns.

## 🎯 Template Basics

### What are Prompt Templates?

Prompt templates are reusable prompt patterns that:

- **Separate structure from content** - Define prompt logic once, use with different data
- **Enable variable substitution** - Dynamic content injection
- **Promote consistency** - Standardize prompt formats across applications
- **Facilitate maintenance** - Update prompts in one place
- **Support versioning** - Track prompt evolution over time

### TOML Template Format

LMStrix uses TOML (Tom's Obvious Minimal Language) for template definition:

```toml
# Basic template structure
[template_name]
prompt = "Your prompt template with {{variables}}"
description = "Optional template description"
version = "1.0"
tags = ["category", "use_case"]

[another_template]
prompt = """
Multi-line prompt template
with {{variable1}} and {{variable2}}
"""
```

## 📝 Basic Templates

### Simple Variable Substitution

Create a basic template file `basic_prompts.toml`:

```toml
[greeting]
prompt = "Hello {{name}}, how can I help you today?"
description = "Simple greeting template"

[question]
prompt = "Please answer this question: {{question}}"

[summary]
prompt = "Create a brief summary of the following text: {{text}}"
```

Use with CLI:

```bash
# Use greeting template
lmstrix infer greeting --file-prompt basic_prompts.toml --text "Alice"

# Use summary template with file input
lmstrix infer summary --file-prompt basic_prompts.toml --text-file document.txt

# Use question template
lmstrix infer question --file-prompt basic_prompts.toml --text "What is machine learning?"
```

Use with Python API:

```python
from lmstrix.core.inference_manager import InferenceManager

manager = InferenceManager()

result = manager.infer_with_template(
    template_name="summary",
    model_id="llama-3.2-3b-instruct",
    template_file="basic_prompts.toml",
    variables={"text": "Content to summarize..."},
    out_ctx=200
)

print(result['response'])
```

### Multi-Variable Templates

```toml
[analysis]
prompt = """
Analyze the following {{content_type}} about {{topic}}:

Content: {{content}}

Please provide:
1. Key insights about {{topic}}
2. {{analysis_type}} analysis
3. Recommendations
"""
description = "Flexible analysis template"

[comparison]
prompt = """
Compare {{item1}} and {{item2}} based on the following criteria:
- {{criteria1}}
- {{criteria2}}
- {{criteria3}}

Item 1: {{item1_description}}
Item 2: {{item2_description}}

Provide a detailed comparison and recommendation.
"""
```

Usage:

```python
result = manager.infer_with_template(
    template_name="analysis",
    model_id="mistral-7b-instruct",
    template_file="prompts.toml",
    variables={
        "content_type": "research paper",
        "topic": "artificial intelligence",
        "content": "Paper content here...",
        "analysis_type": "technical"
    }
)
```

## 🔧 Advanced Template Features

### Conditional Logic

Use conditional blocks for dynamic prompt construction:

```toml
[conditional_summary]
prompt = """
{{#if detailed}}
Create a comprehensive, detailed summary of the following text.
Include key points, supporting details, and analysis.
{{else}}
Create a brief summary of the following text.
Focus on the main points only.
{{/if}}

{{#if include_keywords}}
Also extract the top 5 keywords from the text.
{{/if}}

Text: {{text}}
"""

[adaptive_response]
prompt = """
{{#if user_level == "beginner"}}
Explain {{topic}} in simple terms that a beginner can understand.
Use analogies and avoid technical jargon.
{{else if user_level == "intermediate"}}
Explain {{topic}} with moderate technical detail.
Include some technical terms but explain them.
{{else}}
Provide a detailed technical explanation of {{topic}}.
Use appropriate technical terminology and assume prior knowledge.
{{/if}}
"""
```

### Loops and Iteration

Process lists and repeating content:

```toml
[multi_question]
prompt = """
Please answer the following questions:

{{#each questions}}
{{@index}}. {{this}}
{{/each}}

Provide clear, concise answers for each question.
"""

[batch_analysis]
prompt = """
Analyze each of the following items:

{{#each items}}
Item {{@index}}: {{this.name}}
Description: {{this.description}}
{{#if this.priority}}Priority: {{this.priority}}{{/if}}

{{/each}}

Provide insights for each item and overall recommendations.
"""
```

### Nested Templates

Build complex prompts from smaller components:

```toml
[role_prompt]
prompt = """
You are {{role.name}}, {{role.description}}.

{{role.instructions}}

{{#if role.constraints}}
Important constraints:
{{#each role.constraints}}
- {{this}}
{{/each}}
{{/if}}
"""

[task_prompt]
prompt = """
{{> role_prompt}}

Your task is to {{task.action}} the following {{task.type}}:

{{task.content}}

{{#if task.requirements}}
Requirements:
{{#each task.requirements}}
- {{this}}
{{/each}}
{{/if}}

{{task.output_format}}
"""
```

### Template Inheritance

Create template hierarchies:

```toml
# Base template
[base_analysis]
prompt = """
{{#block "introduction"}}
Analyze the following content:
{{/block}}

{{#block "content"}}
{{content}}
{{/block}}

{{#block "instructions"}}
Provide a thorough analysis.
{{/block}}
"""

# Specialized template extending base
[technical_analysis]
extends = "base_analysis"
prompt = """
{{#block "introduction"}}
Perform a technical analysis of the following content:
{{/block}}

{{#block "instructions"}}
Focus on:
1. Technical accuracy
2. Implementation details
3. Performance implications
4. Best practices
{{/block}}
"""
```

## 📚 Template Libraries

### Organizing Templates

Structure templates by category and use case:

```
prompts/
├── analysis/
│   ├── general.toml
│   ├── technical.toml
│   └── financial.toml
├── creative/
│   ├── writing.toml
│   ├── brainstorming.toml
│   └── storytelling.toml
├── qa/
│   ├── educational.toml
│   ├── technical.toml
│   └── conversational.toml
└── utility/
    ├── summarization.toml
    ├── translation.toml
    └── formatting.toml
```

### Analysis Templates

```toml
# analysis/general.toml
[comprehensive_analysis]
prompt = """
Conduct a comprehensive analysis of: {{subject}}

Context: {{context}}
Data: {{data}}

Analysis Framework:
1. Executive Summary
2. Key Findings
3. Detailed Analysis
4. Implications
5. Recommendations
6. Next Steps

Please be thorough and objective in your analysis.
"""

[swot_analysis]
prompt = """
Perform a SWOT analysis for: {{subject}}

Context: {{context}}

Please analyze:
- Strengths: Internal positive factors
- Weaknesses: Internal areas for improvement  
- Opportunities: External positive possibilities
- Threats: External potential challenges

{{#if include_matrix}}
Present results in a structured matrix format.
{{/if}}
"""

[comparative_analysis]
prompt = """
Compare and contrast {{item1}} and {{item2}}.

Comparison criteria:
{{#each criteria}}
- {{this}}
{{/each}}

{{#if context}}
Context: {{context}}
{{/if}}

Provide:
1. Side-by-side comparison
2. Advantages and disadvantages of each
3. Use case recommendations
4. Overall assessment
"""
```

### Creative Writing Templates

```toml
# creative/writing.toml
[story_generator]
prompt = """
Write a {{genre}} story with the following elements:

Setting: {{setting}}
Main character: {{protagonist}}
Conflict: {{conflict}}
{{#if theme}}Theme: {{theme}}{{/if}}

Requirements:
- Length: {{length}} words
- Tone: {{tone}}
- Target audience: {{audience}}

{{#if constraints}}
Additional constraints:
{{#each constraints}}
- {{this}}
{{/each}}
{{/if}}
"""

[character_development]
prompt = """
Develop a detailed character profile for: {{character_name}}

Basic Information:
- Role in story: {{role}}
- Age: {{age}}
- Background: {{background}}

Please create:
1. Physical description
2. Personality traits
3. Backstory
4. Motivations and goals
5. Character arc
6. Relationships with other characters
7. Distinctive dialogue style

{{#if additional_notes}}
Additional notes: {{additional_notes}}
{{/if}}
"""

[dialogue_writer]
prompt = """
Write a dialogue between {{character1}} and {{character2}}.

Setting: {{setting}}
Situation: {{situation}}
Mood: {{mood}}

Character 1 ({{character1}}):
- Personality: {{char1_personality}}
- Goal in conversation: {{char1_goal}}

Character 2 ({{character2}}):
- Personality: {{char2_personality}}  
- Goal in conversation: {{char2_goal}}

Write natural, engaging dialogue that advances the plot and reveals character.
"""
```

### Educational Templates

```toml
# qa/educational.toml
[explain_concept]
prompt = """
Explain {{concept}} to a {{audience_level}} audience.

{{#if context}}
Context: {{context}}
{{/if}}

Please include:
1. Clear definition
2. Key characteristics
3. Real-world examples
4. {{#if audience_level == "beginner"}}Simple analogies{{else}}Practical applications{{/if}}
5. Common misconceptions (if any)

{{#if related_concepts}}
Also briefly mention how it relates to: {{related_concepts}}
{{/if}}

Use {{tone}} tone and make it engaging.
"""

[step_by_step_guide]
prompt = """
Create a step-by-step guide for: {{task}}

Audience: {{audience}}
Difficulty level: {{difficulty}}
{{#if prerequisites}}Prerequisites: {{prerequisites}}{{/if}}

Format:
1. Overview and goals
2. Required materials/tools
3. Detailed step-by-step instructions
4. Tips and best practices
5. Common pitfalls to avoid
6. Troubleshooting guide

{{#if time_estimate}}
Estimated time: {{time_estimate}}
{{/if}}
"""

[quiz_generator]
prompt = """
Create a {{quiz_type}} quiz about {{topic}}.

Requirements:
- Number of questions: {{num_questions}}
- Difficulty: {{difficulty}}
- Question types: {{question_types}}

{{#if learning_objectives}}
Learning objectives:
{{#each learning_objectives}}
- {{this}}
{{/each}}
{{/if}}

Include:
1. Questions with multiple choice answers
2. Correct answers
3. Explanations for each answer
4. Difficulty rationale
"""
```

## 🛠️ Template Development Tools

### Template Validation

Validate templates before use:

```python
from lmstrix.loaders.prompt_loader import PromptLoader, TemplateValidator

validator = TemplateValidator()

# Validate template file
validation_result = validator.validate_file("prompts.toml")

if validation_result.is_valid:
    print("✅ Template file is valid")
else:
    print("❌ Validation errors:")
    for error in validation_result.errors:
        print(f"  • {error}")
```

### Template Testing

Test templates with sample data:

```python
from lmstrix.utils.template_tester import TemplateTester

tester = TemplateTester()

# Test template with sample variables
test_result = tester.test_template(
    template_file="prompts.toml",
    template_name="analysis",
    test_variables={
        "subject": "Python programming",
        "context": "Educational tutorial",
        "data": "Sample code examples"
    },
    model_id="llama-3.2-3b-instruct"
)

print(f"Template test result: {test_result.success}")
print(f"Generated prompt length: {test_result.prompt_length}")
print(f"Response quality score: {test_result.quality_score}")
```

### Template Analytics

Analyze template performance:

```python
from lmstrix.utils.template_analytics import TemplateAnalytics

analytics = TemplateAnalytics()

# Track template usage
analytics.track_usage("analysis", {
    "model_id": "llama-3.2-3b-instruct",
    "success": True,
    "response_time": 5.2,
    "tokens_used": 342,
    "user_rating": 4.5
})

# Get template performance metrics
metrics = analytics.get_template_metrics("analysis")
print(f"Usage count: {metrics['usage_count']}")
print(f"Average rating: {metrics['avg_rating']:.2f}")
print(f"Success rate: {metrics['success_rate']:.1%}")
print(f"Average response time: {metrics['avg_response_time']:.1f}s")
```

## 🎨 Prompt Engineering Best Practices

### Template Design Principles

1. **Clarity and Specificity**
   ```toml
   # Good: Specific and clear
   [bug_report_analysis]
   prompt = """
   Analyze this bug report and categorize it by:
   - Severity (Critical, High, Medium, Low)
   - Component affected
   - Root cause category
   - Estimated effort to fix
   
   Bug report: {{bug_description}}
   """
   
   # Avoid: Vague and ambiguous
   [generic_analysis]
   prompt = "Analyze this: {{content}}"
   ```

2. **Consistent Structure**
   ```toml
   # Use consistent formatting patterns
   [structured_template]
   prompt = """
   ## Task: {{task_title}}
   
   ### Context
   {{context}}
   
   ### Requirements
   {{#each requirements}}
   - {{this}}
   {{/each}}
   
   ### Output Format
   {{output_format}}
   """
   ```

3. **Flexible Parameters**
   ```toml
   [adaptive_explanation]
   prompt = """
   {{#if audience_level}}
   Explain {{topic}} for a {{audience_level}} audience.
   {{else}}
   Explain {{topic}} in general terms.
   {{/if}}
   
   {{#if max_length}}
   Keep the explanation under {{max_length}} words.
   {{/if}}
   
   {{#if include_examples}}
   Include practical examples.
   {{/if}}
   """
   ```

### Variable Naming Conventions

Use clear, descriptive variable names:

```toml
# Good: Descriptive names
[content_analysis]
prompt = """
Analyze the {{content_type}} titled "{{content_title}}" 
from the perspective of {{analysis_perspective}}.

Content: {{content_body}}
Target audience: {{target_audience}}
Analysis depth: {{analysis_depth}}
"""

# Avoid: Generic names
[analysis]
prompt = "Analyze {{x}} using {{y}} for {{z}}"
```

### Error Handling in Templates

Build robust templates with fallbacks:

```toml
[robust_template]
prompt = """
{{#if task}}
Task: {{task}}
{{else}}
Task: General analysis
{{/if}}

{{#if content}}
Content to analyze: {{content}}
{{else}}
No content provided. Please provide content for analysis.
{{/if}}

{{#if requirements}}
Requirements:
{{#each requirements}}
- {{this}}
{{/each}}
{{else}}
Default requirements:
- Be thorough and objective
- Provide actionable insights
{{/if}}
"""
```

## 🔄 Template Workflows

### Development Workflow

1. **Design Phase**
   - Define use case and requirements
   - Identify variables and logic needed
   - Sketch template structure

2. **Implementation Phase**
   - Write initial template
   - Add variable substitution
   - Implement conditional logic

3. **Testing Phase**
   - Validate template syntax
   - Test with sample data
   - Evaluate output quality

4. **Optimization Phase**
   - Refine prompts based on results
   - Optimize for different models
   - Add error handling

5. **Production Phase**
   - Deploy to template library
   - Monitor usage and performance
   - Iterate based on feedback

### Version Control

Track template evolution:

```toml
[analysis_v1]
prompt = "Basic analysis template"
version = "1.0"
deprecated = true
replaced_by = "analysis_v2"

[analysis_v2]
prompt = "Improved analysis template with better structure"
version = "2.0"
changelog = [
    "Added structured output format",
    "Improved clarity of instructions",
    "Added support for multiple analysis types"
]
```

### A/B Testing Templates

Compare template performance:

```python
from lmstrix.utils.ab_testing import TemplateABTester

tester = TemplateABTester()

# Set up A/B test
test_id = tester.create_test(
    name="analysis_template_comparison",
    template_a="analysis_v1",
    template_b="analysis_v2",
    test_variables={"content": "sample_content"},
    models=["llama-3.2-3b-instruct", "mistral-7b-instruct"],
    metrics=["response_quality", "response_time", "user_satisfaction"]
)

# Run test
results = tester.run_test(test_id, sample_size=100)

# Analyze results
winner = tester.analyze_results(test_id)
print(f"Winning template: {winner.template_name}")
print(f"Confidence level: {winner.confidence:.1%}")
print(f"Performance improvement: {winner.improvement:.1%}")
```

## 📊 Template Performance Optimization

### Model-Specific Optimization

Optimize templates for different models:

```toml
# Template optimized for smaller models (3B-7B)
[analysis_small_model]
prompt = """
Analyze: {{content}}

Focus on:
1. Main points
2. Key insights  
3. Brief recommendations

Keep response concise and clear.
"""

# Template optimized for larger models (13B+)
[analysis_large_model]
prompt = """
Conduct a comprehensive analysis of the following content,
demonstrating deep understanding and nuanced reasoning:

{{content}}

Please provide:
1. Executive summary with key findings
2. Detailed analysis with supporting evidence
3. Multiple perspectives and viewpoints
4. Implications and consequences
5. Actionable recommendations with rationale
6. Potential challenges and mitigation strategies

Use sophisticated reasoning and provide comprehensive insights.
"""
```

### Dynamic Template Selection

Automatically choose optimal templates:

```python
from lmstrix.utils.template_selector import SmartTemplateSelector

selector = SmartTemplateSelector()

# Register template variants
selector.register_template_variant("analysis", "small_model", {
    "model_size_range": (0, 7000),  # Parameters in millions
    "template_file": "analysis_optimized.toml",
    "template_name": "analysis_small_model"
})

selector.register_template_variant("analysis", "large_model", {
    "model_size_range": (7000, None),
    "template_file": "analysis_optimized.toml", 
    "template_name": "analysis_large_model"
})

# Automatically select best template
best_template = selector.select_template(
    base_template="analysis",
    model_id="llama-3.2-3b-instruct",
    context_size=2048
)

# Use selected template
result = manager.infer_with_template(
    template_name=best_template.name,
    template_file=best_template.file,
    model_id="llama-3.2-3b-instruct",
    variables={"content": "Content to analyze"}
)
```

## 🚀 Advanced Use Cases

### Dynamic Prompt Assembly

Build prompts dynamically based on context:

```python
from lmstrix.core.prompt_builder import DynamicPromptBuilder

builder = DynamicPromptBuilder()

# Define prompt components
builder.add_component("role", "You are an expert {{domain}} analyst.")
builder.add_component("task", "Analyze the following {{content_type}}:")
builder.add_component("content", "{{content}}")
builder.add_component("format", "Provide analysis in {{output_format}} format.")

# Build prompt based on context
prompt = builder.build({
    "domain": "financial",
    "content_type": "quarterly report",
    "content": "Q3 financial data...",
    "output_format": "structured"
})
```

### Multi-Turn Conversation Templates

Design templates for conversational AI:

```toml
[conversation_starter]
prompt = """
{{#if context.is_new_conversation}}
Hello! I'm here to help with {{topic}}. 
What would you like to know?
{{else}}
Continuing our discussion about {{topic}}.
What's your next question?
{{/if}}

{{#if context.previous_topics}}
We've previously discussed: {{context.previous_topics}}
{{/if}}
"""

[follow_up_handler]
prompt = """
Based on our previous discussion about {{previous_topic}},
you're now asking about {{current_topic}}.

Previous context: {{conversation_history}}

Current question: {{user_question}}

Please provide a helpful response that:
1. Acknowledges the previous context
2. Directly addresses the current question
3. Suggests related topics if relevant
"""
```

### Prompt Chaining

Chain multiple prompts for complex tasks:

```python
from lmstrix.utils.prompt_chain import PromptChain

chain = PromptChain()

# Define chain steps
chain.add_step("extract_key_points", {
    "template": "key_point_extraction",
    "variables": {"content": "{{input}}"}
})

chain.add_step("analyze_points", {
    "template": "point_analysis", 
    "variables": {"points": "{{extract_key_points.output}}"}
})

chain.add_step("generate_summary", {
    "template": "final_summary",
    "variables": {
        "points": "{{extract_key_points.output}}",
        "analysis": "{{analyze_points.output}}"
    }
})

# Execute chain
result = chain.execute(
    input_data={"input": "Long document content..."},
    model_id="llama-3.2-3b-instruct"
)

print(f"Final summary: {result.final_output}")
print(f"Chain execution time: {result.total_time:.2f}s")
```

## 🚀 Next Steps

Master prompt templating, then explore:

- **[Performance & Optimization](performance.md)** - Production optimization techniques
- **[Model Management](model-management.md)** - Advanced model operations
- **[Python API](python-api.md)** - Programmatic template usage
- **[CLI Interface](cli-interface.md)** - Command-line template workflows

---

*Prompt templating mastered! Craft powerful, reusable prompts! 🎨*