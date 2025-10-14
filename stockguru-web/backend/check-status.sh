#!/bin/bash

echo "🔍 检查 Python 3.12 安装状态..."
echo ""

# 检查 Homebrew 安装进程
if pgrep -f "brew install python" > /dev/null; then
    echo "⏳ Homebrew 正在安装 Python 3.12..."
    echo "   请稍候..."
else
    echo "✅ 安装进程已完成或未运行"
fi

echo ""

# 检查 Python 3.12 是否可用
if command -v python3.12 &> /dev/null; then
    echo "✅ Python 3.12 已安装"
    python3.12 --version
    echo "   路径: $(which python3.12)"
    echo ""
    echo "🎉 可以继续执行设置脚本了！"
    echo "   运行: ./setup-python312.sh"
else
    echo "⏳ Python 3.12 尚未安装完成"
    echo ""
    echo "请等待 Homebrew 安装完成，然后运行："
    echo "   brew install python@3.12"
fi

echo ""
