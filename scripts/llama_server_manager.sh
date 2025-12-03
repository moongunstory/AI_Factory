#!/bin/bash

# llama-server 관리 스크립트 (GPU 지원)
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$PROJECT_DIR/scripts/.llama_server.pid"
LOG_FILE="$PROJECT_DIR/output/logs/llama_server.log"
MODEL_PATH="$PROJECT_DIR/models/llama-3.1-8b/model-q4_K_M.gguf"
LLAMA_SERVER="$PROJECT_DIR/engine/llama.cpp/build/bin/llama-server"

mkdir -p "$(dirname "$LOG_FILE")"

SERVER_HOST="127.0.0.1"
SERVER_PORT=8080

# GPU 지원 llama-server 파라미터
# -ngl -1 = 모든 레이어를 GPU에 로드 (CUDA 사용)
# GPU가 없으면 자동으로 CPU 사용
LLAMA_PARAMS=(
    --host "$SERVER_HOST"
    --port "$SERVER_PORT"
    --model "$MODEL_PATH"
    --ctx-size 4096              # GPU: 더 큰 컨텍스트
    --batch-size 2048            # GPU: 큰 배치 크기
    --threads 4                  # GPU 환경: CPU 스레드 적게
    --n-gpu-layers -1            # 모든 레이어를 GPU에 로드 (-1)
    --parallel 8                 # 동시 요청 처리
    --cont-batching              # Continuous batching 활성화
    --flash-attn                 # Flash Attention 활성화 (속도 향상)
    --mlock                      # 메모리 고정
    --log-disable
)

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

start_server() {
    if is_running; then
        echo "[경고] llama-server 이미 실행 중 (PID: $(cat $PID_FILE))"
        return 0
    fi

    if [ ! -f "$MODEL_PATH" ]; then
        echo "[오류] 모델 파일 없음: $MODEL_PATH"
        exit 1
    fi

    if [ ! -f "$LLAMA_SERVER" ]; then
        echo "[오류] llama-server 실행 파일 없음: $LLAMA_SERVER"
        exit 1
    fi

    echo "=========================================="
    echo " llama-server 시작 (GPU 가속)"
    echo "=========================================="
    echo "모델: ${MODEL_PATH##*/}"
    echo "포트: $SERVER_PORT"
    echo "GPU 레이어: 모두 (-1)"
    echo "Context: 4096 tokens"
    echo "Batch: 2048"
    echo "=========================================="

    nohup "$LLAMA_SERVER" "${LLAMA_PARAMS[@]}" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    local pid=$!

    echo "[시작] PID $pid"
    echo "[로그] $LOG_FILE"

    # health check
    echo -n "[대기] 서버 준비 중"
    local max_wait=60
    for ((i=0; i<$max_wait; i++)); do
        if curl -s "http://$SERVER_HOST:$SERVER_PORT/health" >/dev/null 2>&1; then
            echo ""
            echo "[완료] llama-server 준비됨!"
            echo "[URL] http://$SERVER_HOST:$SERVER_PORT"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    echo "[오류] 60초 동안 서버 응답 없음"
    stop_server
    exit 1
}

stop_server() {
    if ! is_running; then
        echo "[정보] 실행 중인 llama-server 없음"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    echo "[중지] llama-server 종료 중 (PID: $pid)"

    kill -TERM "$pid" 2>/dev/null || true

    for ((i=0; i<10; i++)); do
        if ! ps -p "$pid" >/dev/null 2>&1; then
            rm -f "$PID_FILE"
            echo "[완료] 정상 종료"
            return 0
        fi
        sleep 1
    done

    echo "[강제 종료]"
    kill -KILL "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "[완료] 강제 종료됨"
}

restart_server() {
    echo "[재시작]"
    stop_server
    sleep 2
    start_server
}

status_server() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "[상태] llama-server 실행 중"
        echo "PID: $pid"
        ps -p "$pid" -o pid,ppid,%cpu,%mem,vsz,rss,cmd
        echo ""
        if curl -s "http://$SERVER_HOST:$SERVER_PORT/health" >/dev/null 2>&1; then
            echo "✓ Health OK"
        else
            echo "✗ Health Check 실패"
        fi
    else
        echo "[상태] 실행 중 아님"
        return 1
    fi
}

cleanup_orphans() {
    echo "[정리] 고아 llama-server 프로세스 검색"
    local orphans=$(pgrep -f "llama-server .* $MODEL_PATH" || true)

    if [ -z "$orphans" ]; then
        echo "[완료] 고아 프로세스 없음"
        return 0
    fi

    for pid in $orphans; do
        if [ -f "$PID_FILE" ] && [ "$pid" == "$(cat "$PID_FILE")" ]; then
            continue
        fi
        echo "[종료] 고아 PID: $pid"
        kill -KILL "$pid" 2>/dev/null || true
    done

    echo "[완료]"
}

case "$1" in
    start) start_server ;;
    stop) stop_server ;;
    restart) restart_server ;;
    status) status_server ;;
    cleanup) cleanup_orphans ;;
    *)  echo "사용법: $0 {start|stop|restart|status|cleanup}" ;;
esac
