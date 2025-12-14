@echo off
chcp 65001 >nul
REM ========================================
REM Chrome Debug Mode - Failsafe Version
REM ========================================

echo.
echo ========================================
echo Chrome Debug Mode 시작
echo ========================================
echo.

REM Step 1: 사용자에게 Chrome 종료 요청
echo [중요] Chrome을 완전히 종료해야 합니다!
echo.
echo 지금 바로:
echo 1. 모든 Chrome 창 닫기 (X 버튼)
echo 2. 작업 관리자 열기 (Ctrl+Shift+Esc)
echo 3. "Chrome" 검색해서 모든 프로세스 "작업 끝내기"
echo 4. Chrome 프로세스가 완전히 사라졌는지 확인
echo.
pause

echo.
echo [자동 종료 시도 중...]
taskkill /F /IM chrome.exe /T >nul 2>&1
timeout /t 5 /nobreak >nul

REM 프로세스 확인
tasklist /FI "IMAGENAME eq chrome.exe" 2>NUL | find /I /N "chrome.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo.
    echo ⚠️  경고: Chrome 프로세스가 여전히 실행 중입니다!
    echo.
    echo 작업 관리자에서 수동으로 모든 chrome.exe를 종료하고
    echo 아무 키나 눌러 계속하세요.
    echo.
    pause
) else (
    echo ✓ Chrome 프로세스 없음 확인
)

echo.
echo [Chrome Debug Mode 시작...]
echo - 포트: 9222  
echo - 프로필: AutomationProfile
echo.

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data" ^
  --profile-directory=AutomationProfile

echo ✓ Chrome 시작 명령 실행
echo.
echo 5초 대기 중 (Chrome 초기화)...
timeout /t 5 /nobreak >nul

echo.
echo [Debug 포트 확인 중...]
set /a MAX_RETRY=30
set /a RETRY=0

:CHECK_PORT
netstat -ano | findstr :9222 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Debug 포트 9222 활성화 확인!
    goto PORT_OK
)

set /a RETRY+=1
if %RETRY% GEQ %MAX_RETRY% (
    echo.
    echo ❌ 오류: 30초 후에도 포트가 활성화되지 않았습니다.
    echo.
    echo 문제 해결:
    echo 1. Chrome 창을 모두 닫으세요
    echo 2. 이 배치 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo   대기 중... (%RETRY%/%MAX_RETRY%)
timeout /t 1 /nobreak >nul
goto CHECK_PORT

:PORT_OK
echo.
echo ========================================
echo ✅ Chrome Debug Mode 준비 완료!
echo ========================================
echo.
echo 📌 Chrome이 열렸습니다 (AutomationProfile)
echo    chatgpt.com에서 GPT Plus 로그인 후 Enter
echo.
pause

echo.
echo [자동화 테스트 실행 중...]
cd /d "%~dp0"
python worker/debug_workflow_test.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ 테스트 성공!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ 테스트 실패
    echo ========================================
)

echo.
pause
