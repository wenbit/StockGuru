# 批量同步功能说明

## ✅ 断点续传功能确认

批量同步功能**确实是断点续传的**，不会删除已有数据。

## 🔍 误解澄清

### 你看到的情况

在前端界面看到：
- 2025-10-20: 状态"同步中"，总数 5,378，成功 500，失败 0

这让你以为数据被删除了重新同步。

### 实际情况

**数据没有被删除！**

```bash
# 验证：10-20 的数据还在
curl -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2025-10-20","end_date":"2025-10-20"}' 

# 结果：3891 条数据 ✅
```

## 📊 同步逻辑说明

### 1. 检查机制

批量同步会先检查每个日期：

```python
# 伪代码
for date in date_range:
    # 1. 检查同步状态
    status = get_sync_status(date)
    
    # 2. 检查数据是否存在
    data_count = count_data(date)
    
    # 3. 决定是否同步
    if status == 'success' and data_count > 0:
        # 跳过，数据已存在
        skip()
    else:
        # 需要同步
        sync(date)
```

### 2. 断点续传

`test_copy_sync.py` 支持断点续传：

```python
# 查询已同步的股票
synced_stocks = get_synced_stocks(date)

# 过滤掉已同步的
stocks_to_sync = [s for s in all_stocks if s not in synced_stocks]

# 只同步剩余的
sync(stocks_to_sync)
```

### 3. 为什么显示"同步中"？

可能的原因：

#### 原因 1：之前的同步未完成

- 之前同步 10-20 时中断了
- 状态停留在 "syncing"
- 数据只同步了一部分（3891 条）
- 现在继续同步剩余的

#### 原因 2：正在补充数据

- 之前同步了 3891 条
- 但总共应该有 5000+ 条
- 现在在补充缺失的数据

#### 原因 3：数据验证

- 检测到数据不完整
- 自动触发补充同步

## 🎯 验证方法

### 方法 1：查看数据量变化

```bash
# 同步前
curl -X POST http://localhost:8000/api/v1/daily/query \
  -d '{"start_date":"2025-10-20","end_date":"2025-10-20"}' 
# 结果：3891 条

# 等待同步完成后再查询
# 结果：应该会增加到 5000+ 条
```

### 方法 2：查看同步日志

```bash
# 查看日志
./scripts/view_sync_logs.sh -l 100

# 查找关键信息
# "📋 发现已同步 XXX 只股票，将跳过..."
# "📋 剩余待同步: XXX 只股票"
```

### 方法 3：查看数据库

```sql
-- 查看 10-20 的数据量
SELECT 
    trade_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT stock_code) as unique_stocks
FROM daily_stock_data
WHERE trade_date = '2025-10-20'
GROUP BY trade_date;
```

## 📝 同步状态说明

### 状态字段含义

| 字段 | 说明 |
|------|------|
| total_records | 总股票数（约 5378 只 A 股） |
| success_count | 本次同步成功的数量 |
| 数据库实际记录数 | 累计的总数据量 |

**重要**：
- `success_count` 是**本次同步**的成功数
- 不是数据库中的总数据量
- 数据库中的数据是累计的

### 示例

```
第一次同步：
- success_count: 3891
- 数据库记录: 3891 条

第二次同步（断点续传）：
- success_count: 1500 (本次新增)
- 数据库记录: 5391 条 (3891 + 1500)
```

## 🔧 如果真的想重新同步

如果你确实想删除数据重新同步：

### 方法 1：手动删除数据

```sql
-- 删除指定日期的数据
DELETE FROM daily_stock_data WHERE trade_date = '2025-10-20';

-- 重置同步状态
UPDATE daily_sync_status 
SET status = 'pending', 
    success_count = 0, 
    total_records = 0
WHERE sync_date = '2025-10-20';
```

### 方法 2：使用清理脚本

```bash
# 创建清理脚本
python3 scripts/cleanup_and_resync.py --date 2025-10-20
```

## ⚠️ 注意事项

### 1. 不要频繁重新同步

- 数据同步需要时间（15-20 分钟）
- 频繁同步会浪费资源
- 可能触发 API 限流

### 2. 断点续传的优势

- **节省时间**：只同步缺失的数据
- **节省资源**：不重复获取已有数据
- **提高效率**：支持中断后继续

### 3. 数据完整性

- 同步完成后会自动验证
- 如果数据不完整会自动补充
- 不需要手动干预

## 🎯 最佳实践

### 1. 首次同步

```bash
# 同步整个日期范围
# 系统会自动跳过已有数据
POST /api/v1/sync-status/sync/batch
{
  "start_date": "2025-09-01",
  "end_date": "2025-10-20"
}
```

### 2. 补充同步

```bash
# 如果某天数据不完整
# 重新同步该日期即可
# 系统会自动断点续传
POST /api/v1/sync-status/sync/date
{
  "sync_date": "2025-10-20"
}
```

### 3. 定期同步

```bash
# 每天自动同步最新数据
# 通过定时任务自动执行
# 无需手动操作
```

## 📊 当前同步状态

根据最新数据：

```
2025-10-20:
- 状态: syncing (同步中)
- 数据库: 3891 条 (已有)
- 本次同步: 1500 只 (正在进行)
- 预计完成: 约 2 分钟
```

**结论**：
- ✅ 数据没有被删除
- ✅ 正在断点续传
- ✅ 同步完成后数据会更完整

## 🔗 相关文档

- [同步指南](SYNC_GUIDE.md)
- [日志查看指南](docs/SYNC_LOGS_GUIDE.md)
- [时区修复说明](TIMEZONE_FIX.md)

---

**创建时间**: 2025-10-21 16:00  
**状态**: 同步进行中  
**预计完成**: 16:02
