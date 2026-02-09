@echo off
chcp 65001 >nul 2>&1
title 健康资讯聚合平台 - 运行中
color 0A

cd /d "%~dp0"

:: 设置便携版 Node.js 路径（如果有的话）
if exist "node_portable" (
    for /d %%i in (node_portable\node-*) do set "PATH=%%i;%%PATH%%"
)

:: 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未找到 Node.js，请先运行 "一键安装.bat"
    pause
    exit /b 1
)

:: 检查依赖
if not exist "node_modules" (
    echo.
    echo [提示] 尚未安装依赖，请先运行 "一键安装.bat"
    pause
    exit /b 1
)

:: 创建数据目录
if not exist "data" mkdir data

echo.
echo ============================================
echo    健康资讯聚合平台 v1.0.0
echo ============================================
echo.
echo  启动中，请稍候...
echo.

:: 2秒后自动打开浏览器
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:3000"

echo  ┌──────────────────────────────────────┐
echo  │                                      │
echo  │  电脑浏览器访问:                      │
echo  │  http://localhost:3000               │
echo  │                                      │
echo  │  手机访问 (同一Wi-Fi):                │

:: 显示局域网 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "IP=%%a"
    set "IP=!IP: =!"
)
setlocal enabledelayedexpansion
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr "192.168"') do (
    set "LANIP=%%a"
    call set "LANIP=%%LANIP: =%%"
    echo  │  http://!LANIP!:3000               │
)
endlocal

echo  │                                      │
echo  │  关闭此窗口即可停止服务               │
echo  └──────────────────────────────────────┘
echo.

:: 启动服务
node server/index.js

pause
