@echo off
chcp 65001 > nul
echo ========================================
echo    AI Shorts Factory - Starting...
echo ========================================
echo.

:: 프로젝트 루트 디렉토리로 이동
cd /d "%~dp0"

:: 백엔드 서버 실행 (새 창에서, 최소화)
echo [1/2] Starting Backend Server (port 8000)...
start /min "Backend Server" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python -m backend.main"

:: 잠시 대기 (백엔드가 먼저 시작되도록)
timeout /t 2 /nobreak > nul

:: 프론트엔드 서버 실행 (새 창에서, 최소화)
echo [2/2] Starting Frontend Server (port 3000)...
start /min "Frontend Server" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo    Servers Starting...
echo ========================================
echo.

:: 프론트엔드 서버가 준비될 때까지 대기
echo    Waiting for servers to be ready...
timeout /t 5 /nobreak > nul

:: 브라우저에서 프론트엔드 자동 열기
echo    Opening browser...
start http://localhost:3000

echo.
echo ========================================
echo    App is now running!
echo ========================================
echo.
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo    This window will close in 3 seconds...
timeout /t 3 /nobreak > nul
