@echo off
echo ========================================
echo Starting AI Factory (Server + Worker)
echo ========================================
echo.

start "FastAPI Server" cmd /k "cd backend && python -m uvicorn main:app --reload --port 8000"
timeout /t 2 /nobreak > nul

start "Worker Process" cmd /k "python -m worker.main"

echo.
echo ========================================
echo Server and Worker started in separate windows
echo Close this window to keep them running
echo ========================================
pause
