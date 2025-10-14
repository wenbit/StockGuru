#!/bin/bash

# Python 3.12 环境设置脚本

set -e  # 遇到错误立即退出

echo "🚀 开始设置 Python 3.12 环境..."
echo ""

# 1. 检查是否已安装 Python 3.12
echo "📦 步骤 1/5: 检查 Python 3.12..."
if command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 已安装"
    PYTHON312_PATH=$(which python3.12)
    echo "   路径: $PYTHON312_PATH"
else
    echo "⚠️  Python 3.12 未安装"
    echo "   正在通过 Homebrew 安装..."
    brew install python@3.12
    
    # 添加到 PATH
    if [[ -f "/opt/homebrew/bin/python3.12" ]]; then
        PYTHON312_PATH="/opt/homebrew/bin/python3.12"
    elif [[ -f "/usr/local/bin/python3.12" ]]; then
        PYTHON312_PATH="/usr/local/bin/python3.12"
    else
        echo "❌ Python 3.12 安装失败"
        exit 1
    fi
    echo "✅ Python 3.12 安装完成"
fi

echo ""

# 2. 验证 Python 版本
echo "📦 步骤 2/5: 验证 Python 版本..."
PYTHON_VERSION=$($PYTHON312_PATH --version)
echo "✅ $PYTHON_VERSION"
echo ""

# 3. 创建虚拟环境
echo "📦 步骤 3/5: 创建虚拟环境..."
if [[ -d "venv" ]]; then
    echo "⚠️  虚拟环境已存在，删除旧环境..."
    rm -rf venv
fi

$PYTHON312_PATH -m venv venv
echo "✅ 虚拟环境创建完成"
echo ""

# 4. 激活虚拟环境并安装依赖
echo "📦 步骤 4/5: 安装依赖..."
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

echo "✅ 依赖安装完成"
echo ""

# 5. 验证安装
echo "📦 步骤 5/5: 验证安装..."
python --version
echo ""
echo "已安装的包："
pip list | grep -E "fastapi|uvicorn|pydantic|supabase"
echo ""

echo "🎉 环境设置完成！"
echo ""
echo "下一步："
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 启动服务: uvicorn app.main:app --reload"
echo "3. 访问 API 文档: http://localhost:8000/docs"
echo ""
