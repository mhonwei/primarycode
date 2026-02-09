@echo off
chcp 65001 >nul 2>&1
title 健康资讯 - 数据采集
color 0B

cd /d "%~dp0"

:: 设置便携版 Node.js 路径
if exist "node_portable" (
    for /d %%i in (node_portable\node-*) do set "PATH=%%i;%%PATH%%"
)

:: 检查环境
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先运行 "一键安装.bat"
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [错误] 尚未安装依赖，请先运行 "一键安装.bat"
    pause
    exit /b 1
)

echo.
echo ============================================
echo    正在采集最新健康资讯...
echo    （需要联网，请耐心等待）
echo ============================================
echo.

node server/scripts/run-aggregation.js

echo.
echo ============================================
echo    采集完成！
echo    启动 "启动程序.bat" 即可查看内容
echo ============================================
echo.
pause
