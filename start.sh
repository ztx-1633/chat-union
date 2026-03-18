#!/bin/bash

# Chat-Union 启动脚本

set -e

echo "========================================="
echo "  Chat-Union 启动脚本"
echo "========================================="

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3.8+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📦 安装/更新依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
fi

echo ""
echo "🚀 启动 Chat-Union 后端服务..."
echo "📱 访问地址: http://localhost:8000"
echo "💬 聊天界面: http://localhost:8000/frontend/index.html"
echo "⚙️  管理控制台: http://localhost:8000/frontend/admin.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================="
echo ""

# 启动后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
