# llama-server 관리 스크립트 (Windows GPU 지원)
# PowerShell 7.0+ 권장

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'cleanup')]
    [string]$Action = 'status'
)

$ErrorActionPreference = "Stop"

# 프로젝트 경로 설정
$PROJECT_DIR = $PSScriptRoot
$PID_FILE     = Join-Path $PROJECT_DIR "output\logs\.llama_server.pid"
$OUT_LOG_FILE = Join-Path $PROJECT_DIR "output\logs\llama_server.out.log"
$ERR_LOG_FILE = Join-Path $PROJECT_DIR "output\logs\llama_server.err.log"
$MODEL_PATH = Join-Path $PROJECT_DIR "models\solar-10.7b\solar-10.7b-instruct-v1.0.Q6_K.gguf"
$LLAMA_SERVER = Join-Path $PROJECT_DIR "engine\llama.cpp\build\bin\Release\llama-server.exe"

# 로그 디렉토리 생성
$LOG_DIR = Split-Path -Parent $OUT_LOG_FILE
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

# 서버 설정
$SERVER_HOST = "127.0.0.1"
$SERVER_PORT = 8080

# GPU 지원 llama-server 파라미터
# -ngl -1 = 모든 레이어를 GPU에 로드 (CUDA 사용)
$LLAMA_PARAMS = @(
    "--host", $SERVER_HOST,
    "--port", $SERVER_PORT,
    "--model", $MODEL_PATH,
    "--ctx-size", "4096",           # GPU: 더 큰 컨텍스트
    "--batch-size", "2048",         # GPU: 큰 배치 크기
    "--threads", "4",               # GPU 환경: CPU 스레드 적게
    "--n-gpu-layers", "-1",         # 모든 레이어를 GPU에 로드
    "--parallel", "8",              # 동시 요청 처리
    "--cont-batching",              # Continuous batching 활성화
    "--flash-attn"                  # Flash Attention 활성화 (속도 향상)
)

function Test-ServerRunning {
    if (Test-Path $PID_FILE) {
        $pid = Get-Content $PID_FILE -ErrorAction SilentlyContinue
        if ($pid) {
            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                return $true
            } catch {
                Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
            }
        }
    }
    return $false
}

