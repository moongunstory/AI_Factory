@echo off
echo ========================================
echo Starting FastAPI Server (Job Queue Mode)
echo ========================================
echo.

cd backend
python -m uvicorn main:app --reload --port 8000

pause
