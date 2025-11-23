#!/bin/bash

# AI Short Factory - Story to Prompts Runner
# This script runs the story-to-prompts conversion pipeline

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==========================================="
echo " 🎬 AI Short Factory - Story to Prompts  "
echo "==========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if llama-cli exists
LLAMA_CLI="$PROJECT_DIR/engine/llama.cpp/build/bin/llama-cli"
if [ ! -f "$LLAMA_CLI" ]; then
    echo "❌ llama-cli not found at: $LLAMA_CLI"
    echo "   Please build llama.cpp first."
    exit 1
fi

# Check if model exists
MODEL_DIR="$PROJECT_DIR/models/llama-3.1-8b"
if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR/*.gguf 2>/dev/null)" ]; then
    echo "❌ No .gguf model found in: $MODEL_DIR"
    echo "   Please download a GGUF model first."
    exit 1
fi

echo "✅ Environment ready"
echo ""

# Check if story file or argument provided
if [ $# -eq 0 ]; then
    # No arguments - use example story
    if [ -f "example_story.txt" ]; then
        echo "📖 Using example story (example_story.txt)"
        echo ""
        python -m src --file example_story.txt --verbose
    else
        echo "💡 Usage examples:"
        echo "   ./run_llama.sh \"Your story here\""
        echo "   ./run_llama.sh --file story.txt"
        echo "   ./run_llama.sh --file story.txt --style anime --duration 30"
        echo ""
        echo "Running interactive mode..."
        python -m src --help
    fi
else
    # Arguments provided - pass to Python module
    echo "🚀 Running story-to-prompts conversion..."
    echo ""
    python -m src "$@"
fi

echo ""
echo "==========================================="
echo " ✅ Done! Check output/prompts/ for results"
echo "==========================================="
