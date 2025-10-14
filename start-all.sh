#!/bin/bash

# StockGuru 一键启动脚本

echo "🚀 启动 StockGuru 全栈应用..."
echo ""

# 检查是否在正确的目录
if [ ! -d "frontend" ] || [ ! -d "stockguru-web/backend" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 启动后端
echo "📦 步骤 1/2: 启动后端..."
cd stockguru-web/backend

if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 setup-python312.sh"
    exit 1
fi

# 在后台启动后端
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

echo "✅ 后端已启动 (PID: $BACKEND_PID)"
echo "   日志: stockguru-web/backend/backend.log"
echo "   API: http://localhost:8000/docs"
echo ""

# 等待后端启动
sleep 3

# 启动前端
echo "📦 步骤 2/2: 启动前端..."
cd ../../frontend

if [ ! -d "node_modules" ]; then
    echo "⚠️  依赖未安装，正在安装..."
    npm install
fi

# 在后台启动前端
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ 前端已启动 (PID: $FRONTEND_PID)"
echo "   日志: frontend/frontend.log"
echo "   URL: http://localhost:3000"
echo ""

# 保存 PID
cd ..
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo "🎉 所有服务已启动！"
echo ""
echo "访问应用:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000/docs"
echo ""
echo "停止服务:"
echo "  ./stop-all.sh"
echo ""
echo "查看日志:"
echo "  tail -f stockguru-web/backend/backend.log"
echo "  tail -f frontend/frontend.log"
echo ""
