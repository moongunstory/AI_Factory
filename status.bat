@echo off
REM ==========================================
REM AI Short Factory - Check Service Status
REM ==========================================

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "PY_MANAGER=%PROJECT_DIR%src\manage_server.py"

echo.
python "%PY_MANAGER%" status
echo.
pause
