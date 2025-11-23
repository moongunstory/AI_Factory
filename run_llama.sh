#!/bin/bash

MODEL_PATH="$HOME/models/llama-3.1-8b/model-q4_K_M.gguf"
PORT=8080

echo "[INFO] Starting Llama Server..."
~/Projects/AI_Short_Factory/llama.cpp/build/bin/llama-server \
  -m "$MODEL_PATH" \
  --port $PORT \
  --ctx-size 4096 \
  --threads 6
