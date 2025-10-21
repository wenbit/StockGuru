# 同步记录时区修复说明

## 📋 问题描述

同步记录中的 `start_time` 和 `end_time` 显示的不是北京时间（UTC+8），而是 UTC 时间或其他时区。

**问题示例**：
- 实际北京时间：2025/10/21 15:19:58
- 显示时间：2025/10/21 07:19:58（相差 8 小时）

## 🔍 问题原因

1. **数据库表结构问题**：
   - 使用了 `TIMESTAMP` 类型而不是 `TIMESTAMP WITH TIME ZONE`
   - PostgreSQL 在存储时会将 datetime 对象转换为 UTC 时间

2. **代码问题**：
   - 虽然代码中使用了 `BEIJING_TZ`，但直接传递 datetime 对象
   - psycopg2 会自动将带时区的 datetime 转换为 UTC

## ✅ 修复方案

### 方案：将时间转换为字符串格式插入

不直接传递 datetime 对象，而是转换为字符串格式，然后在 SQL 中转换为 timestamp。

### 修改的文件

#### 1. `scripts/test_copy_sync.py`

**修改位置**：`update_sync_status` 方法

**修改前**：
```python
beijing_now = datetime.now(BEIJING_TZ)

if existing:
    end_time = beijing_now if status in ('success', 'failed', 'skipped') else None
    cursor.execute("""
        UPDATE daily_sync_status 
        SET ...
            end_time = COALESCE(%s, end_time),
            updated_at = %s
        WHERE sync_date = %s
    """, (..., end_time, beijing_now, sync_date))
else:
    cursor.execute("""
        INSERT INTO daily_sync_status (
            ..., start_time
        ) VALUES (..., %s)
    """, (..., beijing_now))
```

**修改后**：
```python
beijing_now = datetime.now(BEIJING_TZ)
beijing_now_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')

if existing:
    end_time_str = beijing_now_str if status in ('success', 'failed', 'skipped') else None
    cursor.execute("""
        UPDATE daily_sync_status 
        SET ...
            end_time = COALESCE(%s::timestamp, end_time),
            updated_at = %s::timestamp
        WHERE sync_date = %s
    """, (..., end_time_str, beijing_now_str, sync_date))
else:
    cursor.execute("""
        INSERT INTO daily_sync_status (
            ..., start_time
        ) VALUES (..., %s::timestamp)
    """, (..., beijing_now_str))
```

#### 2. `stockguru-web/backend/app/services/sync_status_service.py`

**修改位置**：`create_or_update_status` 和 `update_record` 方法

**修改内容**：
- 将 `beijing_now` 转换为字符串：`beijing_now_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')`
- 在 SQL 中使用 `%s::timestamp` 进行类型转换
- 所有时间参数都使用字符串格式

## 🚀 应用修复

### 1. 重启后端服务

```bash
cd /Users/van/dev/source/claudecode_src/StockGuru

# 停止后端
kill $(cat logs/.backend.pid)

# 重启后端
cd stockguru-web/backend
source .env
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../../logs/backend.log 2>&1 &
echo $! > ../../logs/.backend.pid
cd ../..
```

### 2. 验证修复

#### 方法 1：查看新的同步记录

```bash
# 启动一个新的同步任务
python3 scripts/test_copy_sync.py --date 2025-10-21

# 查看同步状态
./scripts/view_sync_logs.sh -s
```

#### 方法 2：直接查询数据库

```sql
-- 查看最新的同步记录
SELECT 
    sync_date,
    status,
    start_time,
    end_time,
    TO_CHAR(start_time, 'YYYY-MM-DD HH24:MI:SS') as start_time_str,
    TO_CHAR(end_time, 'YYYY-MM-DD HH24:MI:SS') as end_time_str
FROM daily_sync_status
WHERE sync_date >= CURRENT_DATE - INTERVAL '3 days'
ORDER BY sync_date DESC;
```

#### 方法 3：通过 API 查看

```bash
# 查看同步状态
curl http://localhost:8000/api/v1/sync-status/status | python3 -m json.tool
```

## 📊 预期结果

修复后，时间应该显示为北京时间：

| 字段 | 修复前 | 修复后 |
|------|--------|--------|
| start_time | 2025/10/21 07:19:58 | 2025/10/21 15:19:58 |
| end_time | 2025/10/21 07:19:54 | 2025/10/21 15:19:54 |

## ⚠️ 注意事项

### 1. 历史数据

**问题**：已有的历史数据仍然是 UTC 时间

**解决方案**：可以选择性地更新历史数据

```sql
-- 将历史数据的时间加 8 小时（谨慎使用）
UPDATE daily_sync_status
SET 
    start_time = start_time + INTERVAL '8 hours',
    end_time = end_time + INTERVAL '8 hours',
    updated_at = updated_at + INTERVAL '8 hours'
WHERE sync_date < CURRENT_DATE;
```

**建议**：
- 如果历史数据不多，可以手动更新
- 如果历史数据很多，建议保持原样，只修复新数据
- 或者在前端显示时进行时区转换

### 2. 数据库表结构

**长期方案**：修改表结构使用 `TIMESTAMP WITH TIME ZONE`

```sql
-- 备份数据
CREATE TABLE daily_sync_status_backup AS SELECT * FROM daily_sync_status;

-- 修改列类型
ALTER TABLE daily_sync_status 
ALTER COLUMN start_time TYPE TIMESTAMP WITH TIME ZONE USING start_time AT TIME ZONE 'Asia/Shanghai';

ALTER TABLE daily_sync_status 
ALTER COLUMN end_time TYPE TIMESTAMP WITH TIME ZONE USING end_time AT TIME ZONE 'Asia/Shanghai';

ALTER TABLE daily_sync_status 
ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'Asia/Shanghai';

ALTER TABLE daily_sync_status 
ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'Asia/Shanghai';
```

**注意**：
- 这个操作会锁表，建议在维护窗口执行
- 执行前务必备份数据
- 当前的字符串方案已经足够，可以暂不修改表结构

### 3. 前端显示

如果前端需要显示时间，确保：
- 从 API 获取的时间已经是北京时间字符串
- 不需要再进行时区转换
- 直接显示即可

## 🔧 故障排除

### 问题 1：时间仍然不正确

**检查**：
1. 确认后端服务已重启
2. 确认使用的是新的同步记录
3. 检查数据库连接的时区设置

**解决**：
```bash
# 检查数据库时区
psql $NEON_DATABASE_URL -c "SHOW timezone;"

# 如果需要，设置连接时区
psql $NEON_DATABASE_URL -c "SET timezone = 'Asia/Shanghai';"
```

### 问题 2：部分记录正确，部分不正确

**原因**：可能有多个地方在更新同步状态

**检查**：
```bash
# 搜索所有更新同步状态的代码
grep -r "UPDATE daily_sync_status" --include="*.py"
grep -r "INSERT INTO daily_sync_status" --include="*.py"
```

### 问题 3：前端显示时间错误

**检查**：前端是否进行了额外的时区转换

**解决**：确保前端直接显示从 API 获取的时间字符串

## 📝 测试清单

- [ ] 后端服务已重启
- [ ] 新的同步任务时间正确
- [ ] API 返回的时间正确
- [ ] 前端显示的时间正确
- [ ] 日志中的时间正确

## 📚 相关文档

- [数据同步指南](SYNC_GUIDE.md)
- [日志查看指南](docs/SYNC_LOGS_GUIDE.md)
- [数据库Schema](stockguru-web/database/daily_sync_status_schema.sql)

---

**修复时间**: 2025-10-21  
**修复人员**: StockGuru Team  
**状态**: ✅ 已修复
