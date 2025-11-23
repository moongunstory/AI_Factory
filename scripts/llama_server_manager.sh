#!/bin/bash

# llama-server 관리 스크립트
# 단일 인스턴스 보장, PID 기반 프로세스 관리

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$PROJECT_DIR/.llama_server.pid"
LOG_FILE="$PROJECT_DIR/output/logs/llama_server.log"
MODEL_PATH="$PROJECT_DIR/models/llama-3.1-8b/model-q4_K_M.gguf"
LLAMA_SERVER="$PROJECT_DIR/engine/llama.cpp/build/bin/llama-server"

# 로그 디렉토리 생성
mkdir -p "$(dirname "$LOG_FILE")"

# 서버 포트 및 호스트
SERVER_HOST="127.0.0.1"
SERVER_PORT=8080

# 최적화된 llama-server 파라미터
# CPU-only 환경에 최적화됨
LLAMA_PARAMS=(
    --host "$SERVER_HOST"
    --port "$SERVER_PORT"
    --model "$MODEL_PATH"
    --ctx-size 1024              # 4096 → 1024 (메모리 75% 절감)
    --batch-size 512             # 배치 처리 효율성
    --threads 8                  # CPU 코어 활용 (시스템에 따라 조정)
    --n-gpu-layers 0             # CPU 전용
    --n-parallel 4               # 동시 요청 4개 처리
    --cont-batching              # Continuous batching 활성화
    --flash-attn                 # Flash attention (속도 향상)
    --mlock                      # 메모리 고정 (스왑 방지)
    --log-disable                # 내부 로그 비활성화
)

function is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            # PID 파일은 있지만 프로세스 없음 (고아 파일)
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

function start_server() {
    if is_running; then
        echo "[경고] llama-server가 이미 실행 중입니다 (PID: $(cat "$PID_FILE"))"
        return 0
    fi

    # 모델 파일 확인
    if [ ! -f "$MODEL_PATH" ]; then
        echo "[오류] 모델 파일을 찾을 수 없습니다: $MODEL_PATH"
        exit 1
    fi

    # llama-server 실행 파일 확인
    if [ ! -f "$LLAMA_SERVER" ]; then
        echo "[오류] llama-server를 찾을 수 없습니다: $LLAMA_SERVER"
        echo "llama.cpp를 빌드해주세요."
        exit 1
    fi

    echo "=========================================="
    echo " llama-server 시작"
    echo "=========================================="
    echo "모델: $(basename "$MODEL_PATH")"
    echo "포트: $SERVER_PORT"
    echo "Context: 1024 tokens"
    echo "Threads: 8"
    echo "동시 요청: 4"
    echo "=========================================="
    echo ""

    # 백그라운드에서 llama-server 실행
    nohup "$LLAMA_SERVER" "${LLAMA_PARAMS[@]}" > "$LOG_FILE" 2>&1 &
    local pid=$!

    # PID 저장
    echo $pid > "$PID_FILE"

    echo "[시작] llama-server 프로세스 시작됨 (PID: $pid)"
    echo "[로그] $LOG_FILE"

    # 서버 준비 대기 (health check)
    echo -n "[대기] 서버 초기화 중"
    local max_wait=60
    local count=0

    while [ $count -lt $max_wait ]; do
        if curl -s "http://$SERVER_HOST:$SERVER_PORT/health" > /dev/null 2>&1; then
            echo ""
            echo "[완료] llama-server 준비 완료!"
            echo "[URL] http://$SERVER_HOST:$SERVER_PORT"
            return 0
        fi
        echo -n "."
        sleep 1
        count=$((count + 1))
    done

    echo ""
    echo "[오류] 서버 시작 시간 초과 (60초)"
    echo "[힌트] 로그를 확인하세요: $LOG_FILE"

    # 실패 시 정리
    stop_server
    exit 1
}

function stop_server() {
    if ! is_running; then
        echo "[정보] llama-server가 실행 중이 아닙니다"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    echo "[중지] llama-server 종료 중 (PID: $pid)..."

    # SIGTERM으로 graceful shutdown 시도
    kill -TERM "$pid" 2>/dev/null || true

    # 최대 10초 대기
    local count=0
    while [ $count -lt 10 ]; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            echo "[완료] llama-server가 정상적으로 종료되었습니다"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    # 여전히 실행 중이면 강제 종료
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "[경고] 강제 종료 중..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi

    rm -f "$PID_FILE"
    echo "[완료] llama-server가 종료되었습니다"
}

function restart_server() {
    echo "[재시작] llama-server 재시작 중..."
    stop_server
    sleep 2
    start_server
}

function status_server() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "[상태] llama-server 실행 중"
        echo "  PID: $pid"
        echo "  URL: http://$SERVER_HOST:$SERVER_PORT"
        echo ""

        # 메모리 사용량 표시
        if command -v ps &> /dev/null; then
            echo "[리소스]"
            ps -p "$pid" -o pid,ppid,%cpu,%mem,vsz,rss,cmd 2>/dev/null || true
        fi

        # Health check
        echo ""
        echo "[Health Check]"
        if curl -s "http://$SERVER_HOST:$SERVER_PORT/health" > /dev/null 2>&1; then
            echo "  ✓ 서버 응답 정상"
        else
            echo "  ✗ 서버 응답 없음 (시작 중일 수 있음)"
        fi
    else
        echo "[상태] llama-server가 실행 중이 아닙니다"
        return 1
    fi
}

function cleanup_orphans() {
    echo "[정리] 고아 llama-server 프로세스 검색 중..."

    # llama-server 프로세스 검색
    local orphans=$(pgrep -f "llama-server.*$MODEL_PATH" || true)

    if [ -z "$orphans" ]; then
        echo "[완료] 고아 프로세스 없음"
        return 0
    fi

    echo "[발견] 고아 프로세스: $orphans"
    for pid in $orphans; do
        # PID 파일과 일치하지 않으면 고아 프로세스
        if [ -f "$PID_FILE" ]; then
            local registered_pid=$(cat "$PID_FILE")
            if [ "$pid" == "$registered_pid" ]; then
                continue  # 정상 프로세스
            fi
        fi

        echo "[종료] 고아 프로세스 종료: $pid"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 1
        kill -KILL "$pid" 2>/dev/null || true
    done

    echo "[완료] 고아 프로세스 정리 완료"
}

# 메인 로직
case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    cleanup)
        cleanup_orphans
        ;;
    *)
        echo "사용법: $0 {start|stop|restart|status|cleanup}"
        echo ""
        echo "명령어:"
        echo "  start    - llama-server 시작"
        echo "  stop     - llama-server 종료"
        echo "  restart  - llama-server 재시작"
        echo "  status   - 현재 상태 확인"
        echo "  cleanup  - 고아 프로세스 정리"
        exit 1
        ;;
esac
