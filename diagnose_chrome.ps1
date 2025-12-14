# Chrome Debug 진단 스크립트
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Chrome Debug 진단 시작" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Chrome 프로세스 강제 종료
Write-Host "[1/5] Chrome 프로세스 종료 중..." -ForegroundColor Yellow
Get-Process -Name chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "✓ 완료`n" -ForegroundColor Green

# Step 2: 프로필 잠금 파일 확인 및 제거
Write-Host "[2/5] 프로필 잠금 파일 확인 중..." -ForegroundColor Yellow
$userDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"
$lockFile = Join-Path $userDataDir "Default\lockfile"

if (Test-Path $lockFile) {
    Write-Host "⚠️  잠금 파일 발견: $lockFile" -ForegroundColor Yellow
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    Write-Host "✓ 잠금 파일 제거`n" -ForegroundColor Green
} else {
    Write-Host "✓ 잠금 파일 없음`n" -ForegroundColor Green
}

# Step 3: Chrome 시작 (에러 캡처)
Write-Host "[3/5] Chrome 시작 중..." -ForegroundColor Yellow
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

if (-not (Test-Path $chromePath)) {
    Write-Host "❌ Chrome 실행 파일을 찾을 수 없습니다: $chromePath" -ForegroundColor Red
    pause
    exit 1
}

$arguments = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=`"$userDataDir`"",
    "--profile-directory=Default"
)

try {
    $process = Start-Process -FilePath $chromePath -ArgumentList $arguments -PassThru
    Write-Host "✓ Chrome 프로세스 시작됨 (PID: $($process.Id))`n" -ForegroundColor Green
    
    # Step 4: 프로세스 생존 확인
    Write-Host "[4/5] 프로세스 생존 확인 중..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    $stillAlive = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
    if ($null -eq $stillAlive) {
        Write-Host "❌ Chrome 프로세스가 즉시 종료되었습니다!" -ForegroundColor Red
        Write-Host "   프로필이 손상되었거나 충돌이 발생했을 수 있습니다.`n" -ForegroundColor Red
    } else {
        Write-Host "✓ Chrome이 실행 중입니다 (PID: $($stillAlive.Id))`n" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ Chrome 시작 실패: $_" -ForegroundColor Red
    pause
    exit 1
}

# Step 5: Debug 포트 확인
Write-Host "[5/5] Debug 포트 확인 중..." -ForegroundColor Yellow
$maxRetries = 15
for ($i = 1; $i -le $maxRetries; $i++) {
    Start-Sleep -Seconds 1
    $portOpen = Test-NetConnection -ComputerName localhost -Port 9222 -InformationLevel Quiet -WarningAction SilentlyContinue
    
    if ($portOpen) {
        Write-Host "✓ Debug 포트 9222 활성화 확인!`n" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "✅ 성공! Chrome Debug Mode 준비 완료" -ForegroundColor Green
        Write-Host "========================================`n" -ForegroundColor Cyan
        Write-Host "이제 다음 명령을 실행할 수 있습니다:" -ForegroundColor White
        Write-Host "  python worker/debug_workflow_test.py`n" -ForegroundColor White
        pause
        exit 0
    }
    
    Write-Host "  대기 중... ($i/$maxRetries)" -ForegroundColor Gray
}

Write-Host "`n⚠️  15초 후에도 Debug 포트가 활성화되지 않았습니다." -ForegroundColor Yellow
Write-Host "Chrome이 실행 중이지만 Debug 모드로 시작되지 않았을 수 있습니다.`n" -ForegroundColor Yellow

# 프로세스 목록 표시
Write-Host "현재 Chrome 프로세스:" -ForegroundColor White
Get-Process -Name chrome -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize

pause
