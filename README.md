# AI Shorts Factory - LLM Pipeline

A production-quality Python module for generating AI short video content using a local Llama language model. Transform a simple story idea into detailed text-to-image/video prompts through a 3-stage pipeline.

## Overview

The pipeline consists of three stages:

1. **Story Outline Generation**: Transforms a logline into structured narrative beats
2. **Scene & Shot Planning**: Converts beats into detailed cinematography plans
3. **Prompt Engineering**: Generates optimized text-to-image/video prompts

All processing runs locally using your own Llama model - no external API calls, no cloud dependencies.

## Features

- **Local-first**: Runs entirely on your local Llama model
- **Strongly typed**: Full Python 3.11+ type hints with Pydantic validation
- **Production-ready**: Comprehensive error handling and logging
- **Extensible**: Clean architecture for future enhancements
- **Serializable**: All outputs are JSON-compatible for storage and sharing

## Prerequisites

- Python 3.11 or higher
- Local Llama model (e.g., Llama 3.1-8B-Instruct)
- Local LLM server exposing OpenAI-compatible Chat Completions API

### Local LLM Server

You need a local HTTP server that exposes the Llama model via an OpenAI-compatible API. Examples:

- **llama.cpp server**: `llama-server` with `--port 8000`
- **vLLM**: OpenAI-compatible server mode
- **Text Generation WebUI**: API mode
- **LocalAI**: OpenAI-compatible endpoints

The server should expose a `/chat/completions` endpoint at `http://localhost:8000/v1` (configurable).

## Installation

```bash
# Clone or navigate to the project
cd ~/Projects/AI_Short_Factory

# Install dependencies
pip install -r requirements.txt

# Install in editable mode (optional, for development)
pip install -e .
```

## Configuration

Set the local LLM server URL via environment variable:

```bash
export LOCAL_LLM_BASE_URL="http://localhost:8000/v1"
```

Or use the default: `http://localhost:8000/v1`

## Quick Start

### Basic Usage

```python
from shorts_llm.pipeline import generate_shorts_prompt_package

# Generate a complete prompt package
result = generate_shorts_prompt_package(
    logline="A knight defeats a dragon and saves the princess.",
    target_duration_seconds=60,
    tone="epic",
    genre="fantasy"
)

# Access the results
print(f"Generated {len(result.prompts.shots)} shots")
print(f"First prompt: {result.prompts.shots[0].positive_prompt}")

# Save to JSON
result.to_json_file("output/my_short.json")
```

### Stage-by-Stage Usage

```python
from shorts_llm.pipeline import (
    generate_story_outline,
    generate_scene_plan,
    generate_prompts
)

# Stage 1: Story Outline
outline = generate_story_outline(
    logline="A robot discovers it has emotions.",
    target_duration_seconds=45,
    tone="emotional",
    genre="sci-fi"
)
print(f"Beats: {len(outline.beats)}")

# Stage 2: Scene & Shot Plan
scene_plan = generate_scene_plan(outline)
print(f"Scenes: {len(scene_plan.scenes)}")

# Stage 3: Prompts
prompts = generate_prompts(scene_plan)
print(f"Shots: {len(prompts.shots)}")

# Iterate through prompts
for shot in prompts.shots:
    print(f"{shot.shot_id}: {shot.positive_prompt[:50]}...")
```

### Testing the Connection

```python
from shorts_llm.llm_client import test_connection

if test_connection():
    print("LLM server is ready!")
else:
    print("Cannot connect to LLM server")
```

## Pipeline Stages in Detail

### Stage 1: Story Outline

**Input**: Logline + optional constraints (duration, tone, genre)

**Output**: Structured story with 5-20 narrative beats

```python
outline = generate_story_outline(
    logline="A hacker infiltrates a corporate AI.",
    target_duration_seconds=90,
    tone="tense",
    genre="cyberpunk",
    temperature=0.7
)

# Access beats
for beat in outline.beats:
    print(f"{beat.title} ({beat.story_function})")
    print(f"  {beat.summary}")
```

### Stage 2: Scene & Shot Planning

**Input**: Story outline from Stage 1

**Output**: 3-12 scenes with 8-40 total shots, each with cinematography details

```python
scene_plan = generate_scene_plan(outline, temperature=0.7)

# Access scenes and shots
for scene in scene_plan.scenes:
    print(f"\n{scene.scene_id}: {scene.location_description}")
    for shot in scene.shots:
        print(f"  - {shot.shot_id}: {shot.shot_type}, {shot.duration_seconds}s")
```

