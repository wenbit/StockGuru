#!/bin/bash

echo "=========================================="
echo "StockGuru CLI 工具安装"
echo "=========================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 安装 Click
echo ""
echo "安装依赖..."
pip3 install click requests

# 创建可执行文件
echo ""
echo "设置可执行权限..."
chmod +x cli.py

# 创建符号链接 (可选)
if [ -w /usr/local/bin ]; then
    echo ""
    echo "创建全局命令..."
    ln -sf "$(pwd)/cli.py" /usr/local/bin/stockguru
    echo "✓ 已创建全局命令: stockguru"
else
    echo ""
    echo "⚠️  无法创建全局命令 (需要 sudo 权限)"
    echo "你可以使用: ./cli.py 来运行命令"
    echo "或手动创建链接: sudo ln -s $(pwd)/cli.py /usr/local/bin/stockguru"
fi

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  stockguru --help          # 查看帮助"
echo "  stockguru status          # 检查系统状态"
echo "  stockguru screen          # 运行筛选"
echo "  stockguru history         # 查看历史"
echo "  stockguru web             # 打开 Web 界面"
echo ""
