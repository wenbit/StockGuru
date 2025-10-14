#!/bin/bash

echo "🔍 验证 Python 环境和依赖安装..."
echo ""

# 激活虚拟环境
source venv/bin/activate

# 1. 检查 Python 版本
echo "📦 Python 版本:"
python --version
echo ""

# 2. 检查关键依赖
echo "📦 关键依赖包:"
pip list | grep -E "fastapi|uvicorn|pydantic|supabase|pandas|numpy|akshare|pywencai"
echo ""

# 3. 检查是否所有依赖都已安装
echo "📦 检查 requirements.txt 中的所有包..."
MISSING=0
while IFS= read -r line; do
    # 跳过空行和注释
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    
    # 提取包名（去掉版本号）
    PACKAGE=$(echo "$line" | sed 's/[>=<].*//' | sed 's/\[.*//')
    
    if pip show "$PACKAGE" &> /dev/null; then
        echo "✅ $PACKAGE"
    else
        echo "❌ $PACKAGE (未安装)"
        MISSING=$((MISSING + 1))
    fi
done < requirements.txt

echo ""

if [ $MISSING -eq 0 ]; then
    echo "🎉 所有依赖已成功安装！"
    echo ""
    echo "下一步："
    echo "1. 激活虚拟环境: source venv/bin/activate"
    echo "2. 启动服务: uvicorn app.main:app --reload"
    echo "3. 访问 API: http://localhost:8000/docs"
else
    echo "⚠️  有 $MISSING 个包未安装"
    echo "请运行: pip install -r requirements.txt"
fi

echo ""
