#!/bin/bash
# 实时监控同步性能

echo "📊 实时性能监控"
echo "================================"
echo ""

# 获取最新的同步任务
LATEST_DATE=$(tail -n 100 stockguru-web/backend/backend.log | grep "开始同步" | tail -1 | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}")

if [ -z "$LATEST_DATE" ]; then
    echo "❌ 未找到正在进行的同步任务"
    exit 1
fi

echo "📅 监控日期: $LATEST_DATE"
echo ""

# 获取开始时间
START_TIME=$(tail -n 1000 stockguru-web/backend/backend.log | grep "开始同步 $LATEST_DATE" | tail -1 | grep -oE "[0-9]{2}:[0-9]{2}:[0-9]{2}")
echo "⏰ 开始时间: $START_TIME"

# 获取最新进度
echo ""
echo "📈 最新进度:"
echo "--------------------------------"
tail -n 100 stockguru-web/backend/backend.log | grep "进度:" | tail -5

echo ""
echo "🔧 优化特性:"
echo "--------------------------------"
tail -n 1000 stockguru-web/backend/backend.log | grep -E "(batch_size|使用缓存|数据库性能)" | tail -3

echo ""
echo "💡 提示: 运行 watch -n 5 ./scripts/monitor_performance.sh 实时监控"
