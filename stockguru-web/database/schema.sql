-- StockGuru 数据库表结构
-- 在 Supabase SQL Editor 中执行

-- 1. 任务表
CREATE TABLE IF NOT EXISTS tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date date NOT NULL,
  status text DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
  params jsonb NOT NULL,
  progress int DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  result_count int,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- 2. 结果表
CREATE TABLE IF NOT EXISTS results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid REFERENCES tasks(id) ON DELETE CASCADE,
  stock_code text NOT NULL,
  stock_name text NOT NULL,
  momentum_score decimal,
  comprehensive_score decimal,
  volume_rank int,
  hot_rank int,
  final_rank int,
  close_price decimal,
  change_pct decimal,
  volume bigint,
  created_at timestamptz DEFAULT now()
);

-- 3. K线缓存表
CREATE TABLE IF NOT EXISTS kline_cache (
  stock_code text NOT NULL,
  date date NOT NULL,
  open decimal,
  close decimal,
  high decimal,
  low decimal,
  volume bigint,
  ma5 decimal,
  ma10 decimal,
  ma20 decimal,
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (stock_code, date)
);

-- 4. 任务日志表
CREATE TABLE IF NOT EXISTS task_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid REFERENCES tasks(id) ON DELETE CASCADE,
  level text CHECK (level IN ('info', 'warning', 'error')),
  message text,
  created_at timestamptz DEFAULT now()
);

-- 5. 用户收藏表（可选）
CREATE TABLE IF NOT EXISTS favorites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  stock_code text NOT NULL UNIQUE,
  stock_name text,
  note text,
  created_at timestamptz DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_task_id ON results(task_id);
CREATE INDEX IF NOT EXISTS idx_results_rank ON results(final_rank);
CREATE INDEX IF NOT EXISTS idx_kline_code_date ON kline_cache(stock_code, date DESC);
CREATE INDEX IF NOT EXISTS idx_task_logs_task_id ON task_logs(task_id);

-- 启用 RLS（Row Level Security）
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE results ENABLE ROW LEVEL SECURITY;
ALTER TABLE kline_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

-- 创建策略：允许匿名访问（个人使用）
CREATE POLICY "Allow anonymous access" ON tasks FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON results FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON kline_cache FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON task_logs FOR ALL USING (true);
CREATE POLICY "Allow anonymous access" ON favorites FOR ALL USING (true);

-- 创建视图：最新筛选结果
CREATE OR REPLACE VIEW latest_screening AS
SELECT 
  t.id as task_id,
  t.date,
  t.status,
  t.result_count,
  t.created_at,
  r.stock_code,
  r.stock_name,
  r.momentum_score,
  r.final_rank
FROM tasks t
LEFT JOIN results r ON t.id = r.task_id
WHERE t.status = 'completed'
ORDER BY t.created_at DESC, r.final_rank ASC;
