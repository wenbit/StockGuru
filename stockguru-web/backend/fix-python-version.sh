#!/bin/bash

# Python 版本修复脚本

echo "🔍 检查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "当前 Python 版本: $PYTHON_VERSION"

# 检查是否是 3.13
if [[ $PYTHON_VERSION == 3.13* ]]; then
    echo "⚠️  检测到 Python 3.13，不兼容 pydantic 2.6"
    echo ""
    echo "解决方案："
    echo ""
    echo "方案1: 使用 pyenv 切换到 Python 3.12"
    echo "  pyenv install 3.12.0"
    echo "  pyenv local 3.12.0"
    echo ""
    echo "方案2: 创建 Python 3.12 虚拟环境"
    echo "  python3.12 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    echo "方案3: 使用 Homebrew 安装 Python 3.12"
    echo "  brew install python@3.12"
    echo "  /opt/homebrew/bin/python3.12 -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    exit 1
elif [[ $PYTHON_VERSION == 3.12* ]] || [[ $PYTHON_VERSION == 3.11* ]]; then
    echo "✅ Python 版本兼容"
    echo ""
    echo "继续安装依赖..."
    pip install -r requirements.txt
else
    echo "⚠️  建议使用 Python 3.11 或 3.12"
    echo "当前版本: $PYTHON_VERSION"
fi
