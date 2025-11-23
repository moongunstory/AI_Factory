# Quick Start Guide

Get up and running with the AI Shorts Factory LLM Pipeline in 5 minutes.

## Prerequisites

1. **Python 3.11+** installed
2. **Local Llama model** at `/home/moon/.llama/checkpoints/Llama3.1-8B-Instruct`
3. **Local LLM server** running (see below)

## Step 1: Start Your Local LLM Server

You need a server that exposes an OpenAI-compatible Chat Completions API. Choose one:

### Option A: llama.cpp Server

```bash
# Navigate to your llama.cpp installation
cd /path/to/llama.cpp

# Start the server
./llama-server \
  --model /home/moon/.llama/checkpoints/Llama3.1-8B-Instruct \
  --port 8000 \
  --ctx-size 4096 \
  --n-gpu-layers 35
```

### Option B: vLLM

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /home/moon/.llama/checkpoints/Llama3.1-8B-Instruct \
  --port 8000
```

### Option C: Text Generation WebUI

Start the WebUI with `--api` flag and configure the OpenAI extension.

## Step 2: Install the Package

```bash
cd ~/Projects/AI_Short_Factory

# Install dependencies
pip install -r requirements.txt

# Install in editable mode (optional, for development)
pip install -e .
```

## Step 3: Set Environment Variable (Optional)

```bash
# Only needed if your server is NOT at http://localhost:8000/v1
export LOCAL_LLM_BASE_URL="http://localhost:8000/v1"
```

## Step 4: Run the Example

```bash
# Test connection first
python -c "from shorts_llm.llm_client import test_connection; print('OK' if test_connection() else 'FAILED')"

# Run the basic example
python examples/basic_usage.py

# Or run the stage-by-stage example
python examples/stage_by_stage.py
```

## Step 5: Use in Your Own Code

```python
from shorts_llm.pipeline import generate_shorts_prompt_package

result = generate_shorts_prompt_package(
    logline="Your story idea here",
    target_duration_seconds=60,
    tone="epic",
    genre="fantasy"
)

# Save results
result.to_json_file("my_short.json")

# Access the prompts
for shot in result.prompts.shots:
    print(f"{shot.shot_id}: {shot.positive_prompt}")
```

## Troubleshooting

**"Cannot connect to LLM server"**
- Is your LLM server running? Check with `curl http://localhost:8000/v1/models`
- Is it on a different port? Set `LOCAL_LLM_BASE_URL`

**"LLM response is not valid JSON"**
- Your model may need to be instruction-tuned (e.g., Llama-3.1-Instruct)
- Try lowering the temperature: `temperature_outline=0.5`

**Import errors**
- Make sure you've installed dependencies: `pip install -r requirements.txt`
- Or install the package: `pip install -e .`

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check out the example scripts in `examples/`
- Review the data schemas in `shorts_llm/schemas.py`
- Customize the system prompts in `shorts_llm/pipeline.py`

## Expected Output

After running successfully, you'll get:

1. **Story Outline**: 5-20 narrative beats
2. **Scene Plan**: 3-12 scenes with 8-40 shots
3. **Prompts**: Ready-to-use text-to-image/video prompts

All results are saved as JSON and can be loaded later.

Enjoy creating AI shorts! 🎬✨
