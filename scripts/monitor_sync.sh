#!/bin/bash
# 监控同步进度

echo "📊 同步进度监控"
echo "================================"

# 检查检查点文件
if [ -f "test_fast_checkpoint.json" ]; then
    echo ""
    echo "📝 检查点信息:"
    python3 -c "
import json
with open('test_fast_checkpoint.json') as f:
    data = json.load(f)
    print(f\"已完成: {len(data['completed_dates'])} 天\")
    print(f\"失败: {len(data['failed_dates'])} 天\")
    print(f\"总记录: {data.get('total_records', 0):,} 条\")
    if data.get('start_time'):
        import time
        elapsed = time.time() - data['start_time']
        print(f\"已运行: {elapsed/60:.1f} 分钟\")
"
fi

echo ""
echo "📈 最近日志:"
echo "--------------------------------"
tail -n 20 stockguru-web/backend/backend.log | grep -E "(进度|完成|成功率)" | tail -n 5

echo ""
echo "================================"
echo "提示: 运行 watch -n 10 ./scripts/monitor_sync.sh 实时监控"
