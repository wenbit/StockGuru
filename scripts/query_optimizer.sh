#!/bin/bash
# 查询优化工具

echo "🔍 查询优化分析工具"
echo "================================"
echo ""

# 检查是否为 Docker 容器
if docker ps | grep -q postgres-test; then
    DB_CMD="docker exec postgres-test psql -U postgres stockguru_test"
else
    DB_CMD="psql stockguru_test"
fi

# 1. 分析慢查询
echo "📊 1. 慢查询分析"
echo "--------------------------------"
$DB_CMD << 'EOF'
-- 需要启用 pg_stat_statements 扩展
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT 
    substring(query, 1, 80) as query_snippet,
    calls,
    ROUND(total_exec_time::numeric / 1000, 2) as total_time_sec,
    ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
    ROUND((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) as pct
FROM pg_stat_statements
WHERE query LIKE '%daily_stock_data%'
  AND query NOT LIKE '%pg_stat_statements%'
ORDER BY total_exec_time DESC
LIMIT 10;
EOF

echo ""
echo "📈 2. 表膨胀分析"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(100 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND tablename = 'daily_stock_data';
EOF

echo ""
echo "🔧 3. 索引健康检查"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as size,
    CASE 
        WHEN idx_scan = 0 THEN '❌ 未使用'
        WHEN idx_scan < 100 THEN '⚠️  很少使用'
        ELSE '✅ 正常使用'
    END as status
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename = 'daily_stock_data'
ORDER BY idx_scan DESC;
EOF

echo ""
echo "💾 4. 缓存命中率"
echo "--------------------------------"
$DB_CMD << 'EOF'
SELECT 
    'Heap Blocks' as type,
    sum(heap_blks_hit) as hits,
    sum(heap_blks_read) as reads,
    CASE 
        WHEN sum(heap_blks_hit) + sum(heap_blks_read) = 0 THEN 0
        ELSE ROUND(100.0 * sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)), 2)
    END as hit_ratio
FROM pg_statio_user_tables
WHERE relname = 'daily_stock_data'
UNION ALL
SELECT 
    'Index Blocks' as type,
    sum(idx_blks_hit) as hits,
    sum(idx_blks_read) as reads,
    CASE 
        WHEN sum(idx_blks_hit) + sum(idx_blks_read) = 0 THEN 0
        ELSE ROUND(100.0 * sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)), 2)
    END as hit_ratio
FROM pg_statio_user_tables
WHERE relname = 'daily_stock_data';
EOF

echo ""
echo "🎯 5. 查询计划分析示例"
echo "--------------------------------"
echo "运行 EXPLAIN ANALYZE 分析查询:"
echo ""
echo "示例 1: 查询涨幅榜"
$DB_CMD << 'EOF'
EXPLAIN (ANALYZE, BUFFERS) 
SELECT stock_code, stock_name, change_pct
FROM daily_stock_data
WHERE trade_date = (SELECT MAX(trade_date) FROM daily_stock_data)
ORDER BY change_pct DESC
LIMIT 10;
EOF

echo ""
echo "✅ 优化建议"
echo "--------------------------------"
echo "1. 如果缓存命中率 < 95%，考虑增加 shared_buffers"
echo "2. 如果有未使用的索引，考虑删除以节省空间"
echo "3. 如果死行比例 > 10%，运行 VACUUM ANALYZE"
echo "4. 定期刷新物化视图以保持数据最新"
echo ""
echo "🔧 维护命令:"
echo "  VACUUM ANALYZE daily_stock_data;  # 清理死行"
echo "  REINDEX TABLE daily_stock_data;    # 重建索引"
echo "  SELECT refresh_all_materialized_views();  # 刷新物化视图"
