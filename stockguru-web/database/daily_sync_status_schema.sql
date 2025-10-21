-- 每日数据同步状态表
CREATE TABLE IF NOT EXISTS daily_sync_status (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL UNIQUE,  -- 同步日期（唯一）
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 同步状态
    total_records INTEGER DEFAULT 0,  -- 同步的总条数
    success_count INTEGER DEFAULT 0,  -- 成功条数
    failed_count INTEGER DEFAULT 0,   -- 失败条数
    start_time TIMESTAMP,  -- 开始时间
    end_time TIMESTAMP,    -- 结束时间
    duration_seconds INTEGER,  -- 耗时（秒）
    error_message TEXT,    -- 错误信息
    remarks TEXT,          -- 备注
    process_id VARCHAR(50),  -- 进程ID（用于检查是否在运行）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 状态说明：
-- 'pending'      - 待同步：需要启动同步
-- 'syncing'      - 同步中：正在同步
-- 'success'      - 同步成功：已完成
-- 'failed'       - 同步失败：需要重新同步
-- 'skipped'      - 无需同步：非交易日或其他原因跳过

-- 创建索引
CREATE INDEX idx_sync_date ON daily_sync_status(sync_date);
CREATE INDEX idx_status ON daily_sync_status(status);
CREATE INDEX idx_created_at ON daily_sync_status(created_at);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_daily_sync_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_sync_status_updated_at
    BEFORE UPDATE ON daily_sync_status
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_sync_status_updated_at();

-- 添加注释
COMMENT ON TABLE daily_sync_status IS '每日数据同步状态表';
COMMENT ON COLUMN daily_sync_status.sync_date IS '同步日期';
COMMENT ON COLUMN daily_sync_status.status IS '同步状态：pending/syncing/success/failed/skipped';
COMMENT ON COLUMN daily_sync_status.total_records IS '同步的总条数';
COMMENT ON COLUMN daily_sync_status.success_count IS '成功条数';
COMMENT ON COLUMN daily_sync_status.failed_count IS '失败条数';
COMMENT ON COLUMN daily_sync_status.start_time IS '开始时间';
COMMENT ON COLUMN daily_sync_status.end_time IS '结束时间';
COMMENT ON COLUMN daily_sync_status.duration_seconds IS '耗时（秒）';
COMMENT ON COLUMN daily_sync_status.error_message IS '错误信息';
COMMENT ON COLUMN daily_sync_status.remarks IS '备注';
COMMENT ON COLUMN daily_sync_status.process_id IS '进程ID（用于检查是否在运行）';
