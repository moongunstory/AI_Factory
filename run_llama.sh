#!/bin/bash

PROJECT_DIR="$HOME/Projects/AI_Short_Factory"

$PROJECT_DIR/llama.cpp/build/bin/llama-server \
  --model $PROJECT_DIR/models/llama-3.1-8b-instruct/llama-3.1-8b-instruct.gguf \
  --port 8080 \
  --threads 6 \
  --batch-size 16 \
  --ctx-size 4096 \
  --gpu-layers 0 \
  --rope-scaling linear
