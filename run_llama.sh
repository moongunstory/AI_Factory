#!/bin/bash

MODEL_PATH="$HOME/Projects/AI_Short_Factory/models/llama-3.1-8b/model-q4_K_M.gguf"
ENGINE_PATH="$HOME/Projects/AI_Short_Factory/engine/llama.cpp/build/bin/llama-server"
PORT=8080

echo "==========================================="
echo " 🚀 Starting Llama.cpp Engine (Optimized) "
echo "==========================================="

$ENGINE_PATH \
  -m "$MODEL_PATH" \
  --port $PORT \
  --ctx-size 4096 \
  --threads 6 \
  --batch-size 32 \
  --no-mmap \
  --verbose-prompt
