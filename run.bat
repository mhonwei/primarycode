@echo off
REM 健康内容网络爬虫系统 - Windows 启动脚本

echo ==========================================
echo   健康内容网络爬虫系统
echo ==========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到 Python，请先安装 Python 3.7 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在检查依赖...
echo.

REM 检查是否已安装依赖
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 正在启动应用程序...
echo.

REM 启动应用
python main.py

if %errorlevel% neq 0 (
    echo.
    echo 错误: 应用程序启动失败
    pause
    exit /b 1
)

pause
