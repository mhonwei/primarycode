@echo off
chcp 65001 >nul 2>&1
title 健康资讯聚合平台 - 一键安装
color 0A

echo.
echo ============================================
echo    健康资讯聚合平台 - 一键安装程序
echo ============================================
echo.

:: 检查是否在正确的目录
if not exist "%~dp0package.json" (
    echo [错误] 找不到 package.json 文件
    echo 请确保此 .bat 文件在项目根目录中
    pause
    exit /b 1
)

cd /d "%~dp0"

:: ===== 第1步：检查 Node.js =====
echo [1/3] 正在检查 Node.js 环境...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  未检测到 Node.js，正在下载便携版 Node.js...
    echo  这可能需要几分钟，请耐心等待...
    echo.

    :: 创建 node_portable 目录
    if not exist "node_portable" mkdir node_portable

    :: 使用 PowerShell 下载 Node.js 便携版
    echo  正在下载 Node.js v20.11.0 便携版...
    powershell -Command "& {$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://npmmirror.com/mirrors/node/v20.11.0/node-v20.11.0-win-x64.zip' -OutFile 'node_portable\node.zip' -TimeoutSec 300 } catch { Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip' -OutFile 'node_portable\node.zip' -TimeoutSec 300 }}"

    if not exist "node_portable\node.zip" (
        echo.
        echo [错误] Node.js 下载失败，请检查网络连接
        echo 你也可以手动下载安装 Node.js: https://nodejs.org
        pause
        exit /b 1
    )

    echo  正在解压 Node.js...
    powershell -Command "& {Expand-Archive -Path 'node_portable\node.zip' -DestinationPath 'node_portable' -Force}"
    del "node_portable\node.zip" >nul 2>&1

    :: 找到解压后的目录
    for /d %%i in (node_portable\node-*) do set "NODE_DIR=%%i"

    echo  Node.js 便携版已安装到: %NODE_DIR%
    set "PATH=%NODE_DIR%;%PATH%"
) else (
    for /f "tokens=*" %%i in ('node --version') do echo  已检测到 Node.js %%i
)

:: 如果有便携版 Node.js，设置 PATH
if exist "node_portable" (
    for /d %%i in (node_portable\node-*) do set "PATH=%%i;%%PATH%%"
)

echo  [OK] Node.js 环境就绪
echo.

:: ===== 第2步：安装依赖 =====
echo [2/3] 正在安装项目依赖（首次较慢，请耐心等待）...
echo  使用淘宝镜像加速下载...

call npm install --registry=https://registry.npmmirror.com 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  镜像源安装失败，尝试默认源...
    call npm install 2>&1
)

if not exist "node_modules" (
    echo.
    echo [错误] 依赖安装失败，请检查网络连接后重试
    pause
    exit /b 1
)

echo  [OK] 依赖安装完成
echo.

:: ===== 第3步：初始化数据库 =====
echo [3/3] 正在初始化数据库...
if not exist "data" mkdir data
echo  [OK] 数据目录已就绪
echo.

:: ===== 安装完成 =====
echo ============================================
echo    安装完成！
echo ============================================
echo.
echo  双击 "启动程序.bat" 即可运行
echo  或者现在就启动？
echo.
set /p START_NOW="  是否立即启动？(Y/N): "
if /i "%START_NOW%"=="Y" (
    call "%~dp0启动程序.bat"
)

pause
