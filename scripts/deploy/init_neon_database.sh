#!/bin/bash
# Neon 数据库初始化脚本
# 用于快速初始化 Neon 数据库结构

set -e  # 遇到错误立即退出

echo "🚀 StockGuru Neon 数据库初始化脚本"
echo "======================================"
echo ""

# 检查是否提供了数据库连接字符串
if [ -z "$1" ]; then
    echo "❌ 错误：请提供 Neon 数据库连接字符串"
    echo ""
    echo "用法："
    echo "  $0 'postgresql://user:password@host/database?sslmode=require'"
    echo ""
    echo "示例："
    echo "  $0 'postgresql://stockguru_owner:npg_xxx@ep-xxx.aws.neon.tech/stockguru?sslmode=require'"
    exit 1
fi

DATABASE_URL="$1"

echo "📊 数据库连接信息："
echo "  URL: ${DATABASE_URL:0:50}..."
echo ""

# 检查 psql 是否安装
if ! command -v psql &> /dev/null; then
    echo "❌ 错误：psql 未安装"
    echo ""
    echo "请安装 PostgreSQL 客户端："
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATABASE_DIR="$PROJECT_ROOT/stockguru-web/database"

echo "📁 项目目录："
echo "  根目录: $PROJECT_ROOT"
echo "  数据库脚本: $DATABASE_DIR"
echo ""

# 测试数据库连接
echo "🔌 测试数据库连接..."
if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ 数据库连接成功"
else
    echo "❌ 数据库连接失败"
    exit 1
fi
echo ""

# 执行数据库脚本
echo "📝 开始执行数据库脚本..."
echo ""

# 1. 创建主表结构
echo "1️⃣  创建主表结构 (daily_stock_data, sync_logs)..."
if psql "$DATABASE_URL" -f "$DATABASE_DIR/daily_stock_data_schema.sql" > /dev/null 2>&1; then
    echo "   ✅ 主表结构创建成功"
else
    echo "   ⚠️  主表可能已存在，跳过"
fi

# 2. 创建同步状态表
echo "2️⃣  创建同步状态表 (daily_sync_status)..."
if psql "$DATABASE_URL" -f "$DATABASE_DIR/daily_sync_status_schema.sql" > /dev/null 2>&1; then
    echo "   ✅ 同步状态表创建成功"
else
    echo "   ⚠️  同步状态表可能已存在，跳过"
fi

# 3. 创建同步进度表
echo "3️⃣  创建同步进度表 (sync_progress)..."
if psql "$DATABASE_URL" -f "$DATABASE_DIR/sync_progress_schema.sql" > /dev/null 2>&1; then
    echo "   ✅ 同步进度表创建成功"
else
    echo "   ⚠️  同步进度表可能已存在，跳过"
fi

# 4. 优化索引（可选）
if [ -f "$DATABASE_DIR/optimize_indexes.sql" ]; then
    echo "4️⃣  优化索引..."
    if psql "$DATABASE_URL" -f "$DATABASE_DIR/optimize_indexes.sql" > /dev/null 2>&1; then
        echo "   ✅ 索引优化成功"
    else
        echo "   ⚠️  索引可能已存在，跳过"
    fi
fi

echo ""
echo "🔍 验证数据库结构..."

# 验证表是否创建成功
TABLES=$(psql "$DATABASE_URL" -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")

echo "📋 已创建的表："
echo "$TABLES" | while read -r table; do
    if [ -n "$table" ]; then
        # 获取表的记录数
        COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
        echo "   ✅ $table (记录数: $(echo $COUNT | tr -d ' '))"
    fi
done

echo ""
echo "✨ 数据库初始化完成！"
echo ""
echo "📊 数据库统计："
psql "$DATABASE_URL" -c "
SELECT 
    schemaname,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname = 'public'
GROUP BY schemaname;
"

echo ""
echo "🎯 下一步："
echo "  1. 在 Render 配置环境变量："
echo "     DATABASE_URL=$DATABASE_URL"
echo "     NEON_DATABASE_URL=$DATABASE_URL"
echo ""
echo "  2. 在 Vercel 配置环境变量："
echo "     NEXT_PUBLIC_API_URL=https://your-app.onrender.com"
echo ""
echo "  3. 初始化历史数据（可选）："
echo "     export NEON_DATABASE_URL='$DATABASE_URL'"
echo "     python3 scripts/test_copy_sync.py --date 2025-10-18 --all"
echo ""
