#!/bin/bash
# 健康内容网络爬虫系统 - Linux/Mac 启动脚本

echo "=========================================="
echo "  健康内容网络爬虫系统"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到 Python3，请先安装 Python 3.7 或更高版本"
    exit 1
fi

echo "正在检查依赖..."
echo ""

# 检查是否已安装依赖
if ! python3 -c "import requests" &> /dev/null; then
    echo "正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

echo ""
echo "正在启动应用程序..."
echo ""

# 启动应用
python3 main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "错误: 应用程序启动失败"
    exit 1
fi
