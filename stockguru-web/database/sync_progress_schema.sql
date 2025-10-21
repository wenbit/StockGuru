-- 同步进度记录表（支持断点续传）
CREATE TABLE IF NOT EXISTS sync_progress (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL,           -- 同步日期
    stock_code VARCHAR(10) NOT NULL,   -- 股票代码
    stock_name VARCHAR(50),            -- 股票名称
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 状态: pending/success/failed
    error_message TEXT,                -- 错误信息
    retry_count INTEGER DEFAULT 0,     -- 重试次数
    synced_at TIMESTAMP,               -- 同步完成时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sync_date, stock_code)      -- 每个日期每只股票只有一条记录
);

-- 状态说明：
-- 'pending'  - 待同步：还未同步
-- 'success'  - 成功：已同步成功
-- 'failed'   - 失败：同步失败，可重试

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_sync_progress_date ON sync_progress(sync_date);
CREATE INDEX IF NOT EXISTS idx_sync_progress_status ON sync_progress(sync_date, status);
CREATE INDEX IF NOT EXISTS idx_sync_progress_code ON sync_progress(stock_code);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_sync_progress_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_sync_progress_updated_at ON sync_progress;
CREATE TRIGGER trigger_update_sync_progress_updated_at
    BEFORE UPDATE ON sync_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_progress_updated_at();

-- 添加注释
COMMENT ON TABLE sync_progress IS '同步进度记录表（支持断点续传）';
COMMENT ON COLUMN sync_progress.sync_date IS '同步日期';
COMMENT ON COLUMN sync_progress.stock_code IS '股票代码';
COMMENT ON COLUMN sync_progress.stock_name IS '股票名称';
COMMENT ON COLUMN sync_progress.status IS '状态：pending/success/failed';
COMMENT ON COLUMN sync_progress.error_message IS '错误信息';
COMMENT ON COLUMN sync_progress.retry_count IS '重试次数';
COMMENT ON COLUMN sync_progress.synced_at IS '同步完成时间';

-- 创建统计视图
CREATE OR REPLACE VIEW sync_progress_summary AS
SELECT 
    sync_date,
    COUNT(*) as total_stocks,
    COUNT(*) FILTER (WHERE status = 'success') as success_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    ROUND(COUNT(*) FILTER (WHERE status = 'success')::numeric / COUNT(*) * 100, 2) as success_rate,
    MIN(created_at) as start_time,
    MAX(synced_at) as last_sync_time
FROM sync_progress
GROUP BY sync_date
ORDER BY sync_date DESC;

COMMENT ON VIEW sync_progress_summary IS '同步进度统计视图';
