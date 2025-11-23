#!/bin/bash

# AI Short Factory - 실행 스크립트

echo "==========================================="
echo " AI Short Factory - Web UI 실행기"
echo "==========================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Flask 설치 확인
if ! python3 -c "import flask" &> /dev/null; then
    echo "[오류] Flask가 설치되지 않았습니다"
    echo "필요한 패키지를 설치합니다..."
    pip install -r requirements.txt
    echo ""
fi

# llama.cpp 모델 경로
MODEL_PATH="$PROJECT_DIR/models/llama-3.1-8b/model-q4_K_M.gguf"

# llama.cpp 실행 파일 경로
LLAMA_CLI="$PROJECT_DIR/engine/llama.cpp/build/bin/llama-cli"

# 모델 존재 확인
if [ ! -f "$MODEL_PATH" ]; then
    echo "[경고] LLaMA 모델이 없습니다:"
    echo "    $MODEL_PATH"
    echo "올바른 위치에 GGUF 모델을 두세요."
    echo ""
else
    echo "[확인] LLaMA 모델 발견됨"
fi

# llama-cli 존재 확인
if [ ! -f "$LLAMA_CLI" ]; then
    echo "[경고] llama-cli가 없습니다:"
    echo "    $LLAMA_CLI"
    echo "llama.cpp를 빌드하여 실행 파일을 생성하세요."
    echo ""
else
    echo "[확인] llama-cli 발견됨"
fi

echo ""
echo "Flask 웹 UI를 시작합니다..."
echo "  → http://localhost:5000"
echo ""
echo "Ctrl+C를 눌러 서버를 종료하세요"
echo ""

# 서버 시작 후 자동으로 브라우저 열기 (2초 후)
(sleep 2 && xdg-open http://localhost:5000 2>/dev/null) &

python3 "$PROJECT_DIR/src/web/app.py"
