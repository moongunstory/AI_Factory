#!/bin/bash

# AI Short Factory - 실행 스크립트

echo "==========================================="
echo " AI Short Factory - Web UI 실행기"
echo "==========================================="
echo ""

# Streamlit 설치 확인
if ! command -v streamlit &> /dev/null; then
    echo "[오류] Streamlit이 설치되지 않았습니다"
    echo "필요한 패키지를 설치합니다..."
    pip install -r requirements.txt
    echo ""
fi

# llama.cpp 모델 존재 확인
if [ ! -f "models/model-q4_K_M.gguf" ]; then
    echo "[경고] LLaMA 모델을 찾을 수 없습니다: models/model-q4_K_M.gguf"
    echo "GGUF 모델을 다운로드하여 models/ 디렉토리에 배치하세요"
    echo ""
fi

# llama-cli 존재 확인
if [ ! -f "bin/llama-cli" ]; then
    echo "[경고] llama-cli를 찾을 수 없습니다: bin/llama-cli"
    echo "llama.cpp를 빌드하여 llama-cli를 bin/ 디렉토리에 배치하세요"
    echo ""
fi

echo "Streamlit 웹 UI를 시작합니다..."
echo "브라우저에서 http://localhost:8501 로 접속하세요"
echo ""
echo "Ctrl+C를 눌러 서버를 중지할 수 있습니다"
echo ""

# Streamlit 실행
streamlit run src/app.py
