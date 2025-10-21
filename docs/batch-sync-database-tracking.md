# 批量同步数据库追踪功能

## 📋 功能说明

批量同步任务现在会**实时写入和更新数据库同步记录表**，可以在数据库层面追踪同步进度。

## ✨ 核心特性

### 1. 任务开始时创建记录
- 启动批量同步时立即在数据库创建记录
- 状态标记为 `syncing`
- 记录同步日期范围和总天数

### 2. 同步过程中实时更新
- 每完成一天的同步，更新数据库记录
- 更新成功数、失败数、总记录数
- 更新进度备注信息

### 3. 任务完成时标记状态
- 同步完成后更新状态为 `success`
- 记录总耗时
- 记录最终统计信息

### 4. 异常处理
- 任务失败时标记为 `failed`
- 记录错误信息
- 保留已完成的部分数据

## 🔄 工作流程

### 阶段1：任务启动

```python
# 创建批量同步记录
batch_record_id = SyncStatusService.create_or_update_status(
    sync_date=mid_date,  # 使用中间日期作为代表
    status='syncing',
    total_records=0,
    success_count=0,
    failed_count=0,
    remarks='批量同步: 2025-10-01 至 2025-10-10, 共10天'
)
```

**数据库记录**：
```sql
INSERT INTO daily_sync_status (
    sync_date, status, total_records, success_count, failed_count,
    remarks, start_time
) VALUES (
    '2025-10-05',  -- 中间日期
    'syncing',
    0, 0, 0,
    '批量同步: 2025-10-01 至 2025-10-10, 共10天',
    CURRENT_TIMESTAMP
);
```

### 阶段2：同步进行中

```python
# 每完成一天，更新记录
SyncStatusService.update_status(
    record_id=batch_record_id,
    status='syncing',
    total_records=total_records,  # 累计总记录数
    success_count=success_count,  # 成功天数
    failed_count=failed_count,    # 失败天数
    remarks='批量同步进度: 3/10天, 成功2, 失败0, 跳过1'
)
```

**数据库更新**：
```sql
UPDATE daily_sync_status 
SET 
    total_records = 15000,
    success_count = 2,
    failed_count = 0,
    remarks = '批量同步进度: 3/10天, 成功2, 失败0, 跳过1'
WHERE id = 123;
```

### 阶段3：任务完成

```python
# 标记完成
SyncStatusService.update_status(
    record_id=batch_record_id,
    status='success',
    total_records=total_records,
    success_count=success_count,
    failed_count=failed_count,
    duration_seconds=int(total_time),
    remarks='批量同步完成: 2025-10-01至2025-10-10, 共10天, 成功8, 失败0, 跳过2, 耗时15分30秒'
)
```

**数据库更新**：
```sql
UPDATE daily_sync_status 
SET 
    status = 'success',
    total_records = 42000,
    success_count = 8,
    failed_count = 0,
    duration_seconds = 930,
    end_time = CURRENT_TIMESTAMP,
    remarks = '批量同步完成: ...'
WHERE id = 123;
```

### 阶段4：异常处理

```python
# 任务失败
SyncStatusService.update_status(
    record_id=batch_record_id,
    status='failed',
    error_message=str(e),
    remarks='批量同步失败: connection timeout'
)
```

## 📊 数据库记录示例

### 批量同步记录

| id | sync_date | status | total_records | success_count | failed_count | remarks | start_time | end_time | duration_seconds |
|----|-----------|--------|---------------|---------------|--------------|---------|------------|----------|------------------|
| 18 | 2025-10-05 | syncing | 15000 | 2 | 0 | 批量同步进度: 3/10天... | 2025-10-18 15:45:00 | NULL | NULL |

**更新后**：

| id | sync_date | status | total_records | success_count | failed_count | remarks | start_time | end_time | duration_seconds |
|----|-----------|--------|---------------|---------------|--------------|---------|------------|----------|------------------|
| 18 | 2025-10-05 | success | 42000 | 8 | 0 | 批量同步完成: 2025-10-01至2025-10-10... | 2025-10-18 15:45:00 | 2025-10-18 16:00:30 | 930 |

## 🎯 查询方法

### 查看批量同步记录

```sql
-- 查看所有批量同步记录（remarks包含"批量同步"）
SELECT * FROM daily_sync_status 
WHERE remarks LIKE '%批量同步%'
ORDER BY start_time DESC;

-- 查看正在进行的批量同步
SELECT * FROM daily_sync_status 
WHERE status = 'syncing' 
  AND remarks LIKE '%批量同步%';

-- 查看最近完成的批量同步
SELECT * FROM daily_sync_status 
WHERE status = 'success' 
  AND remarks LIKE '%批量同步%'
ORDER BY end_time DESC 
LIMIT 10;
```

### API查询

```bash
# 查看同步记录列表
curl "http://localhost:8000/api/v1/sync-status/list?page=1&page_size=50"

# 筛选批量同步记录（通过remarks）
# 前端可以根据remarks字段识别批量同步记录
```

## 🔧 技术实现

### 新增方法

#### 1. `SyncStatusService.update_status()`

```python
@staticmethod
def update_status(
    record_id: int,
    status: str = None,
    total_records: int = None,
    success_count: int = None,
    failed_count: int = None,
    duration_seconds: int = None,
    error_message: str = None,
    remarks: str = None
) -> bool:
    """通过ID更新同步状态记录"""
```

**特点**：
- 通过ID精确更新
- 支持部分字段更新
- 自动处理时间戳
- 返回是否成功

