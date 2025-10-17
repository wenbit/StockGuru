#!/bin/bash
# 数据库性能监控脚本

echo "📊 数据库性能监控"
echo "================================"
echo ""

# 检查是否为 Docker 容器
if docker ps | grep -q postgres-test; then
    DB_CMD="docker exec postgres-test psql -U postgres stockguru_test"
else
    DB_CMD="psql stockguru_test"
fi

echo "📈 1. 索引使用情况"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'daily_stock_data'
ORDER BY idx_scan DESC
LIMIT 10;
EOF

echo ""
echo "📊 2. 表大小统计"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    pg_size_pretty(pg_total_relation_size('daily_stock_data')) as total_size,
    pg_size_pretty(pg_relation_size('daily_stock_data')) as table_size,
    pg_size_pretty(pg_indexes_size('daily_stock_data')) as indexes_size;
EOF

echo ""
echo "🔍 3. 慢查询统计"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    query,
    calls,
    total_exec_time / 1000 as total_time_sec,
    mean_exec_time / 1000 as avg_time_sec
FROM pg_stat_statements
WHERE query LIKE '%daily_stock_data%'
ORDER BY mean_exec_time DESC
LIMIT 5;
EOF

echo ""
echo "💾 4. 缓存命中率"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as cache_hit_ratio
FROM pg_statio_user_tables
WHERE relname = 'daily_stock_data';
EOF

echo ""
echo "🔗 5. 连接池状态"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = 'stockguru_test';
EOF

echo ""
echo "✅ 监控完成"
