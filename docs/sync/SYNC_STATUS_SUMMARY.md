# 每日数据同步状态管理系统

## 📋 概述

新增了一个完整的每日数据同步状态管理系统，用于智能管理和追踪每日数据同步任务。

## ✨ 核心功能

### 1. 同步状态管理
- ✅ **5种状态**: pending(待同步)、syncing(同步中)、success(成功)、failed(失败)、skipped(跳过)
- ✅ **自动判断**: 智能判断是否需要启动同步
- ✅ **进程检测**: 检查同步进程是否还在运行
- ✅ **详细记录**: 记录总条数、成功/失败数、耗时、错误信息等

### 2. 智能同步决策

系统会自动判断是否需要同步：

| 状态 | 进程状态 | 是否同步 | 说明 |
|------|---------|---------|------|
| `pending` | - | ✅ 需要 | 待同步状态 |
| `failed` | - | ✅ 需要 | 上次失败，需重试 |
| `syncing` | 运行中 | ❌ 不需要 | 正在同步中 |
| `syncing` | 已停止 | ✅ 需要 | 进程异常退出 |
| `success` | - | ❌ 不需要 | 已成功完成 |
| `skipped` | - | ❌ 不需要 | 非交易日 |

## 📁 新增文件

### 1. 数据库相关
- `stockguru-web/database/daily_sync_status_schema.sql` - 数据库表结构
- `scripts/init_sync_status_table.py` - 表初始化脚本

### 2. 服务层
- `stockguru-web/backend/app/services/sync_status_service.py` - 状态管理服务
- `stockguru-web/backend/app/services/daily_sync_with_status.py` - 带状态管理的同步服务

### 3. API层
- `stockguru-web/backend/app/api/sync_status.py` - 状态管理API

### 4. 文档和测试
- `docs/SYNC_STATUS_GUIDE.md` - 使用指南
- `scripts/test_sync_status.py` - 功能测试脚本

## 🗄️ 数据库表结构

```sql
CREATE TABLE daily_sync_status (
    id SERIAL PRIMARY KEY,
    sync_date DATE NOT NULL UNIQUE,      -- 同步日期（唯一）
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
    created_at TIMESTAMP,                -- 创建时间
    updated_at TIMESTAMP                 -- 更新时间
);
```

## 🚀 快速开始

### 1. 初始化数据库表

```bash
cd /path/to/StockGuru
python scripts/init_sync_status_table.py
```

### 2. 安装依赖

```bash
pip install psutil  # 用于进程检测
```

### 3. 测试功能

```bash
python scripts/test_sync_status.py
```

### 4. 启动API服务

```bash
cd stockguru-web/backend
python -m uvicorn app.main:app --reload
```

## 📡 API端点

### 查询类

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/sync-status/today` | GET | 获取今日状态 |
| `/api/v1/sync-status/date/{date}` | GET | 获取指定日期状态 |
| `/api/v1/sync-status/recent?days=30` | GET | 获取最近N天状态 |
| `/api/v1/sync-status/pending?days_back=30` | GET | 获取待同步日期列表 |
| `/api/v1/sync-status/summary?days=30` | GET | 获取状态摘要 |

### 操作类

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/sync-status/sync/today` | POST | 同步今日数据 |
| `/api/v1/sync-status/sync/date/{date}` | POST | 同步指定日期 |
| `/api/v1/sync-status/sync/pending?days_back=30` | POST | 同步所有待同步日期 |
| `/api/v1/sync-status/check/{date}` | POST | 检查是否需要同步 |

## 💻 代码示例

### 1. 检查是否需要同步

```python
from datetime import date
from app.services.sync_status_service import SyncStatusService

today = date.today()
need_sync, reason = SyncStatusService.check_need_sync(today)

if need_sync:
    print(f"需要同步: {reason}")
    # 启动同步...
```

### 2. 执行同步（带状态管理）

```python
from datetime import date
from app.services.daily_sync_with_status import get_daily_sync_service

sync_service = get_daily_sync_service()

# 同步今日
result = await sync_service.sync_today()

# 同步所有待同步日期
result = await sync_service.sync_pending_dates(days_back=30)
```

### 3. 手动更新状态

```python
from datetime import date
from app.services.sync_status_service import SyncStatusService

sync_date = date.today()

# 标记为待同步
SyncStatusService.mark_as_pending(sync_date)

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
    error_message="网络超时"
)
```

## 🔄 与定时任务集成

定时任务会自动使用状态管理：

```python
# 在 scheduler.py 中
async def sync_today_data(self):
    """每日同步任务"""
    sync_service = get_daily_sync_service()
    result = await sync_service.sync_today()
    
    # 状态会自动更新：
    # - 开始时: syncing
    # - 成功时: success
    # - 失败时: failed
    # - 非交易日: skipped
```

## 📊 监控和查询

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
    AVG(duration_seconds) as avg_duration
FROM daily_sync_status
WHERE sync_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status;
```

## 🎯 使用场景

### 场景1: 每日自动同步

定时任务每晚20:00自动执行：
1. 检查今日是否需要同步
2. 如果需要，标记为`syncing`并开始同步
3. 完成后标记为`success`或`failed`

### 场景2: 补充历史数据

```bash
# 查找待同步日期
curl http://localhost:8000/api/v1/sync-status/pending?days_back=30

# 批量同步
curl -X POST http://localhost:8000/api/v1/sync-status/sync/pending?days_back=30
```

### 场景3: 失败重试

```bash
# 查看失败记录
curl http://localhost:8000/api/v1/sync-status/recent?days=7

# 重新同步失败日期
curl -X POST http://localhost:8000/api/v1/sync-status/sync/date/2025-10-17
```

### 场景4: 进程异常恢复

如果同步进程异常退出（状态卡在`syncing`）：
1. 系统检测到进程已停止
2. 自动判断需要重新同步
3. 重新启动同步任务

## ⚠️ 注意事项

1. **唯一性**: 每个日期只能有一条记录
2. **进程检测**: 需要安装`psutil`库
3. **时区**: 使用数据库服务器时区
4. **并发**: 避免多个进程同时同步同一日期
5. **清理**: 建议定期清理1年前的旧数据

## 🔧 故障排查

### 问题1: 同步卡在syncing状态

**解决**:
```bash
# 检查进程
curl -X POST http://localhost:8000/api/v1/sync-status/check/2025-10-17

# 重新同步
curl -X POST http://localhost:8000/api/v1/sync-status/sync/date/2025-10-17
```

### 问题2: 重复同步

**原因**: 多个定时任务同时运行

**解决**: 
- 检查`process_id`
- 确保只有一个调度器实例

## 📚 相关文档

- [详细使用指南](docs/SYNC_STATUS_GUIDE.md)
- [API文档](http://localhost:8000/docs) (启动服务后访问)

## 🎉 总结

这个系统提供了：
- ✅ 完整的同步状态管理
- ✅ 智能的同步决策
- ✅ 可靠的进程检测
- ✅ 丰富的API接口
- ✅ 详细的监控数据

现在你可以：
1. 自动判断是否需要同步
2. 避免重复同步
3. 监控同步状态
4. 快速定位问题
5. 批量补充历史数据
