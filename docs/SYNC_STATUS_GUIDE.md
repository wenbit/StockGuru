# 每日数据同步状态管理指南

## 概述

每日数据同步状态表用于管理和追踪每日数据同步任务的状态，实现智能同步管理。

## 功能特性

### 1. 同步状态管理

支持5种状态：
- **pending** (待同步): 需要启动同步
- **syncing** (同步中): 正在同步
- **success** (同步成功): 已完成
- **failed** (同步失败): 需要重新同步
- **skipped** (无需同步): 非交易日或其他原因跳过

### 2. 智能同步判断

自动判断是否需要同步：
- ✅ `pending` 状态 → 需要同步
- ✅ `failed` 状态 → 需要重新同步
- ✅ `syncing` 状态 + 进程已停止 → 需要重新同步
- ❌ `syncing` 状态 + 进程运行中 → 无需同步
- ❌ `success` 或 `skipped` → 无需同步

### 3. 进程检测

- 记录同步进程ID
- 检查进程是否还在运行
- 避免重复同步

## 数据库表结构

```sql
CREATE TABLE daily_sync_status (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL UNIQUE,      -- 同步日期
    status VARCHAR(20) NOT NULL,         -- 同步状态
    total_records INTEGER DEFAULT 0,     -- 总条数
    success_count INTEGER DEFAULT 0,     -- 成功条数
    failed_count INTEGER DEFAULT 0,      -- 失败条数
    start_time TIMESTAMP,                -- 开始时间
    end_time TIMESTAMP,                  -- 结束时间
    duration_seconds INTEGER,            -- 耗时（秒）
    error_message TEXT,                  -- 错误信息
    remarks TEXT,                        -- 备注
    process_id VARCHAR(50),              -- 进程ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 初始化

### 1. 创建数据库表

```bash
cd /path/to/StockGuru
python scripts/init_sync_status_table.py
```

### 2. 验证表创建

```bash
# 查看表结构
psql $DATABASE_URL -c "\d daily_sync_status"

# 查看数据
psql $DATABASE_URL -c "SELECT * FROM daily_sync_status ORDER BY sync_date DESC LIMIT 10"
```

## API使用

### 1. 查询同步状态

#### 获取今日状态
```bash
curl http://localhost:8000/api/v1/sync-status/today
```

#### 获取指定日期状态
```bash
curl http://localhost:8000/api/v1/sync-status/date/2025-10-17
```

#### 获取最近30天状态
```bash
curl http://localhost:8000/api/v1/sync-status/recent?days=30
```

#### 获取待同步日期列表
```bash
curl http://localhost:8000/api/v1/sync-status/pending?days_back=30
```

#### 获取状态摘要
```bash
curl http://localhost:8000/api/v1/sync-status/summary?days=30
```

### 2. 手动触发同步

#### 同步今日数据
```bash
curl -X POST http://localhost:8000/api/v1/sync-status/sync/today
```

#### 同步指定日期
```bash
curl -X POST http://localhost:8000/api/v1/sync-status/sync/date/2025-10-17
```

#### 同步所有待同步日期
```bash
curl -X POST http://localhost:8000/api/v1/sync-status/sync/pending?days_back=30
```

### 3. 检查同步需求

```bash
curl -X POST http://localhost:8000/api/v1/sync-status/check/2025-10-17
```

响应示例：
```json
{
  "status": "success",
  "date": "2025-10-17",
  "need_sync": true,
  "reason": "状态为待同步"
}
```

## Python代码示例

### 1. 基本使用

```python
from datetime import date
from app.services.sync_status_service import SyncStatusService

# 检查是否需要同步
today = date.today()
need_sync, reason = SyncStatusService.check_need_sync(today)

if need_sync:
    print(f"需要同步: {reason}")
else:
    print(f"无需同步: {reason}")
```

### 2. 同步流程

```python
from datetime import date
from app.services.daily_sync_with_status import get_daily_sync_service

# 获取同步服务
sync_service = get_daily_sync_service()

