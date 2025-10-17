#!/bin/bash
# 启动完整的性能测试

echo "🚀 启动性能测试"
echo "================================"
echo ""

# 选择一个测试日期
TEST_DATE="2025-10-09"

echo "📅 测试日期: $TEST_DATE"
echo "⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 清理旧日志（可选）
echo "🧹 准备测试环境..."
echo ""

# 启动同步
echo "🔄 启动同步任务..."
echo ""

START_TIME=$(date +%s)

curl -X POST "http://localhost:8000/api/v1/daily/sync" \
  -H "Content-Type: application/json" \
  -d "{\"sync_date\": \"$TEST_DATE\"}" \
  2>&1 | python3 -m json.tool

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "================================"
echo "⏱️  API 响应时间: ${DURATION} 秒"
echo ""
echo "💡 查看详细日志:"
echo "tail -f stockguru-web/backend/backend.log | grep '$TEST_DATE'"
echo ""
echo "💡 监控进度:"
echo "watch -n 5 './scripts/monitor_performance.sh'"
