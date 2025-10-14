#!/bin/bash

# API 测试脚本

echo "🧪 测试 StockGuru API..."
echo ""

# 检查服务是否运行
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ 服务未运行"
    echo "请先启动服务: ./start.sh"
    exit 1
fi

echo "✅ 服务正在运行"
echo ""

# 测试健康检查
echo "📍 测试健康检查..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# 测试根路径
echo "📍 测试根路径..."
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

echo "🎉 API 测试完成！"
echo ""
echo "访问完整 API 文档: http://localhost:8000/docs"
