#!/bin/bash

# StockGuru 系统测试脚本

echo "🧪 测试 StockGuru 系统..."
echo ""

# 1. 测试后端
echo "📦 测试 1/3: 后端 API"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    if [ "$HEALTH" = "healthy" ]; then
        echo "✅ 后端健康检查通过"
    else
        echo "❌ 后端健康检查失败"
        exit 1
    fi
else
    echo "❌ 后端未运行"
    echo "   请运行: ./start-all.sh"
    exit 1
fi
echo ""

# 2. 测试前端
echo "📦 测试 2/3: 前端服务"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端未运行"
    echo "   请运行: ./start-all.sh"
    exit 1
fi
echo ""

# 3. 测试 API 端点
echo "📦 测试 3/3: API 端点"

# 测试根路径
ROOT=$(curl -s http://localhost:8000/)
if echo "$ROOT" | grep -q "StockGuru"; then
    echo "✅ 根路径正常"
else
    echo "⚠️  根路径响应异常"
fi

# 测试 API 文档
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ API 文档可访问"
else
    echo "⚠️  API 文档不可访问"
fi

echo ""
echo "🎉 系统测试完成！"
echo ""
echo "访问地址:"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000/docs"
echo ""
