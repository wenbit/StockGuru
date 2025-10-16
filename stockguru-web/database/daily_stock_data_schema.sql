-- 每日股票数据表
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- 股票基本信息
    stock_code VARCHAR(10) NOT NULL,           -- 股票代码（如 000001）
    stock_name VARCHAR(50) NOT NULL,           -- 股票名称
    
    -- 交易日期
    trade_date DATE NOT NULL,                  -- 交易日期
    
    -- 价格数据
    open_price DECIMAL(10, 2),                 -- 开盘价
    close_price DECIMAL(10, 2) NOT NULL,       -- 收盘价
    high_price DECIMAL(10, 2),                 -- 最高价
    low_price DECIMAL(10, 2),                  -- 最低价
    
    -- 成交数据
    volume BIGINT,                             -- 成交量（手）
    amount DECIMAL(20, 2),                     -- 成交额（元）
    
    -- 涨跌数据
    change_pct DECIMAL(10, 2),                 -- 涨跌幅（%）
    change_amount DECIMAL(10, 2),              -- 涨跌额（元）
    
    -- 其他指标
    turnover_rate DECIMAL(10, 2),              -- 换手率（%）
    amplitude DECIMAL(10, 2),                  -- 振幅（%）
    
    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 唯一约束：同一股票同一天只有一条记录
    UNIQUE(stock_code, trade_date)
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_daily_stock_trade_date ON daily_stock_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_stock_code ON daily_stock_data(stock_code);
CREATE INDEX IF NOT EXISTS idx_daily_stock_change_pct ON daily_stock_data(change_pct);
CREATE INDEX IF NOT EXISTS idx_daily_stock_code_date ON daily_stock_data(stock_code, trade_date);

-- 创建复合索引用于常见查询
CREATE INDEX IF NOT EXISTS idx_daily_stock_date_change ON daily_stock_data(trade_date, change_pct);

-- 添加注释
COMMENT ON TABLE daily_stock_data IS '每日股票交易数据表';
COMMENT ON COLUMN daily_stock_data.stock_code IS '股票代码';
COMMENT ON COLUMN daily_stock_data.stock_name IS '股票名称';
COMMENT ON COLUMN daily_stock_data.trade_date IS '交易日期';
COMMENT ON COLUMN daily_stock_data.close_price IS '收盘价';
COMMENT ON COLUMN daily_stock_data.volume IS '成交量（手）';
COMMENT ON COLUMN daily_stock_data.amount IS '成交额（元）';
COMMENT ON COLUMN daily_stock_data.change_pct IS '涨跌幅（%）';

-- 数据同步日志表
CREATE TABLE IF NOT EXISTS sync_logs (
    id BIGSERIAL PRIMARY KEY,
    sync_date DATE NOT NULL,                   -- 同步的交易日期
    sync_type VARCHAR(20) NOT NULL,            -- 同步类型：initial/daily
    status VARCHAR(20) NOT NULL,               -- 状态：pending/running/success/failed
    total_stocks INTEGER,                      -- 总股票数
    success_count INTEGER DEFAULT 0,           -- 成功数量
    failed_count INTEGER DEFAULT 0,            -- 失败数量
    error_message TEXT,                        -- 错误信息
    started_at TIMESTAMP WITH TIME ZONE,       -- 开始时间
    completed_at TIMESTAMP WITH TIME ZONE,     -- 完成时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(sync_date, sync_type)
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_date ON sync_logs(sync_date);
CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON sync_logs(status);

COMMENT ON TABLE sync_logs IS '数据同步日志表';