#### 2. 修改 `create_or_update_status()` 返回值

```python
# 修改前
return dict(result) if result else None

# 修改后
return result['id'] if result else None  # 返回ID
```

### 批量同步流程

```python
def batch_sync_background(start_date_str, end_date_str, task_id):
    # 1. 创建记录
    batch_record_id = SyncStatusService.create_or_update_status(...)
    
    # 2. 遍历日期
    for current_date in date_range:
        # 同步单天数据
        sync_single_day(current_date)
        
        # 3. 更新进度（每天）
        SyncStatusService.update_status(
            record_id=batch_record_id,
            status='syncing',
            total_records=total_records,
            success_count=success_count,
            failed_count=failed_count,
            remarks=f'批量同步进度: {processed}/{total_days}天...'
        )
    
    # 4. 标记完成
    SyncStatusService.update_status(
        record_id=batch_record_id,
        status='success',
        duration_seconds=int(total_time),
        remarks='批量同步完成: ...'
    )
```

## 📈 更新频率

### 当前策略

```python
# 每处理完一天，更新一次
if batch_record_id and processed % 1 == 0:
    SyncStatusService.update_status(...)
```

### 可选策略

```python
# 每5天更新一次（减少数据库写入）
if batch_record_id and processed % 5 == 0:
    SyncStatusService.update_status(...)

# 每10%进度更新一次
if batch_record_id and processed % (total_days // 10) == 0:
    SyncStatusService.update_status(...)
```

## 🎨 前端显示

### 识别批量同步记录

```typescript
// 通过remarks字段识别
const isBatchSync = record.remarks?.includes('批量同步');

// 显示特殊标记
{isBatchSync && (
  <span className="badge">批量</span>
)}
```

### 显示进度信息

```typescript
// 从remarks提取进度
const progressMatch = record.remarks?.match(/(\d+)\/(\d+)天/);
if (progressMatch) {
  const [_, current, total] = progressMatch;
  const percent = (parseInt(current) / parseInt(total) * 100).toFixed(1);
  // 显示进度条
}
```

## ⚠️ 注意事项

### 1. 日期选择

**使用中间日期作为代表**：
```python
mid_date = start_date + timedelta(days=total_days // 2)
```

**原因**：
- 避免与单日同步记录冲突
- 便于识别批量同步记录
- 中间日期更具代表性

### 2. 更新频率

**每天更新**：
- ✅ 优点：进度信息最新
- ⚠️ 缺点：数据库写入频繁

**建议**：
- 短期任务（<10天）：每天更新
- 长期任务（>10天）：每5天更新

### 3. 错误处理

```python
try:
    SyncStatusService.update_status(...)
except Exception as e:
    logger.error(f"更新批量同步记录失败: {e}")
    # 不影响主流程，继续同步
```

**原则**：
- 数据库更新失败不应中断同步
- 记录错误日志
- 内存进度不受影响

## 📝 使用示例

### 启动批量同步

```bash
# 通过Web界面
1. 访问 http://localhost:3000/sync-status
2. 选择日期：2025-10-01 至 2025-10-10
3. 点击"开始同步"

# 通过API
curl -X POST "http://localhost:8000/api/v1/sync-status/sync/batch" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-01", "end_date": "2025-10-10"}'
```

### 查看数据库记录

```sql
-- 实时查看进度
SELECT 
    id,
    sync_date,
    status,
    total_records,
    success_count,
    failed_count,
    remarks,
    start_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - start_time)) as elapsed_seconds
FROM daily_sync_status 
WHERE status = 'syncing' 
  AND remarks LIKE '%批量同步%';

-- 查看完成记录
SELECT 
    id,
    sync_date,
    status,
    total_records,
    success_count,
    failed_count,
    duration_seconds,
    remarks
FROM daily_sync_status 
WHERE status = 'success' 
  AND remarks LIKE '%批量同步%'
ORDER BY end_time DESC;
```

### 查看API响应

```bash
# 查看同步记录列表
curl "http://localhost:8000/api/v1/sync-status/list?page=1&page_size=50" | jq

# 响应示例
{
  "status": "success",
  "data": {
    "records": [
      {
        "id": 18,
        "sync_date": "2025-10-05",
        "status": "syncing",
        "total_records": 15000,
        "success_count": 2,
        "failed_count": 0,
        "remarks": "批量同步进度: 3/10天, 成功2, 失败0, 跳过1",
        "start_time": "2025-10-18T15:45:00",
        ...
      }
    ]
  }
}
```

## ✅ 优势

### 1. 数据持久化
- ✅ 进度信息存储在数据库
- ✅ 服务重启后仍可查看
- ✅ 支持历史记录查询

### 2. 多端同步
- ✅ Web界面可以查看
- ✅ API可以查询
- ✅ 数据库可以直接查看

### 3. 监控友好
- ✅ 可以监控同步进度
- ✅ 可以统计成功率
- ✅ 可以分析性能

### 4. 问题排查
- ✅ 记录详细的错误信息
- ✅ 保留完整的时间戳
- ✅ 便于追溯问题

## 🎯 总结

批量同步现在具备完整的数据库追踪功能：

1. ✅ **任务开始** - 创建数据库记录
2. ✅ **进行中** - 实时更新进度
3. ✅ **任务完成** - 标记最终状态
4. ✅ **异常处理** - 记录错误信息

所有批量同步任务都会在 `daily_sync_status` 表中留下完整的追踪记录！🎉
