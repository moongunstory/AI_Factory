@echo off
REM ==========================================
REM AI Short Factory - Windows GPU Launcher
REM ==========================================

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "LLAMA_MANAGER=%PROJECT_DIR%llama_server_manager.ps1"
set "FLASK_APP=%PROJECT_DIR%src\web\app.py"

echo.
echo ==========================================
echo  AI Short Factory - Windows GPU Edition
echo ==========================================
echo.

REM ==========================================
REM 1. Check Dependencies
REM ==========================================

echo [1/4] Checking dependencies...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Python packages
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
)

REM Check model file
set "MODEL_PATH=%PROJECT_DIR%models\solar-10.7b\solar-10.7b-instruct-v1.0.Q6_K.gguf"
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found: %MODEL_PATH%
    echo Please download the model file first.
    pause
    exit /b 1
)
echo [OK] Model file found
echo.

REM Check llama-server
set "LLAMA_SERVER=%PROJECT_DIR%engine\llama.cpp\build\bin\Release\llama-server.exe"
if not exist "%LLAMA_SERVER%" (
    echo [ERROR] llama-server not found: %LLAMA_SERVER%
    echo Please build llama.cpp first.
    pause
    exit /b 1
)
echo [OK] llama-server found
echo.

REM ==========================================
REM 2. Clean up orphan processes
REM ==========================================

echo [2/4] Cleaning up previous processes...
powershell -ExecutionPolicy Bypass -File "%LLAMA_MANAGER%" -Action cleanup >nul 2>&1
echo [OK] Cleanup complete
echo.

REM ==========================================
REM 3. Start llama-server
REM ==========================================

echo [3/4] Starting llama-server with GPU support...
echo.

REM Check if already running
powershell -ExecutionPolicy Bypass -File "%LLAMA_MANAGER%" -Action status >nul 2>&1
if errorlevel 1 (
    powershell -ExecutionPolicy Bypass -File "%LLAMA_MANAGER%" -Action start
) else (
    echo [OK] llama-server already running
)
echo.

REM ==========================================
REM 4. Start Flask Web UI
REM ==========================================

echo [4/4] Starting Flask Web UI...
echo.
echo ==========================================
echo  AI Short Factory Running
echo ==========================================
echo  Web UI: http://localhost:5000
echo  llama-server: http://localhost:8080
echo.
echo  Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Open browser after 2 seconds
start /min cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

REM Start Flask
python "%FLASK_APP%"

REM If Flask exits, show message
echo.
echo [INFO] Flask has stopped.
echo [INFO] llama-server is still running in the background.
echo [INFO] To stop llama-server, run:
echo        powershell -ExecutionPolicy Bypass -File llama_server_manager.ps1 -Action stop
echo.
pause
