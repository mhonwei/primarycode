@echo off
chcp 65001 >nul 2>&1
title Health News Aggregator
color 0A

cd /d "%~dp0"

if exist "node_portable" (
    for /d %%i in (node_portable\node-*) do set "PATH=%%i;%PATH%"
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Run install.bat first.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [ERROR] Dependencies not installed. Run install.bat first.
    pause
    exit /b 1
)

if not exist "data" mkdir data

echo.
echo ============================================
echo    Health News Aggregator v1.0.0
echo ============================================
echo.
echo  PC:     http://localhost:3000
echo.

setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "192.168"') do (
    set "IP=%%a"
    set "IP=!IP: =!"
    if not "!IP!"=="" (
        echo  Phone:  http://!IP!:3000
    )
)
endlocal

echo.
echo  Browser will open in 3 seconds...
echo  Close this window to stop the server.
echo ============================================
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:3000"

node server/index.js

pause