# 同步今日数据
result = await sync_service.sync_today()
print(f"同步结果: {result}")

# 同步所有待同步日期
result = await sync_service.sync_pending_dates(days_back=30)
print(f"同步了 {result['success']} 个日期")
```

### 3. 状态管理

```python
from datetime import date
from app.services.sync_status_service import SyncStatusService

sync_date = date.today()

# 标记为待同步
SyncStatusService.mark_as_pending(sync_date, remarks="手动标记")

# 标记为同步中
SyncStatusService.mark_as_syncing(sync_date, process_id="12345")

# 标记为成功
SyncStatusService.mark_as_success(
    sync_date=sync_date,
    total_records=5000,
    remarks="同步完成"
)

# 标记为失败
SyncStatusService.mark_as_failed(
    sync_date=sync_date,
    error_message="网络超时",
    total_records=5000,
    success_count=3000,
    failed_count=2000
)

# 标记为跳过
SyncStatusService.mark_as_skipped(sync_date, remarks="非交易日")
```

## 定时任务集成

定时任务会自动使用状态管理：

```python
# 在 scheduler.py 中
async def sync_today_data(self):
    """每日同步任务"""
    sync_service = get_daily_sync_service()
    result = await sync_service.sync_today()
    
    # 状态会自动更新
    # - 开始时标记为 syncing
    # - 成功时标记为 success
    # - 失败时标记为 failed
    # - 非交易日标记为 skipped
```

## 监控和告警

### 1. 查看失败的同步

```sql
SELECT sync_date, error_message, failed_count
FROM daily_sync_status
WHERE status = 'failed'
ORDER BY sync_date DESC;
```

### 2. 查看同步性能

```sql
SELECT 
    sync_date,
    total_records,
    duration_seconds,
    ROUND(total_records::numeric / duration_seconds, 2) as records_per_second
FROM daily_sync_status
WHERE status = 'success'
ORDER BY sync_date DESC
LIMIT 10;
```

### 3. 统计同步状态

```sql
SELECT 
    status,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration,
    AVG(total_records) as avg_records
FROM daily_sync_status
WHERE sync_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status;
```

## 最佳实践

### 1. 定期检查待同步日期

```bash
# 每天检查一次
curl http://localhost:8000/api/v1/sync-status/pending?days_back=7
```

### 2. 失败重试

```bash
# 重新同步所有失败的日期
curl -X POST http://localhost:8000/api/v1/sync-status/sync/pending?days_back=30
```

### 3. 监控同步进度

```bash
# 查看最近同步状态
curl http://localhost:8000/api/v1/sync-status/summary?days=7
```

## 故障排查

### 问题1: 同步卡在 syncing 状态

**原因**: 进程异常退出，状态未更新

**解决**:
```bash
# 检查进程是否还在运行
curl -X POST http://localhost:8000/api/v1/sync-status/check/2025-10-17

# 如果进程已停止，重新同步
curl -X POST http://localhost:8000/api/v1/sync-status/sync/date/2025-10-17
```

### 问题2: 重复同步

**原因**: 多个进程同时启动

**解决**: 
- 检查 `process_id` 字段
- 确保只有一个定时任务在运行
- 使用进程锁机制

### 问题3: 数据不一致

**原因**: 同步过程中数据库连接中断

**解决**:
```bash
# 标记为失败，重新同步
curl -X POST http://localhost:8000/api/v1/sync-status/sync/date/2025-10-17
```

## 注意事项

1. **唯一性约束**: `sync_date` 字段有唯一约束，每个日期只能有一条记录
2. **进程检测**: 依赖 `psutil` 库，需要安装：`pip install psutil`
3. **时区**: 所有时间戳使用数据库服务器时区
4. **性能**: 建议定期清理旧数据（保留1年即可）

## 数据清理

```sql
-- 删除1年前的记录
DELETE FROM daily_sync_status
WHERE sync_date < CURRENT_DATE - INTERVAL '1 year';
```
