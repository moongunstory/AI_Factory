#!/bin/bash

##############################################################################
# AI Shorts Factory - Llama Server & Gradio UI Launcher
##############################################################################

set -e

PROJECT_DIR="$HOME/Projects/AI_Short_Factory"
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Configuration
LLAMA_BIN="$PROJECT_DIR/llama.cpp/build/bin/llama-server"
MODEL_PATH="$PROJECT_DIR/models/llama-3.1-8b-instruct/llama-3.1-8b-instruct.gguf"
LLAMA_PORT=8080
LLAMA_LOG="llama_server.log"
GRADIO_PORT=7860

# PID files
LLAMA_PID_FILE="/tmp/ai_shorts_llama.pid"
GRADIO_PID_FILE="/tmp/ai_shorts_gradio.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}[INFO] Shutting down...${NC}"

    if [ -f "$GRADIO_PID_FILE" ]; then
        GRADIO_PID=$(cat "$GRADIO_PID_FILE")
        if kill -0 "$GRADIO_PID" 2>/dev/null; then
            echo -e "${BLUE}[STOP] Stopping Gradio UI (PID: $GRADIO_PID)${NC}"
            kill "$GRADIO_PID" 2>/dev/null || true
        fi
        rm -f "$GRADIO_PID_FILE"
    fi

    if [ -f "$LLAMA_PID_FILE" ]; then
        LLAMA_PID=$(cat "$LLAMA_PID_FILE")
        if kill -0 "$LLAMA_PID" 2>/dev/null; then
            echo -e "${BLUE}[STOP] Stopping Llama Server (PID: $LLAMA_PID)${NC}"
            kill "$LLAMA_PID" 2>/dev/null || true
        fi
        rm -f "$LLAMA_PID_FILE"
    fi

    echo -e "${GREEN}[OK] Cleanup complete${NC}"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Check if llama-server binary exists
if [ ! -f "$LLAMA_BIN" ]; then
    echo -e "${RED}[ERROR] llama-server binary not found at: $LLAMA_BIN${NC}"
    echo "Please build llama.cpp first."
    exit 1
fi

# Check if model exists
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}[ERROR] Model file not found at: $MODEL_PATH${NC}"
    echo "Please download the model first."
    exit 1
fi

# Start Llama Server
echo -e "${BLUE}[INFO] Starting Llama Server...${NC}"

"$LLAMA_BIN" \
  --model "$MODEL_PATH" \
  --port "$LLAMA_PORT" \
  --threads 6 \
  --batch-size 16 \
  --ctx-size 4096 \
  --gpu-layers 0 \
  --rope-scaling linear \
  > "$LLAMA_LOG" 2>&1 &

LLAMA_PID=$!
echo "$LLAMA_PID" > "$LLAMA_PID_FILE"

echo -e "${GREEN}[OK] Llama Server started (PID: $LLAMA_PID)${NC}"
echo -e "     Log: $LLAMA_LOG"

# Wait for Llama server to be ready
echo -e "${BLUE}[INFO] Waiting for Llama server to respond...${NC}"

MAX_WAIT=30  # Maximum wait time in seconds
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$LLAMA_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}[OK] Llama server is live!${NC}"
        break
    fi

    # Check if process is still running
    if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
        echo -e "${RED}[ERROR] Llama server process died unexpectedly${NC}"
        echo "Check the log file: $LLAMA_LOG"
        tail -20 "$LLAMA_LOG"
        rm -f "$LLAMA_PID_FILE"
        exit 1
    fi

    echo -n "."
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo -e "${RED}[ERROR] Llama server failed to start within ${MAX_WAIT}s${NC}"
    echo "Check the log file: $LLAMA_LOG"
    tail -20 "$LLAMA_LOG"
    cleanup
    exit 1
fi

# Give it a bit more time to fully initialize
sleep 2

# Start Gradio Web UI
echo -e "${BLUE}[INFO] Starting Gradio Web UI...${NC}"

python3 app.py > gradio.log 2>&1 &
GRADIO_PID=$!
echo "$GRADIO_PID" > "$GRADIO_PID_FILE"

echo -e "${GREEN}[OK] Web UI started (PID: $GRADIO_PID)${NC}"
echo -e "     Access here: http://localhost:$GRADIO_PORT"

# Status summary
echo ""
echo "=" * 80
echo -e "${GREEN}[INFO] All systems running.${NC}"
echo "=" * 80
echo -e "  ${BLUE}Llama Server:${NC} http://localhost:$LLAMA_PORT (PID: $LLAMA_PID)"
echo -e "  ${BLUE}Gradio UI:${NC}    http://localhost:$GRADIO_PORT (PID: $GRADIO_PID)"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop.${NC}"
echo ""

# Wait for processes
while true; do
    # Check if llama server is still running
    if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
        echo -e "${RED}[ERROR] Llama server stopped unexpectedly${NC}"
        cleanup
        exit 1
    fi

    # Check if Gradio is still running
    if ! kill -0 "$GRADIO_PID" 2>/dev/null; then
        echo -e "${RED}[ERROR] Gradio UI stopped unexpectedly${NC}"
        cleanup
        exit 1
    fi

    sleep 2
done
