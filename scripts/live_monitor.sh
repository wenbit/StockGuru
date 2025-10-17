#!/bin/bash
# 实时监控性能测试

clear
echo "🔴 实时性能监控 - 2025-10-15"
echo "================================"
echo ""

# 获取开始时间
START_LOG=$(tail -n 500 stockguru-web/backend/backend.log | grep "开始同步 2025-10-15" | tail -1)
START_TIME=$(echo "$START_LOG" | grep -oE "[0-9]{2}:[0-9]{2}:[0-9]{2}")

if [ -z "$START_TIME" ]; then
    echo "❌ 未找到测试任务"
    exit 1
fi

echo "⏰ 开始时间: $START_TIME"
echo "⏰ 当前时间: $(date '+%H:%M:%S')"

# 计算已用时间
START_SECONDS=$(echo $START_TIME | awk -F: '{print ($1 * 3600) + ($2 * 60) + $3}')
CURRENT_SECONDS=$(date '+%H:%M:%S' | awk -F: '{print ($1 * 3600) + ($2 * 60) + $3}')
ELAPSED=$((CURRENT_SECONDS - START_SECONDS))
ELAPSED_MIN=$((ELAPSED / 60))
ELAPSED_SEC=$((ELAPSED % 60))

echo "⏱️  已用时间: ${ELAPSED_MIN}分${ELAPSED_SEC}秒"
echo ""

# 优化特性
echo "🔧 优化特性:"
echo "--------------------------------"
tail -n 500 stockguru-web/backend/backend.log | grep -E "(batch_size|使用缓存|数据库性能)" | grep "2025-10-15" | tail -3
echo ""

# 最新进度
echo "📈 最新进度:"
echo "--------------------------------"
PROGRESS=$(tail -n 200 stockguru-web/backend/backend.log | grep "进度:" | tail -1)
echo "$PROGRESS"

if [ ! -z "$PROGRESS" ]; then
    # 提取进度数字
    CURRENT=$(echo "$PROGRESS" | grep -oE "[0-9]+/[0-9]+" | head -1 | cut -d'/' -f1)
    TOTAL=$(echo "$PROGRESS" | grep -oE "[0-9]+/[0-9]+" | head -1 | cut -d'/' -f2)
    SUCCESS=$(echo "$PROGRESS" | grep -oE "成功: [0-9]+" | grep -oE "[0-9]+")
    FAILED=$(echo "$PROGRESS" | grep -oE "失败: [0-9]+" | grep -oE "[0-9]+")
    
    if [ ! -z "$CURRENT" ] && [ ! -z "$TOTAL" ]; then
        PERCENT=$((CURRENT * 100 / TOTAL))
        SPEED=$((CURRENT * 60 / ELAPSED))
        REMAINING=$((TOTAL - CURRENT))
        ETA_SECONDS=$((REMAINING * 60 / SPEED))
        ETA_MIN=$((ETA_SECONDS / 60))
        
        echo ""
        echo "📊 统计:"
        echo "  进度: $CURRENT/$TOTAL ($PERCENT%)"
        echo "  成功: $SUCCESS"
        echo "  失败: $FAILED"
        echo "  速度: $SPEED 股/分钟"
        echo "  预计剩余: ~${ETA_MIN} 分钟"
    fi
fi

echo ""
echo "💡 按 Ctrl+C 退出监控"
echo "💡 运行: watch -n 3 ./scripts/live_monitor.sh 自动刷新"
