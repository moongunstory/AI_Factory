@echo off
chcp 65001 > nul
cls

:menu
echo.
echo ========================================
echo    AI Shorts Factory - Start Menu
echo ========================================
echo.
echo    1. 전체 실행 (프론트엔드 + 백엔드 + 워커)
echo    2. 개발 모드 (백엔드 + 워커만)
echo    3. 백엔드 서버만
echo    4. 워커만
echo    5. 프론트엔드 앱만
echo    0. 종료
echo.
echo ========================================
echo.

set /p choice="선택하세요 (0-5): "

if "%choice%"=="1" goto full
if "%choice%"=="2" goto dev
if "%choice%"=="3" goto backend
if "%choice%"=="4" goto worker
if "%choice%"=="5" goto frontend
if "%choice%"=="0" goto end
echo 잘못된 선택입니다.
timeout /t 2 /nobreak > nul
goto menu

:full
echo.
echo ========================================
echo    전체 실행 모드
echo ========================================
echo.
cd /d "%~dp0"

echo [1/3] Starting Backend Server (port 8000)...
start /min "Backend Server" cmd /k ".venv\Scripts\activate && python -m backend.main"
timeout /t 2 /nobreak > nul

echo [2/3] Starting Worker Process...
start /min "Worker Process" cmd /k ".venv\Scripts\activate && python -m worker.main"
timeout /t 2 /nobreak > nul

echo [3/3] Starting Frontend Server (port 3000)...
start /min "Frontend Server" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo Waiting for servers to be ready...
timeout /t 10 /nobreak > nul

echo Opening browser...
start http://localhost:3000

echo.
echo ========================================
echo    All services started!
echo ========================================
echo.
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
goto end

:dev
echo.
echo ========================================
echo    개발 모드 (백엔드 + 워커)
echo ========================================
echo.
cd /d "%~dp0"

echo [1/2] Starting Backend Server (port 8000)...
start "Backend Server" cmd /k ".venv\Scripts\activate && python -m backend.main"
timeout /t 2 /nobreak > nul

echo [2/2] Starting Worker Process...
start "Worker Process" cmd /k ".venv\Scripts\activate && python -m worker.main"

echo.
echo ========================================
echo    Backend and Worker started!
echo ========================================
echo.
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
goto end

:backend
echo.
echo ========================================
echo    백엔드 서버만 실행
echo ========================================
echo.
cd /d "%~dp0"

echo Starting Backend Server (port 8000)...
.venv\Scripts\activate && python -m backend.main
pause
goto end

:worker
echo.
echo ========================================
echo    워커 프로세스만 실행
echo ========================================
echo.
cd /d "%~dp0"

echo Worker will watch: .data/queue/pending/
echo Press Ctrl+C to stop
echo.
.venv\Scripts\activate && python -m worker.main
pause
goto end

:frontend
echo.
echo ========================================
echo    프론트엔드만 실행
echo ========================================
echo.
cd /d "%~dp0\frontend"

echo Starting Frontend Server (port 3000)...
start /min "Frontend Server" cmd /k "npm run dev"

echo.
echo Waiting for server...
timeout /t 5 /nobreak > nul

echo Opening browser...
start http://localhost:3000
pause
goto end

:end
echo.
echo 프로그램을 종료합니다.
timeout /t 2 /nobreak > nul
exit
