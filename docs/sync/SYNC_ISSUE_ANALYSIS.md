# 数据同步问题深度分析报告

## 📊 问题概述

**时间范围**: 2025-09-08 至 2025-09-10  
**严重程度**: 🔴 高危

### 核心问题

| 日期 | 状态 | 总数 | 成功 | 失败 | 失败率 | 实际数据 | 问题 |
|------|------|------|------|------|--------|----------|------|
| 2025-09-08 | success | 5372 | 4769 | 0 | 0% | 5269 | ⚠️ 成功数与实际不符 (+500) |
| 2025-09-09 | failed | 5372 | 18 | 5354 | **99.7%** | 18 | 🔴 几乎完全失败 |
| 2025-09-10 | failed | 5373 | 3135 | 2238 | **41.7%** | 3032 | 🔴 大量失败 |

## 🔍 问题分析

### 1. 核心问题：计数逻辑错误

**发现的异常**：
- ✅ 2025-09-08: 成功数 4769，但数据库有 5269 条（多了 500 条）
- ❌ 2025-09-09: 成功数 18，失败数 5354，但实际只有 18 条数据
- ⚠️ 2025-09-10: 成功数 3135，但数据库只有 3032 条（少了 103 条）

**问题根源**：
```python
# 当前的计数逻辑有问题
success_count = 成功获取数据的股票数
failed_count = 获取失败的股票数
total_records = 应该是实际插入数据库的记录数

# 但实际上：
# 1. success_count 可能包含了已存在的数据（重复尝试）
# 2. failed_count 可能重复计数
# 3. total_records 计算不准确
```

### 2. 2025-09-09 的灾难性失败

**现象**：
- 5372 只股票，只成功 18 只（0.3% 成功率）
- 5354 只失败（99.7% 失败率）

**可能原因**：
1. **数据源问题**：baostock 在该日期可能有问题
2. **网络问题**：大量请求超时
3. **数据库连接问题**：连接池耗尽或超时
4. **代码逻辑问题**：错误处理不当导致连锁失败

### 3. 2025-09-10 的部分失败

**现象**：
- 成功 3135 只（58.3%）
- 失败 2238 只（41.7%）

**分析**：
- 比 09-09 好，但仍然失败率过高
- 可能是从 09-09 的问题中部分恢复

### 4. 数据一致性问题

**09-08 的异常**：
```
同步记录显示：成功 4769
数据库实际：5269 条
差异：+500 条
```

**可能原因**：
1. 重复同步但计数器没有正确处理
2. 已存在的数据被重新插入（ON CONFLICT DO NOTHING）
3. 计数逻辑在处理已存在数据时有bug

## 🐛 代码问题定位

### 问题1：计数逻辑混乱

**当前代码**（`test_copy_sync.py`）：
```python
# 问题：success 和 failed 的计数可能不准确
success = 0
failed = 0

for stock in stocks:
    try:
        data = fetch_data(stock)
        if data:
            success += 1  # ❌ 即使数据已存在也会 +1
        else:
            failed += 1
    except:
        failed += 1  # ❌ 可能重复计数

# 最终更新
total_records = actual_count  # ❌ 这个值可能不是实际插入的数量
success_count = success       # ❌ 包含了已存在的数据
failed_count = failed         # ❌ 可能重复计数
```

### 问题2：错误处理不当

```python
# 当前代码可能在遇到错误时没有正确恢复
try:
    data = bs.query_history_k_data_plus(...)
except Exception as e:
    failed += 1
    # ❌ 没有记录具体错误
    # ❌ 没有重试机制
    # ❌ 可能导致后续股票也失败
```

### 问题3：数据库操作问题

```python
# 使用 ON CONFLICT DO NOTHING
INSERT INTO daily_stock_data ... ON CONFLICT DO NOTHING

# 问题：
# 1. 无法区分"新插入"和"已存在"
# 2. 计数器会把已存在的也算作成功
# 3. 导致 success_count 不准确
```

## 💡 解决方案

### 方案1：修复计数逻辑

