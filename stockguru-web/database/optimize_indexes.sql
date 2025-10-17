-- 数据库索引优化脚本
-- 用于提升查询性能

-- 1. 复合索引：按日期和涨跌幅查询（常用于筛选强势股）
CREATE INDEX IF NOT EXISTS idx_date_change_desc 
ON daily_stock_data(trade_date DESC, change_pct DESC);

-- 2. 复合索引：按日期和成交量查询（常用于筛选活跃股）
CREATE INDEX IF NOT EXISTS idx_date_volume_desc 
ON daily_stock_data(trade_date DESC, volume DESC);

-- 3. 复合索引：按日期和成交额查询
CREATE INDEX IF NOT EXISTS idx_date_amount_desc 
ON daily_stock_data(trade_date DESC, amount DESC);

-- 4. 部分索引：只索引活跃股票（成交量 > 100万手）
CREATE INDEX IF NOT EXISTS idx_active_stocks 
ON daily_stock_data(stock_code, trade_date)
WHERE volume > 1000000;

-- 5. 部分索引：只索引涨停股（涨跌幅 > 9%）
CREATE INDEX IF NOT EXISTS idx_limit_up_stocks 
ON daily_stock_data(stock_code, trade_date, change_pct)
WHERE change_pct > 9.0;

-- 6. 覆盖索引：包含常用查询的所有列
CREATE INDEX IF NOT EXISTS idx_screening_cover 
ON daily_stock_data(trade_date, change_pct, volume, amount)
INCLUDE (stock_code, stock_name, close_price);

-- 7. 优化现有索引：添加 NULLS LAST
DROP INDEX IF EXISTS idx_daily_stock_change_pct;
CREATE INDEX idx_daily_stock_change_pct 
ON daily_stock_data(change_pct DESC NULLS LAST);

-- 查看索引使用情况
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'daily_stock_data'
-- ORDER BY idx_scan DESC;

-- 查看索引大小
-- SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid))
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'daily_stock_data';

COMMENT ON INDEX idx_date_change_desc IS '优化按日期和涨跌幅查询';
COMMENT ON INDEX idx_date_volume_desc IS '优化按日期和成交量查询';
COMMENT ON INDEX idx_active_stocks IS '部分索引：只索引活跃股票';
COMMENT ON INDEX idx_limit_up_stocks IS '部分索引：只索引涨停股';
COMMENT ON INDEX idx_screening_cover IS '覆盖索引：包含筛选常用列';
