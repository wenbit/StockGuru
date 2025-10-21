#!/bin/bash
#
# 实时监控后端数据同步进度
#

echo "🔍 实时监控后端数据同步进度"
echo "按 Ctrl+C 停止监控"
echo ""

while true; do
    # 获取当前时间
    current_time=$(date '+%H:%M:%S')
    
    # 调用 API 获取同步进度
    response=$(curl -s http://localhost:8000/api/v1/sync-status/sync/batch/active 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        # 解析 JSON 数据
        status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
        
        if [ "$status" = "success" ]; then
            # 提取进度信息
            task_status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('status', '-'))" 2>/dev/null)
            current=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('current', 0))" 2>/dev/null)
            total=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('total', 0))" 2>/dev/null)
            success=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('success', 0))" 2>/dev/null)
            failed=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('failed', 0))" 2>/dev/null)
            skipped=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('skipped', 0))" 2>/dev/null)
            current_date=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('current_date', '-'))" 2>/dev/null)
            progress_pct=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('progress_percent', 0))" 2>/dev/null)
            message=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); prog=data.get('data', {}).get('progress', {}); print(prog.get('message', '-'))" 2>/dev/null)
            
            # 生成进度条
            bar_length=40
            filled_length=$(echo "$progress_pct" | awk '{printf "%.0f", $1 * 40 / 100}')
            bar=$(printf "%-${bar_length}s" "$(printf '#%.0s' $(seq 1 $filled_length))" | tr ' ' '-')
            
            # 清屏并显示进度
            clear
            echo "╔════════════════════════════════════════════════════════════════════════════╗"
            echo "║                     🔄 后端数据同步实时进度                                ║"
            echo "╠════════════════════════════════════════════════════════════════════════════╣"
            echo "║ ⏰ 时间: $current_time                                                        "
            echo "║ 📊 状态: $task_status                                                         "
            echo "║ 📅 当前日期: $current_date                                                    "
            echo "╠════════════════════════════════════════════════════════════════════════════╣"
            echo "║ 进度: [$bar] $progress_pct%"
            echo "║                                                                            ║"
            echo "║ 📈 总数: $total 天                                                           "
            echo "║ 🔵 当前: $current/$total                                                     "
            echo "║ ✅ 成功: $success                                                            "
            echo "║ ❌ 失败: $failed                                                             "
            echo "║ ⏭️  跳过: $skipped                                                           "
            echo "╠════════════════════════════════════════════════════════════════════════════╣"
            echo "║ 💬 消息: $message"
            echo "╚════════════════════════════════════════════════════════════════════════════╝"
            
            # 如果完成则退出
            if [ "$task_status" = "completed" ] || [ "$progress_pct" = "100.0" ]; then
                echo ""
                echo "✅ 同步已完成！"
                break
            fi
        else
            clear
            echo "╔════════════════════════════════════════════════════════════════════════════╗"
            echo "║                     🔄 后端数据同步实时进度                                ║"
            echo "╠════════════════════════════════════════════════════════════════════════════╣"
            echo "║ ⏰ 时间: $current_time                                                        "
            echo "║                                                                            ║"
            echo "║ 📭 当前没有活动的同步任务                                                  ║"
            echo "╚════════════════════════════════════════════════════════════════════════════╝"
        fi
    else
        clear
        echo "╔════════════════════════════════════════════════════════════════════════════╗"
        echo "║                     🔄 后端数据同步实时进度                                ║"
        echo "╠════════════════════════════════════════════════════════════════════════════╣"
        echo "║ ⏰ 时间: $current_time                                                        "
        echo "║                                                                            ║"
        echo "║ ❌ 无法连接到后端服务 (http://localhost:8000)                              ║"
        echo "║                                                                            ║"
        echo "║ 请确保后端服务正在运行                                                     ║"
        echo "╚════════════════════════════════════════════════════════════════════════════╝"
    fi
    
    # 等待 2 秒后刷新
    sleep 2
done
