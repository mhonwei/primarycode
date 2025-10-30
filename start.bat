@echo off
echo ======================================
echo AI案例智库系统 - 启动脚本
echo ======================================

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo.
echo 📦 检查依赖...

REM 后端依赖
if not exist "backend\venv" (
    echo 创建Python虚拟环境...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
)

REM 前端依赖
if not exist "frontend\node_modules" (
    echo 安装前端依赖...
    cd frontend
    call npm install
    cd ..
)

echo.
echo 🚀 启动服务...

REM 启动后端
echo 启动后端服务 (端口 5000)...
cd backend
start "AI案例智库-后端" cmd /k "venv\Scripts\activate && python app.py"
cd ..

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
echo 启动前端服务 (端口 3000)...
cd frontend
start "AI案例智库-前端" cmd /k "npm start"
cd ..

echo.
echo ======================================
echo ✅ 服务已启动！
echo ======================================
echo.
echo 后端服务: http://localhost:5000
echo 前端应用: http://localhost:3000
echo.
echo 请在新打开的窗口中查看服务
echo 关闭窗口即可停止服务
echo.
pause