function Start-LlamaServer {
    if (Test-ServerRunning) {
        $pid = Get-Content $PID_FILE
        Write-Host "[경고] llama-server 이미 실행 중 (PID: $pid)" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $MODEL_PATH)) {
        Write-Host "[오류] 모델 파일 없음: $MODEL_PATH" -ForegroundColor Red
        exit 1
    }

    if (-not (Test-Path $LLAMA_SERVER)) {
        Write-Host "[오류] llama-server 실행 파일 없음: $LLAMA_SERVER" -ForegroundColor Red
        Write-Host "        llama.cpp를 빌드하거나 경로를 확인하세요." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host " llama-server 시작 (GPU 가속)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "모델: $(Split-Path -Leaf $MODEL_PATH)" -ForegroundColor Green
    Write-Host "포트: $SERVER_PORT" -ForegroundColor Green
    Write-Host "GPU 레이어: 모두 (-1)" -ForegroundColor Green
    Write-Host "Context: 4096 tokens" -ForegroundColor Green
    Write-Host "Batch: 2048" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan

    # llama-server 실행
    $process = Start-Process -FilePath $LLAMA_SERVER `
        -ArgumentList $LLAMA_PARAMS `
        -RedirectStandardOutput $OUT_LOG_FILE `
        -RedirectStandardError $ERR_LOG_FILE `
        -PassThru `
        -WindowStyle Hidden

    $process.Id | Out-File $PID_FILE -Encoding UTF8

    Write-Host "[시작] PID $($process.Id)" -ForegroundColor Green
    Write-Host "[stdout 로그] $OUT_LOG_FILE" -ForegroundColor Gray
    Write-Host "[stderr 로그] $ERR_LOG_FILE" -ForegroundColor Gray

    # Health check
    Write-Host "[대기] 서버 준비 중" -NoNewline -ForegroundColor Yellow
    $max_wait = 60
    for ($i = 0; $i -lt $max_wait; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://${SERVER_HOST}:${SERVER_PORT}/health" `
                -TimeoutSec 1 `
                -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host ""
                Write-Host "[완료] llama-server 준비됨!" -ForegroundColor Green
                Write-Host "[URL] http://${SERVER_HOST}:${SERVER_PORT}" -ForegroundColor Cyan
                return
            }
        } catch {
            # 계속 대기
        }
        Write-Host "." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }

    Write-Host ""
    Write-Host "[오류] 60초 동안 서버 응답 없음" -ForegroundColor Red
    Write-Host "[stdout 로그 확인] Get-Content $OUT_LOG_FILE -Tail 20" -ForegroundColor Yellow
    Write-Host "[stderr 로그 확인] Get-Content $ERR_LOG_FILE -Tail 20" -ForegroundColor Yellow
    Stop-LlamaServer
    exit 1
}

function Stop-LlamaServer {
    if (-not (Test-ServerRunning)) {
        Write-Host "[정보] 실행 중인 llama-server 없음" -ForegroundColor Gray
        return
    }

    $pid = Get-Content $PID_FILE
    Write-Host "[중지] llama-server 종료 중 (PID: $pid)" -ForegroundColor Yellow

    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        $process.CloseMainWindow() | Out-Null

        # 정상 종료 대기 (10초)
        for ($i = 0; $i -lt 10; $i++) {
            if ($process.HasExited) {
                Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
                Write-Host "[완료] 정상 종료" -ForegroundColor Green
                return
            }
            Start-Sleep -Seconds 1
        }

        # 강제 종료
        Write-Host "[강제 종료]" -ForegroundColor Red
        Stop-Process -Id $pid -Force
        Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
        Write-Host "[완료] 강제 종료됨" -ForegroundColor Yellow
    } catch {
        Write-Host "[오류] 프로세스 종료 실패: $_" -ForegroundColor Red
        Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
    }
}

function Restart-LlamaServer {
    Write-Host "[재시작]" -ForegroundColor Cyan
    Stop-LlamaServer
    Start-Sleep -Seconds 2
    Start-LlamaServer
}

function Get-ServerStatus {
    if (Test-ServerRunning) {
        $pid = Get-Content $PID_FILE
        Write-Host "[상태] llama-server 실행 중" -ForegroundColor Green
        Write-Host "PID: $pid" -ForegroundColor Gray

        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "CPU: $([math]::Round($process.CPU, 2))s" -ForegroundColor Gray
            Write-Host "메모리: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
        } catch {
            Write-Host "[경고] 프로세스 정보 조회 실패" -ForegroundColor Yellow
        }

        Write-Host ""
        try {
            $response = Invoke-WebRequest -Uri "http://${SERVER_HOST}:${SERVER_PORT}/health" `
                -TimeoutSec 2 `
                -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ Health OK" -ForegroundColor Green
            }
        } catch {
            Write-Host "✗ Health Check 실패" -ForegroundColor Red
        }
    } else {
        Write-Host "[상태] 실행 중 아님" -ForegroundColor Gray
        exit 1
    }
}

function Remove-OrphanProcesses {
    Write-Host "[정리] 고아 llama-server 프로세스 검색" -ForegroundColor Yellow

    $orphans = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue

    if (-not $orphans) {
        Write-Host "[완료] 고아 프로세스 없음" -ForegroundColor Green
        return
    }

    $currentPid = $null
    if (Test-Path $PID_FILE) {
        $currentPid = Get-Content $PID_FILE
    }

    foreach ($process in $orphans) {
        if ($currentPid -and $process.Id -eq $currentPid) {
            continue
        }
        Write-Host "[종료] 고아 PID: $($process.Id)" -ForegroundColor Yellow
        Stop-Process -Id $process.Id -Force
    }

    Write-Host "[완료]" -ForegroundColor Green
}

# 메인 실행
switch ($Action.ToLower()) {
    'start'   { Start-LlamaServer }
    'stop'    { Stop-LlamaServer }
    'restart' { Restart-LlamaServer }
    'status'  { Get-ServerStatus }
    'cleanup' { Remove-OrphanProcesses }
    default   {
        Write-Host "사용법: .\llama_server_manager.ps1 [-Action] {start|stop|restart|status|cleanup}" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "예시:" -ForegroundColor Cyan
        Write-Host "  .\llama_server_manager.ps1 start" -ForegroundColor Gray
        Write-Host "  .\llama_server_manager.ps1 status" -ForegroundColor Gray
        Write-Host "  .\llama_server_manager.ps1 stop" -ForegroundColor Gray
    }
}