```python
def sync_with_accurate_counting(sync_date):
    """准确计数的同步逻辑"""
    
    # 初始化计数器
    stats = {
        'total_stocks': 0,      # 总股票数
        'fetch_success': 0,     # 成功获取数据
        'fetch_failed': 0,      # 获取失败
        'insert_new': 0,        # 新插入记录
        'insert_skip': 0,       # 跳过（已存在）
        'insert_error': 0       # 插入错误
    }
    
    for stock in get_all_stocks():
        stats['total_stocks'] += 1
        
        try:
            # 1. 获取数据
            data = fetch_stock_data(stock, sync_date)
            
            if data is None or data.empty:
                stats['fetch_failed'] += 1
                continue
            
            stats['fetch_success'] += 1
            
            # 2. 插入数据库（返回实际插入的行数）
            inserted_rows = insert_to_db(data)
            
            if inserted_rows > 0:
                stats['insert_new'] += inserted_rows
            else:
                stats['insert_skip'] += 1
                
        except Exception as e:
            stats['fetch_failed'] += 1
            log_error(stock, sync_date, str(e))
    
    # 3. 更新同步状态（使用准确的计数）
    update_sync_status(
        sync_date=sync_date,
        status='success' if stats['fetch_failed'] == 0 else 'failed',
        total_records=stats['total_stocks'],
        success_count=stats['insert_new'],  # 只计算新插入的
        failed_count=stats['fetch_failed'],
        remarks=f"获取成功{stats['fetch_success']}, 失败{stats['fetch_failed']}, "
                f"新插入{stats['insert_new']}, 已存在{stats['insert_skip']}"
    )
```

### 方案2：增强错误处理

```python
def fetch_with_retry(stock_code, sync_date, max_retries=3):
    """带重试的数据获取"""
    
    for attempt in range(max_retries):
        try:
            data = bs.query_history_k_data_plus(
                stock_code,
                fields="date,code,open,high,low,close,volume,amount,...",
                start_date=sync_date,
                end_date=sync_date,
                frequency="d",
                adjustflag="3"
            )
            
            if data.error_code == '0':
                return data.data
            else:
                # 记录 baostock 返回的错误
                log_warning(f"{stock_code}: baostock error {data.error_code}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待后重试
                continue
            else:
                log_error(f"{stock_code}: {str(e)}")
                return None
    
    return None
```

### 方案3：改进数据库插入

```python
def insert_with_tracking(conn, data, sync_date):
    """跟踪插入结果的数据库操作"""
    
    cur = conn.cursor()
    
    # 使用 ON CONFLICT DO UPDATE 来跟踪
    insert_sql = """
        INSERT INTO daily_stock_data (
            stock_code, stock_name, trade_date, 
            open_price, close_price, high_price, low_price,
            volume, amount, change_pct, ...
        ) VALUES %s
        ON CONFLICT (stock_code, trade_date) 
        DO UPDATE SET updated_at = NOW()
        RETURNING (xmax = 0) AS inserted
    """
    
    # 批量插入并获取结果
    result = execute_values(
        cur, insert_sql, data, 
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ...)",
        fetch=True
    )
    
    # 统计新插入和更新的数量
    new_inserts = sum(1 for row in result if row[0])
    updates = len(result) - new_inserts
    
    conn.commit()
    
    return {
        'new': new_inserts,
        'updated': updates,
        'total': len(result)
    }
```

### 方案4：添加详细日志

```python
import logging

# 配置日志
logging.basicConfig(
    filename=f'sync_{sync_date}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def sync_with_logging(sync_date):
    """带详细日志的同步"""
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"开始同步 {sync_date}")
    
    for i, stock in enumerate(stocks):
        try:
            logger.debug(f"[{i+1}/{len(stocks)}] 处理 {stock}")
            
            data = fetch_data(stock, sync_date)
            
            if data is None:
                logger.warning(f"{stock}: 无数据")
                continue
            
            result = insert_data(data)
            logger.info(f"{stock}: 插入 {result['new']} 条新记录")
            
        except Exception as e:
            logger.error(f"{stock}: 失败 - {str(e)}", exc_info=True)
    
    logger.info(f"同步完成 {sync_date}")
```

