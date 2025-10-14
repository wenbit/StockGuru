#!/bin/bash

# StockGuru 诊断脚本

echo "🔍 StockGuru 系统诊断..."
echo ""

# 1. 检查后端进程
echo "📦 1. 检查后端进程"
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "✅ 后端进程运行中 (PID: $BACKEND_PID)"
    else
        echo "❌ 后端进程不存在"
    fi
else
    echo "❌ 未找到后端 PID 文件"
fi
echo ""

# 2. 检查前端进程
echo "📦 2. 检查前端进程"
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "✅ 前端进程运行中 (PID: $FRONTEND_PID)"
    else
        echo "❌ 前端进程不存在"
    fi
else
    echo "❌ 未找到前端 PID 文件"
fi
echo ""

# 3. 测试后端健康检查
echo "📦 3. 测试后端 API"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "✅ 后端健康检查通过"
    echo "   响应: $HEALTH"
else
    echo "❌ 后端健康检查失败"
    echo "   后端可能未启动或启动失败"
fi
echo ""

# 4. 测试前端
echo "📦 4. 测试前端服务"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务不可用"
fi
echo ""

# 5. 测试筛选 API
echo "📦 5. 测试筛选 API"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/screening \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-10-13"}' 2>&1)

if echo "$RESPONSE" | grep -q "task_id"; then
    echo "✅ 筛选 API 正常"
    echo "   响应: $(echo $RESPONSE | python3 -m json.tool 2>/dev/null || echo $RESPONSE)"
else
    echo "❌ 筛选 API 异常"
    echo "   响应: $RESPONSE"
fi
echo ""

# 6. 检查后端日志错误
echo "📦 6. 检查后端日志（最近10行）"
if [ -f "stockguru-web/backend/backend.log" ]; then
    echo "---"
    tail -10 stockguru-web/backend/backend.log
    echo "---"
else
    echo "⚠️  未找到后端日志文件"
fi
echo ""

# 7. 检查 Python 环境
echo "📦 7. 检查 Python 环境"
cd stockguru-web/backend
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境存在"
    echo "   Python: $(python --version)"
    echo "   pip: $(pip --version | head -1)"
else
    echo "❌ 虚拟环境不存在"
fi
cd ../..
echo ""

# 8. 总结
echo "🎯 诊断总结"
echo "---"
echo "如果所有检查都通过，系统应该正常工作。"
echo "如果有失败项，请查看对应的错误信息。"
echo ""
echo "常用命令:"
echo "  重启服务: ./stop-all.sh && ./start-all.sh"
echo "  查看日志: tail -f stockguru-web/backend/backend.log"
echo "  测试系统: ./test-system.sh"
echo ""
