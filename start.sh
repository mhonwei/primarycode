#!/bin/bash

echo "======================================"
echo "AI案例智库系统 - 启动脚本"
echo "======================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.9+"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到Node.js，请先安装Node.js 16+"
    exit 1
fi

echo ""
echo "📦 检查依赖..."

# 后端依赖
if [ ! -d "backend/venv" ]; then
    echo "创建Python虚拟环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# 前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "🚀 启动服务..."

# 启动后端
echo "启动后端服务 (端口 5000)..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务 (端口 3000)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "✅ 服务已启动！"
echo "======================================"
echo ""
echo "后端服务: http://localhost:5000"
echo "前端应用: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
wait

# 清理
echo ""
echo "🛑 停止服务..."
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "服务已停止"
