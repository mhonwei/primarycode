@echo off
chcp 65001 >nul 2>&1
title Fetch Health News
color 0B

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
echo    Fetching latest health news ...
echo    Please wait ...
echo ============================================
echo.

node server/scripts/run-aggregation.js

echo.
echo ============================================
echo    Done! Run start.bat to view.
echo ============================================
echo.
pause
