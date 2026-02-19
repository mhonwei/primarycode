@echo off
chcp 65001 >nul 2>&1
title 打包绿色便携版
color 0E

echo.
echo ============================================
echo   打包"健康资讯"绿色便携版（免安装）
echo ============================================
echo.
echo  此脚本将生成一个独立的文件夹，
echo  包含所有运行所需的文件（含 Node.js），
echo  复制到任意 Windows 电脑上双击即可运行。
echo.

cd /d "%~dp0.."

:: 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 需要 Node.js 环境来执行打包，请先安装
    pause
    exit /b 1
)

set "BUILD_DIR=dist\健康资讯聚合平台"

:: 清理旧的构建
if exist "dist" rmdir /s /q dist
mkdir "%BUILD_DIR%"

echo [1/5] 正在下载 Node.js 便携版...
mkdir "%BUILD_DIR%\runtime"
powershell -Command "& {$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://npmmirror.com/mirrors/node/v20.11.0/node-v20.11.0-win-x64.zip' -OutFile '%BUILD_DIR%\runtime\node.zip' -TimeoutSec 300 } catch { Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip' -OutFile '%BUILD_DIR%\runtime\node.zip' -TimeoutSec 300 }}"

if not exist "%BUILD_DIR%\runtime\node.zip" (
    echo [错误] Node.js 下载失败
    pause
    exit /b 1
)

echo [2/5] 正在解压 Node.js 运行环境...
powershell -Command "& {Expand-Archive -Path '%BUILD_DIR%\runtime\node.zip' -DestinationPath '%BUILD_DIR%\runtime' -Force}"
del "%BUILD_DIR%\runtime\node.zip"

echo [3/5] 正在复制应用程序文件...
xcopy "server" "%BUILD_DIR%\server\" /E /I /Q /Y
xcopy "client" "%BUILD_DIR%\client\" /E /I /Q /Y
xcopy "node_modules" "%BUILD_DIR%\node_modules\" /E /I /Q /Y
copy "package.json" "%BUILD_DIR%\" /Y >nul
mkdir "%BUILD_DIR%\data"

echo [4/5] 正在生成启动器...

:: 生成启动器 bat
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title 健康资讯聚合平台
echo color 0A
echo cd /d "%%~dp0"
echo.
echo :: 设置内置 Node.js 路径
echo for /d %%%%i in ^(runtime\node-*^) do set "PATH=%%%%i;%%%%PATH%%%%"
echo.
echo if not exist "data" mkdir data
echo.
echo echo.
echo echo ============================================
echo echo    健康资讯聚合平台 v1.0.0
echo echo ============================================
echo echo.
echo echo  正在启动，3秒后自动打开浏览器...
echo echo.
echo echo  电脑访问: http://localhost:3000
echo echo.
echo echo  手机访问（同一Wi-Fi下）:
echo setlocal enabledelayedexpansion
echo for /f "tokens=2 delims=:" %%%%a in ^('ipconfig ^^^| findstr /i "IPv4" ^^^| findstr "192.168"'^) do ^(
echo     set "LANIP=%%%%a"
echo     call set "LANIP=%%%%LANIP: =%%%%"
echo     echo  http://!LANIP!:3000
echo ^)
echo endlocal
echo echo.
echo echo  关闭此窗口即可停止服务
echo echo ============================================
echo echo.
echo.
echo start "" cmd /c "timeout /t 3 /nobreak ^>nul ^&^& start http://localhost:3000"
echo node server/index.js
echo pause
) > "%BUILD_DIR%\启动健康资讯.bat"

:: 生成采集数据 bat
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo title 采集健康资讯
echo color 0B
echo cd /d "%%~dp0"
echo for /d %%%%i in ^(runtime\node-*^) do set "PATH=%%%%i;%%%%PATH%%%%"
echo if not exist "data" mkdir data
echo echo.
echo echo 正在采集最新健康资讯，请稍候...
echo echo.
echo node server/scripts/run-aggregation.js
echo echo.
echo echo 采集完成！双击 "启动健康资讯.bat" 查看内容
echo pause
) > "%BUILD_DIR%\采集数据.bat"

echo [5/5] 打包完成！
echo.
echo ============================================
echo  输出目录: dist\健康资讯聚合平台\
echo ============================================
echo.
echo  使用方法:
echo  1. 将 "健康资讯聚合平台" 整个文件夹复制到目标电脑
echo  2. 双击 "采集数据.bat" 获取最新资讯
echo  3. 双击 "启动健康资讯.bat" 启动并查看
echo.
echo  可以压缩成 ZIP 发送给别人使用！
echo.
pause
