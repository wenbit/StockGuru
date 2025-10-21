#!/bin/bash
#
# 实时显示数据同步日志（美化版）
#

echo "📋 实时显示数据同步日志"
echo "按 Ctrl+C 停止"
echo ""

# 显示最近的进度
echo "最近进度："
tail -20 logs/backend.log | grep "test_copy_sync: 进度" | tail -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "实时日志流："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 实时跟踪日志，只显示关键信息
tail -f logs/backend.log | grep --line-buffered -E "test_copy_sync: (进度|✅|⚠️|❌|数据获取完成|开始测试)" | while read line; do
    # 提取时间和内容
    timestamp=$(echo "$line" | cut -d' ' -f1-2)
    content=$(echo "$line" | sed 's/.*test_copy_sync: //')
    
    # 根据内容类型添加颜色
    if [[ $content == *"进度:"* ]]; then
        # 提取进度百分比
        percent=$(echo "$content" | grep -oP '\d+%' | head -1)
        current=$(echo "$content" | grep -oP '进度: \K\d+')
        total=$(echo "$content" | grep -oP '/\K\d+' | head -1)
        success=$(echo "$content" | grep -oP '成功: \K\d+')
        speed=$(echo "$content" | grep -oP '速度: \K[0-9.]+')
        eta=$(echo "$content" | grep -oP '预计剩余: \K\d+')
        eta_min=$((eta / 60))
        
        printf "\r⏱️  %s | 📊 %s (%d/%d) | ✅ %d | 🚀 %s股/秒 | ⏳ %d分钟   " \
               "$timestamp" "$percent" "$current" "$total" "$success" "$speed" "$eta_min"
    elif [[ $content == *"✅"* ]]; then
        echo ""
        echo "💾 $timestamp | $content"
    elif [[ $content == *"⚠️"* ]]; then
        echo ""
        echo "⚠️  $timestamp | $content"
    elif [[ $content == *"数据获取完成"* ]]; then
        echo ""
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎉 $timestamp | $content"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        break
    elif [[ $content == *"开始测试"* ]]; then
        echo "🚀 $timestamp | $content"
        echo ""
    fi
done