### Stage 3: Prompt Engineering

**Input**: Scene plan from Stage 2

**Output**: Optimized prompts for each shot + global style guide

```python
prompts = generate_prompts(scene_plan, temperature=0.7)

# Global style (applies to all shots)
print(f"Visual Style: {prompts.global_style.visual_style}")
print(f"Color Palette: {prompts.global_style.color_palette}")

# Individual shot prompts
for shot_prompt in prompts.shots:
    print(f"\n{shot_prompt.shot_id}:")
    print(f"Positive: {shot_prompt.positive_prompt}")
    print(f"Negative: {shot_prompt.negative_prompt}")
    print(f"Duration: {shot_prompt.duration_seconds}s")
```

## Advanced Usage

### Custom Temperature per Stage

Control creativity/randomness independently for each stage:

```python
result = generate_shorts_prompt_package(
    logline="A chef's dish comes to life.",
    temperature_outline=0.8,       # More creative story structure
    temperature_scene_plan=0.6,    # Balanced shot planning
    temperature_prompts=0.7,       # Standard prompt generation
)
```

### Loading and Saving Results

```python
# Save to JSON
result.to_json_file("output/my_short.json")

# Load from JSON
from shorts_llm.schemas import ShortsGenerationResult
loaded = ShortsGenerationResult.from_json_file("output/my_short.json")

# Access data
print(loaded.outline.logline)
print(loaded.prompts.shots[0].positive_prompt)
```

### Error Handling

```python
from shorts_llm.llm_client import LLMConnectionError, InvalidLLMResponse
from pydantic import ValidationError

try:
    result = generate_shorts_prompt_package(
        logline="A detective solves a mystery.",
        target_duration_seconds=120
    )
except LLMConnectionError as e:
    print(f"Cannot connect to LLM server: {e}")
except InvalidLLMResponse as e:
    print(f"LLM returned invalid response: {e}")
except ValidationError as e:
    print(f"Data validation failed: {e}")
```

## Project Structure

```
AI_Short_Factory/
├── shorts_llm/
│   ├── __init__.py          # Package exports
│   ├── config.py            # Configuration and environment variables
│   ├── llm_client.py        # HTTP client for local Llama API
│   ├── schemas.py           # Pydantic models for all data structures
│   └── pipeline.py          # 3-stage pipeline orchestration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Data Schemas

All data structures are defined as Pydantic models in `shorts_llm/schemas.py`:

- `StoryBeat`, `StoryMetadata`, `StoryOutline` (Stage 1)
- `ShotPlan`, `ScenePlan`, `ScenePlanPackage` (Stage 2)
- `GlobalStyle`, `ShotPrompt`, `PromptPackage` (Stage 3)
- `ShortsGenerationResult` (Final output)

See the module docstrings for detailed field descriptions.

## Logging

Enable debug logging to see detailed pipeline execution:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now run the pipeline
result = generate_shorts_prompt_package(...)
```

Or set the log level via environment variable:

```bash
export SHORTS_LLM_LOG_LEVEL=DEBUG
```

## Environment Variables

- `LOCAL_LLM_BASE_URL`: Base URL for local LLM server (default: `http://localhost:8000/v1`)
- `SHORTS_LLM_LOG_LEVEL`: Logging level (default: `INFO`)

## Limitations & Future Enhancements

Current limitations:
- Requires local LLM server to be running separately
- No retry logic for transient failures (single-shot generation)
- No caching of intermediate results

Potential enhancements:
- Fine-tuning support for domain-specific prompts
- Multi-agent collaboration for different creative roles
- Automatic retry with exponential backoff
- Prompt template customization
- Support for style transfer and visual references

## Troubleshooting

**"Cannot connect to LLM server"**
- Ensure your local LLM server is running
- Check the URL with `echo $LOCAL_LLM_BASE_URL`
- Verify the server exposes `/chat/completions` endpoint

**"LLM response is not valid JSON"**
- The model may need stronger prompting or fine-tuning
- Try increasing `max_tokens` if output is truncated
- Check server logs for model errors

**"Validation failed"**
- The LLM output doesn't match expected schema
- Try adjusting temperature (lower = more consistent)
- Check that your model is instruction-tuned (e.g., Llama-Instruct)

## License

[Your license here]

## Contributing

[Your contribution guidelines here]
