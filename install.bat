@echo off
chcp 65001 >nul 2>&1
title Health News - Install
color 0A

cd /d "%~dp0"

echo.
echo ============================================
echo    Health News Aggregator - Install
echo ============================================
echo.

if not exist "package.json" (
    echo [ERROR] package.json not found.
    echo Please make sure this bat file is in the project root folder.
    pause
    exit /b 1
)

echo [1/3] Checking Node.js ...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  Node.js not found. Downloading portable version...
    echo  This may take a few minutes...
    echo.
    powershell -ExecutionPolicy Bypass -File "scripts\download-node.ps1"
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Node.js download failed.
        echo Please install Node.js manually from https://nodejs.org
        pause
        exit /b 1
    )
)

if exist "node_portable" (
    for /d %%i in (node_portable\node-*) do set "PATH=%%i;%PATH%"
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is still not available.
    echo Please install it manually from https://nodejs.org
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version') do echo  Node.js %%v OK
echo.

echo [2/3] Installing dependencies (using China mirror) ...
call npm install --registry=https://registry.npmmirror.com 2>&1
if not exist "node_modules" (
    echo  Mirror failed, trying default source...
    call npm install 2>&1
)

if not exist "node_modules" (
    echo [ERROR] npm install failed. Check your network.
    pause
    exit /b 1
)

echo  Dependencies OK
echo.

echo [3/3] Creating data folder ...
if not exist "data" mkdir data
echo  Done.
echo.

echo ============================================
echo    Install Complete!
echo ============================================
echo.
echo  Next steps:
echo    1. Double-click "start.bat" to launch
echo    2. Double-click "fetch-news.bat" to get news
echo.

set /p STARTNOW="  Start now? (Y/N): "
if /i "%STARTNOW%"=="Y" call "%~dp0start.bat"

pause
