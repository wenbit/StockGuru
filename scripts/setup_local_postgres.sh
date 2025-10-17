#!/bin/bash
# 安装和配置本地 PostgreSQL 测试环境

set -e  # 遇到错误立即退出

echo "🚀 本地 PostgreSQL 测试环境安装"
echo "================================"
echo ""

# 1. 检查是否已安装
echo "📦 步骤 1/6: 检查 PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL 已安装: $(psql --version)"
else
    echo "⏳ PostgreSQL 未安装，开始安装..."
    brew install postgresql@15
    echo "✅ PostgreSQL 安装完成"
fi
echo ""

# 2. 启动服务
echo "🔄 步骤 2/6: 启动 PostgreSQL 服务..."
brew services start postgresql@15
sleep 3
echo "✅ PostgreSQL 服务已启动"
echo ""

# 3. 创建测试数据库
echo "📊 步骤 3/6: 创建测试数据库..."
if psql -lqt | cut -d \| -f 1 | grep -qw stockguru_test; then
    echo "⚠️  数据库 stockguru_test 已存在，删除重建..."
    dropdb stockguru_test
fi
createdb stockguru_test
echo "✅ 数据库 stockguru_test 创建成功"
echo ""

# 4. 导入表结构
echo "📝 步骤 4/6: 导入表结构..."
psql stockguru_test < stockguru-web/database/daily_stock_data_schema.sql
echo "✅ 表结构导入成功"
echo ""

# 5. 验证表结构
echo "🔍 步骤 5/6: 验证表结构..."
psql stockguru_test -c "\dt" | grep daily_stock_data
echo "✅ 表结构验证成功"
echo ""

# 6. 显示连接信息
echo "📋 步骤 6/6: 配置完成"
echo "================================"
echo ""
echo "✅ 本地 PostgreSQL 测试环境已就绪！"
echo ""
echo "📊 数据库信息:"
echo "  数据库名: stockguru_test"
echo "  连接URL: postgresql://localhost/stockguru_test"
echo "  用户名: $(whoami)"
echo ""
echo "🔧 环境变量配置:"
echo "  export DATABASE_URL='postgresql://localhost/stockguru_test'"
echo ""
echo "🧪 测试命令:"
echo "  # 1. 设置环境变量"
echo "  export DATABASE_URL='postgresql://localhost/stockguru_test'"
echo ""
echo "  # 2. 重启后端服务（使用新数据库）"
echo "  cd stockguru-web/backend"
echo "  pkill -f uvicorn"
echo "  uvicorn app.main:app --reload --port 8000 &"
echo ""
echo "  # 3. 运行测试"
echo "  curl -X POST 'http://localhost:8000/api/v1/daily/sync' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"sync_date\": \"2025-10-10\"}'"
echo ""
echo "💡 查看数据:"
echo "  psql stockguru_test -c 'SELECT COUNT(*) FROM daily_stock_data;'"
echo ""
echo "🎉 安装完成！"
