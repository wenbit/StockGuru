#!/bin/bash

# StockGuru 后端启动脚本

echo "🚀 启动 StockGuru 后端服务..."
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在！"
    echo "请先运行: ./setup-python312.sh"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 验证 Python 版本
PYTHON_VERSION=$(python --version)
echo "✅ $PYTHON_VERSION"
echo ""

# 检查依赖
echo "📦 检查关键依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  依赖未安装，正在安装..."
    pip install -r requirements.txt
fi

echo "✅ 依赖检查完成"
echo ""

# 启动服务
echo "🌐 启动 FastAPI 服务..."
echo "📍 API 文档: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
