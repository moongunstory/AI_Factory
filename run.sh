#!/bin/bash

# AI Short Factory - Run Script

echo "==========================================="
echo " 🎬 AI Short Factory - Web UI Launcher"
echo "==========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit is not installed"
    echo "Installing requirements..."
    pip install -r requirements.txt
    echo ""
fi

# Check if llama.cpp model exists
if [ ! -f "models/model-q4_K_M.gguf" ]; then
    echo "⚠️  Warning: LLaMA model not found at models/model-q4_K_M.gguf"
    echo "Please download a GGUF model and place it in the models/ directory"
    echo ""
fi

# Check if llama-cli exists
if [ ! -f "bin/llama-cli" ]; then
    echo "⚠️  Warning: llama-cli not found at bin/llama-cli"
    echo "Please build llama.cpp and place llama-cli in the bin/ directory"
    echo ""
fi

echo "🚀 Starting Streamlit web UI..."
echo "📱 The app will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run streamlit
streamlit run app.py
