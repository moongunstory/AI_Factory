#!/bin/bash

# ==========================================
# AI Short Factory - 최적화된 실행 스크립트
# ==========================================
#
# 개선사항:
# - llama-server를 단일 인스턴스로 관리
# - 프로세스 충돌 방지
# - 고아 프로세스 정리
# - Graceful shutdown
# - 메모리 최적화
#

set -e  # 에러 발생 시 즉시 종료

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLAMA_SERVER_MANAGER="$PROJECT_DIR/scripts/llama_server_manager.sh"
FLASK_APP="$PROJECT_DIR/src/web/app.py"

# 색상 출력
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================="
echo " AI Short Factory - 최적화 실행기"
echo "==========================================="
echo -e "${NC}"

# ==========================================
# 1. 의존성 확인
# ==========================================

echo -e "${YELLOW}[1/4] 의존성 확인 중...${NC}"

# Python 패키지 확인 및 설치
if ! python3 -c "import flask" &> /dev/null || ! python3 -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}필요한 패키지를 설치합니다...${NC}"
    pip install -r requirements.txt
fi

# llama.cpp 모델 확인
MODEL_PATH="$PROJECT_DIR/models/llama-3.1-8b/model-q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}[오류] LLaMA 모델이 없습니다:${NC}"
    echo "    $MODEL_PATH"
    echo "올바른 위치에 GGUF 모델을 두세요."
    exit 1
fi
echo -e "${GREEN}✓ 모델 파일 확인 완료${NC}"

# llama-server 확인
LLAMA_SERVER="$PROJECT_DIR/engine/llama.cpp/build/bin/llama-server"
if [ ! -f "$LLAMA_SERVER" ]; then
    echo -e "${RED}[오류] llama-server가 없습니다:${NC}"
    echo "    $LLAMA_SERVER"
    echo "llama.cpp를 빌드하여 실행 파일을 생성하세요."
    exit 1
fi
echo -e "${GREEN}✓ llama-server 확인 완료${NC}"

echo ""

# ==========================================
# 2. 고아 프로세스 정리
# ==========================================

echo -e "${YELLOW}[2/4] 이전 프로세스 정리 중...${NC}"
"$LLAMA_SERVER_MANAGER" cleanup 2>/dev/null || true
echo -e "${GREEN}✓ 정리 완료${NC}"
echo ""

# ==========================================
# 3. llama-server 시작
# ==========================================

echo -e "${YELLOW}[3/4] llama-server 시작 중...${NC}"

# 이미 실행 중인지 확인
if "$LLAMA_SERVER_MANAGER" status &> /dev/null; then
    echo -e "${GREEN}✓ llama-server가 이미 실행 중입니다${NC}"
else
    # 새로 시작
    "$LLAMA_SERVER_MANAGER" start
fi

echo ""

# ==========================================
# 4. Flask 웹 UI 시작
# ==========================================

echo -e "${YELLOW}[4/4] Flask 웹 UI 시작 중...${NC}"
echo ""
echo -e "${GREEN}==========================================="
echo " 🚀 AI Short Factory 실행 중"
echo "==========================================="
echo -e " Web UI: ${BLUE}http://localhost:5000${NC}"
echo -e " llama-server: ${BLUE}http://localhost:8080${NC}"
echo ""
echo -e " ${YELLOW}Ctrl+C${NC}를 눌러 서버를 종료하세요"
echo -e "${GREEN}==========================================="
echo -e "${NC}"

# Cleanup function for graceful shutdown
cleanup() {
    echo ""
    echo -e "${YELLOW}[종료] 서버를 종료하는 중...${NC}"

    # Flask 종료 (현재 스크립트 종료 시 자동으로 종료됨)
    echo -e "${YELLOW}  ➜ Flask 종료 중...${NC}"

    # llama-server는 계속 실행 상태로 유지 (다음 실행 시 재사용)
    # 종료하려면 수동으로: ./scripts/llama_server_manager.sh stop
    echo -e "${GREEN}  ✓ Flask 종료 완료${NC}"
    echo ""
    echo -e "${BLUE}[안내] llama-server는 백그라운드에서 계속 실행됩니다${NC}"
    echo -e "${BLUE}       다음 실행 시 빠르게 시작됩니다${NC}"
    echo -e "${BLUE}       종료하려면: ./scripts/llama_server_manager.sh stop${NC}"
    echo ""

    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT TERM

# 브라우저 자동 열기 (2초 후)
(sleep 2 && xdg-open http://localhost:5000 2>/dev/null) &

# Flask 실행
python3 "$FLASK_APP"
