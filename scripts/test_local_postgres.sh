#!/bin/bash
# 测试本地 PostgreSQL 的 COPY 命令性能

echo "🧪 本地 PostgreSQL COPY 命令测试"
echo "================================"
echo ""

# 检查环境变量
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL 未设置，使用默认值"
    export DATABASE_URL='postgresql://localhost/stockguru_test'
fi

echo "📋 测试配置:"
echo "  数据库: $DATABASE_URL"
echo "  测试日期: 2025-10-10"
echo ""

# 清空测试表
echo "🧹 清空测试数据..."
psql stockguru_test -c "TRUNCATE TABLE daily_stock_data;"
echo "✅ 测试表已清空"
echo ""

# 记录开始时间
START_TIME=$(date +%s)
echo "⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 运行同步测试
echo "🔄 开始同步测试..."
curl -X POST "http://localhost:8000/api/v1/daily/sync" \
  -H "Content-Type: application/json" \
  -d '{"sync_date": "2025-10-10"}' \
  2>&1 | python3 -m json.tool

# 记录结束时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "⏰ 结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "⏱️  总耗时: ${DURATION} 秒"
echo ""

# 查看结果
echo "📊 同步结果:"
echo "--------------------------------"
psql stockguru_test -c "SELECT COUNT(*) as total_records FROM daily_stock_data;"
psql stockguru_test -c "SELECT stock_code, stock_name, trade_date, close_price FROM daily_stock_data LIMIT 5;"
echo ""

# 查看日志中的 COPY 命令执行情况
echo "📝 COPY 命令执行日志:"
echo "--------------------------------"
tail -n 100 stockguru-web/backend/backend.log | grep -E "(COPY|回退)" | tail -10
echo ""

echo "✅ 测试完成！"
echo ""
echo "💡 查看详细日志:"
echo "  tail -f stockguru-web/backend/backend.log | grep -E '(COPY|进度)'"
