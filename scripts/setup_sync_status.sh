#!/bin/bash
# 快速安装同步状态管理系统

echo "=========================================="
echo "安装同步状态管理系统"
echo "=========================================="
echo ""

# 1. 安装依赖
echo "1. 安装Python依赖..."
pip install psutil -q
echo "✅ psutil 已安装"
echo ""

# 2. 初始化数据库表
echo "2. 初始化数据库表..."
python scripts/init_sync_status_table.py
echo ""

# 3. 运行测试
echo "3. 运行功能测试..."
python scripts/test_sync_status.py
echo ""

echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 启动API服务: cd stockguru-web/backend && python -m uvicorn app.main:app --reload"
echo "2. 访问API文档: http://localhost:8000/docs"
echo "3. 查看使用指南: cat docs/SYNC_STATUS_GUIDE.md"
echo ""
