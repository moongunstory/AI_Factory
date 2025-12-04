@echo off
REM ==========================================
REM AI Short Factory - Stop All Services
REM ==========================================

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "PY_MANAGER=%PROJECT_DIR%src\manage_server.py"

echo.
echo ==========================================
echo  AI Short Factory - Stopping Services
echo ==========================================
echo.

REM Stop all services
python "%PY_MANAGER%" stop all

echo.
echo ==========================================
echo  All Services Stopped
echo ==========================================
echo.
pause
