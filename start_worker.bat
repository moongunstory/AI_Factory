@echo off
echo ========================================
echo Starting AI Factory Worker
echo ========================================
echo.
echo Worker will watch: queue/pending/
echo Press Ctrl+C to stop
echo.

python -m worker.main

pause
