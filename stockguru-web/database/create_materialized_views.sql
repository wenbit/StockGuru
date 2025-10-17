-- 物化视图：预计算常用查询，提升性能

-- 1. 每日统计汇总
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_market_stats AS
SELECT 
    trade_date,
    COUNT(*) as total_stocks,
    COUNT(*) FILTER (WHERE change_pct > 0) as up_count,
    COUNT(*) FILTER (WHERE change_pct < 0) as down_count,
    COUNT(*) FILTER (WHERE change_pct = 0) as flat_count,
    AVG(change_pct) as avg_change_pct,
    AVG(volume) as avg_volume,
    SUM(amount) as total_amount,
    MAX(change_pct) as max_change_pct,
    MIN(change_pct) as min_change_pct,
    COUNT(*) FILTER (WHERE change_pct >= 9.9) as limit_up_count,
    COUNT(*) FILTER (WHERE change_pct <= -9.9) as limit_down_count
FROM daily_stock_data
GROUP BY trade_date
ORDER BY trade_date DESC;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_daily_stats_date 
ON daily_market_stats(trade_date DESC);

COMMENT ON MATERIALIZED VIEW daily_market_stats IS '每日市场统计汇总';


-- 2. 强势股榜单（最近30天涨幅前100）
CREATE MATERIALIZED VIEW IF NOT EXISTS top_gainers_30d AS
SELECT 
    stock_code,
    stock_name,
    trade_date,
    close_price,
    change_pct,
    volume,
    amount,
    turnover_rate,
    ROW_NUMBER() OVER (PARTITION BY trade_date ORDER BY change_pct DESC) as rank
FROM daily_stock_data
WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days'
  AND volume > 1000000  -- 只统计活跃股
  AND change_pct IS NOT NULL
ORDER BY trade_date DESC, change_pct DESC;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_top_gainers_date_rank 
ON top_gainers_30d(trade_date DESC, rank);

COMMENT ON MATERIALIZED VIEW top_gainers_30d IS '最近30天强势股榜单';


-- 3. 活跃股票列表（按成交量）
CREATE MATERIALIZED VIEW IF NOT EXISTS most_active_stocks AS
SELECT 
    stock_code,
    stock_name,
    trade_date,
    close_price,
    volume,
    amount,
    change_pct,
    turnover_rate,
    ROW_NUMBER() OVER (PARTITION BY trade_date ORDER BY volume DESC) as rank
FROM daily_stock_data
WHERE trade_date >= CURRENT_DATE - INTERVAL '30 days'
  AND volume IS NOT NULL
ORDER BY trade_date DESC, volume DESC;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_active_stocks_date_rank 
ON most_active_stocks(trade_date DESC, rank);

COMMENT ON MATERIALIZED VIEW most_active_stocks IS '活跃股票列表（按成交量）';


-- 4. 涨停股统计
CREATE MATERIALIZED VIEW IF NOT EXISTS limit_up_stocks AS
SELECT 
    stock_code,
    stock_name,
    trade_date,
    close_price,
    change_pct,
    volume,
    amount,
    turnover_rate
FROM daily_stock_data
WHERE trade_date >= CURRENT_DATE - INTERVAL '90 days'
  AND change_pct >= 9.9
ORDER BY trade_date DESC, change_pct DESC;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_limit_up_date 
ON limit_up_stocks(trade_date DESC);

COMMENT ON MATERIALIZED VIEW limit_up_stocks IS '涨停股统计（最近90天）';


-- 5. 股票动量排行（最近5日平均涨幅）
CREATE MATERIALIZED VIEW IF NOT EXISTS stock_momentum_5d AS
WITH recent_data AS (
    SELECT 
        stock_code,
        stock_name,
        trade_date,
        change_pct,
        volume
    FROM daily_stock_data
    WHERE trade_date >= CURRENT_DATE - INTERVAL '7 days'
)
SELECT 
    stock_code,
    MAX(stock_name) as stock_name,
    COUNT(*) as trading_days,
    AVG(change_pct) as avg_change_5d,
    SUM(change_pct) as total_change_5d,
    AVG(volume) as avg_volume_5d,
    MAX(trade_date) as latest_date
FROM recent_data
GROUP BY stock_code
HAVING COUNT(*) >= 3  -- 至少3个交易日
ORDER BY avg_change_5d DESC
LIMIT 500;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_momentum_avg_change 
ON stock_momentum_5d(avg_change_5d DESC);

COMMENT ON MATERIALIZED VIEW stock_momentum_5d IS '股票动量排行（5日平均涨幅）';


-- 刷新物化视图的函数
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_market_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY top_gainers_30d;
    REFRESH MATERIALIZED VIEW CONCURRENTLY most_active_stocks;
    REFRESH MATERIALIZED VIEW CONCURRENTLY limit_up_stocks;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stock_momentum_5d;
    
    RAISE NOTICE '所有物化视图已刷新';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_materialized_views IS '刷新所有物化视图';


-- 创建定时刷新任务（需要 pg_cron 扩展）
-- 每天凌晨1点自动刷新
-- SELECT cron.schedule('refresh-materialized-views', '0 1 * * *', 'SELECT refresh_all_materialized_views()');


-- 查看物化视图大小
-- SELECT 
--     schemaname,
--     matviewname,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
-- FROM pg_matviews
-- ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;
