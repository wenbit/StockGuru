#!/bin/bash

# StockGuru 停止脚本

echo "🛑 停止 StockGuru 服务..."
echo ""

# 停止后端
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✅ 后端已停止 (PID: $BACKEND_PID)"
    else
        echo "⚠️  后端进程不存在"
    fi
    rm .backend.pid
else
    echo "⚠️  未找到后端 PID 文件"
fi

# 停止前端
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        echo "✅ 前端已停止 (PID: $FRONTEND_PID)"
    else
        echo "⚠️  前端进程不存在"
    fi
    rm .frontend.pid
else
    echo "⚠️  未找到前端 PID 文件"
fi

echo ""
echo "🎉 所有服务已停止"
