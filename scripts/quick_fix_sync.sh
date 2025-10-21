#!/bin/bash
#
# 快速修复 2025-09-09 和 2025-09-10 的同步问题
#

set -e

echo "================================================================================================"
echo "数据同步问题快速修复脚本"
echo "================================================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查环境变量
if [ -z "$NEON_DATABASE_URL" ]; then
    echo -e "${RED}错误：未设置 NEON_DATABASE_URL 环境变量${NC}"
    echo "请先运行: source stockguru-web/backend/.env"
    exit 1
fi

echo -e "${YELLOW}步骤 1/5: 停止当前同步任务${NC}"
echo "------------------------------------------------------------------------------------------------"
echo "检查是否有正在运行的同步任务..."

# 检查后端进程
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo -e "${YELLOW}发现正在运行的后端服务${NC}"
    read -p "是否需要重启后端服务以停止同步任务？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "停止后端服务..."
        pkill -f "uvicorn app.main:app" || true
        sleep 2
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
        
        echo "重新启动后端服务..."
        cd stockguru-web/backend
        source .env
        nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../../logs/backend.log 2>&1 &
        echo $! > ../../logs/.backend.pid
        cd ../..
        sleep 3
        echo -e "${GREEN}✓ 后端服务已重启${NC}"
    fi
else
    echo -e "${GREEN}✓ 没有发现正在运行的同步任务${NC}"
fi

echo ""
echo -e "${YELLOW}步骤 2/5: 分析当前数据状态${NC}"
echo "------------------------------------------------------------------------------------------------"
python3 scripts/analyze_sync_issue.py

echo ""
read -p "是否继续执行数据清理和重新同步？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消操作"
    exit 0
fi

echo ""
echo -e "${YELLOW}步骤 3/5: 清理错误数据${NC}"
echo "------------------------------------------------------------------------------------------------"
echo "正在清理 2025-09-09 和 2025-09-10 的数据..."

psql $NEON_DATABASE_URL << 'EOF'
-- 删除错误数据
DELETE FROM daily_stock_data WHERE trade_date IN ('2025-09-09', '2025-09-10');

-- 重置同步状态
UPDATE daily_sync_status 
SET status = 'pending',
    total_records = 0,
    success_count = 0,
    failed_count = 0,
    start_time = NULL,
    end_time = NULL,
    duration_seconds = NULL,
    remarks = '待重新同步（已修复计数逻辑）',
    updated_at = NOW()
WHERE sync_date IN ('2025-09-09', '2025-09-10');

-- 显示清理结果
SELECT '清理后的数据量:' as info;
SELECT trade_date, COUNT(*) as count
FROM daily_stock_data 
WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-11'
GROUP BY trade_date
ORDER BY trade_date;

SELECT '同步状态:' as info;
SELECT sync_date, status, total_records, success_count, failed_count
FROM daily_sync_status
WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-11'
ORDER BY sync_date;
EOF

echo -e "${GREEN}✓ 数据清理完成${NC}"

echo ""
echo -e "${YELLOW}步骤 4/5: 重新同步数据${NC}"
echo "------------------------------------------------------------------------------------------------"

# 同步 2025-09-09
echo ""
echo "同步 2025-09-09..."
python3 scripts/test_copy_sync.py --date 2025-09-09

# 等待几秒
sleep 3

# 同步 2025-09-10
echo ""
echo "同步 2025-09-10..."
python3 scripts/test_copy_sync.py --date 2025-09-10

echo -e "${GREEN}✓ 数据同步完成${NC}"

echo ""
echo -e "${YELLOW}步骤 5/5: 验证结果${NC}"
echo "------------------------------------------------------------------------------------------------"

psql $NEON_DATABASE_URL << 'EOF'
-- 验证数据量
SELECT '数据量验证:' as info;
SELECT 
    trade_date,
    COUNT(*) as records,
    COUNT(DISTINCT stock_code) as unique_stocks
FROM daily_stock_data
WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-10'
GROUP BY trade_date
ORDER BY trade_date;

-- 验证同步状态
SELECT '同步状态验证:' as info;
SELECT 
    sync_date,
    status,
    total_records,
    success_count,
    failed_count,
    ROUND(failed_count::numeric / NULLIF(total_records, 0) * 100, 2) as fail_rate_pct,
    remarks
FROM daily_sync_status
WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-10'
ORDER BY sync_date;

-- 检查数据一致性
SELECT '数据一致性检查:' as info;
SELECT 
    s.sync_date,
    s.success_count as sync_success,
    COUNT(d.id) as db_count,
    s.success_count - COUNT(d.id) as difference
FROM daily_sync_status s
LEFT JOIN daily_stock_data d ON s.sync_date = d.trade_date
WHERE s.sync_date BETWEEN '2025-09-08' AND '2025-09-10'
GROUP BY s.sync_date, s.success_count
ORDER BY s.sync_date;
EOF

echo ""
echo "================================================================================================"
echo -e "${GREEN}✅ 修复完成！${NC}"
echo "================================================================================================"
echo ""
echo "请检查以上验证结果："
echo "  1. 每天数据量应该 > 4000 条"
echo "  2. 失败率应该 < 5%"
echo "  3. sync_success 与 db_count 应该基本一致（误差 < 10）"
echo ""
echo "如果结果不理想，请查看日志文件："
echo "  - logs/sync_2025-09-09.log"
echo "  - logs/sync_2025-09-10.log"
echo ""
