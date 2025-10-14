#!/bin/bash

echo "🔍 检查前端项目状态..."
echo ""

if [ -d "frontend" ]; then
    echo "✅ frontend 目录已创建"
    echo ""
    
    if [ -f "frontend/package.json" ]; then
        echo "✅ package.json 存在"
        echo ""
        
        if [ -d "frontend/node_modules" ]; then
            echo "✅ node_modules 已安装"
            echo ""
            echo "🎉 前端项目创建完成！"
            echo ""
            echo "下一步："
            echo "1. cd frontend"
            echo "2. npm run dev"
            echo "3. 访问 http://localhost:3000"
        else
            echo "⏳ 依赖正在安装中..."
            echo "   请稍候..."
        fi
    else
        echo "⏳ 项目正在初始化..."
    fi
else
    echo "⏳ 项目正在创建中..."
    echo ""
    echo "检查进程:"
    ps aux | grep -E "npm|npx|create-next-app" | grep -v grep | head -5
fi

echo ""