## 🔧 修复步骤

### 步骤1：停止当前同步任务

```bash
# 通过 API 停止（如果有停止接口）
# 或者重启后端服务
```

### 步骤2：修复同步代码

需要修改的文件：
- `scripts/test_copy_sync.py`
- `stockguru-web/backend/app/services/daily_data_sync_service_neon.py`

### 步骤3：清理错误数据

```sql
-- 删除 09-09 和 09-10 的错误数据
DELETE FROM daily_stock_data WHERE trade_date IN ('2025-09-09', '2025-09-10');

-- 重置同步状态
UPDATE daily_sync_status 
SET status = 'pending', 
    success_count = 0, 
    failed_count = 0,
    remarks = '待重新同步（已修复计数逻辑）'
WHERE sync_date IN ('2025-09-09', '2025-09-10');
```

### 步骤4：重新同步

```bash
# 使用修复后的代码重新同步
python scripts/test_copy_sync.py --date 2025-09-09
python scripts/test_copy_sync.py --date 2025-09-10
```

### 步骤5：验证结果

```sql
-- 验证数据量
SELECT 
    trade_date,
    COUNT(*) as records,
    COUNT(DISTINCT stock_code) as stocks
FROM daily_stock_data
WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-10'
GROUP BY trade_date
ORDER BY trade_date;

-- 应该看到每天约 4000-5000 条记录
```

## 📋 预防措施

### 1. 添加数据验证

```python
def validate_sync_result(sync_date, stats):
    """验证同步结果"""
    
    warnings = []
    
    # 检查成功率
    if stats['failed_count'] > stats['total_records'] * 0.1:
        warnings.append(f"失败率过高: {stats['failed_count']}/{stats['total_records']}")
    
    # 检查数据量
    if stats['success_count'] < 4000:
        warnings.append(f"数据量偏少: {stats['success_count']} < 4000")
    
    # 检查一致性
    db_count = get_db_count(sync_date)
    if abs(db_count - stats['success_count']) > 10:
        warnings.append(f"计数不一致: DB={db_count}, 记录={stats['success_count']}")
    
    if warnings:
        send_alert(sync_date, warnings)
    
    return len(warnings) == 0
```

### 2. 添加监控告警

```python
def monitor_sync_health():
    """监控同步健康度"""
    
    # 检查最近的同步
    recent_syncs = get_recent_syncs(days=7)
    
    for sync in recent_syncs:
        if sync['status'] == 'failed':
            alert(f"同步失败: {sync['sync_date']}")
        
        if sync['failed_count'] > sync['total_records'] * 0.1:
            alert(f"失败率过高: {sync['sync_date']}")
```

### 3. 改进同步策略

```python
# 分批同步，避免一次性处理太多
BATCH_SIZE = 500

for batch in chunks(all_stocks, BATCH_SIZE):
    sync_batch(batch, sync_date)
    time.sleep(1)  # 避免请求过快
```

## 📊 修复后的预期结果

| 日期 | 状态 | 总数 | 成功 | 失败 | 数据库记录 | 一致性 |
|------|------|------|------|------|-----------|--------|
| 2025-09-09 | success | ~5373 | ~5200 | <100 | ~5200 | ✅ 一致 |
| 2025-09-10 | success | ~5373 | ~5200 | <100 | ~5200 | ✅ 一致 |

## 🎯 总结

### 核心问题
1. **计数逻辑错误**：success_count 包含了已存在的数据
2. **错误处理不足**：导致连锁失败
3. **缺乏验证**：没有及时发现异常

### 解决方案
1. ✅ 修复计数逻辑（区分新插入和已存在）
2. ✅ 增强错误处理（重试机制）
3. ✅ 添加数据验证（自动检测异常）
4. ✅ 改进日志记录（便于排查）

### 下一步
1. 停止当前同步任务
2. 应用代码修复
3. 清理错误数据
4. 重新同步 09-09 和 09-10
5. 验证结果
