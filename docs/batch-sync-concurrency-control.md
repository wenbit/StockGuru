# 批量同步并发控制

## ✅ 功能说明

确保同一时间只能运行一个批量同步任务，防止：
- 数据库连接过多
- 资源竞争
- 数据冲突
- 性能下降

## 🔒 实现方案

### 1. 全局状态管理

```python
# 同步锁
_sync_lock = threading.Lock()

# 同步状态标志
_is_syncing = False
```

### 2. 任务启动检查

```python
@router.post("/sync/batch")
async def trigger_batch_sync(request: BatchSyncRequest):
    # 检查是否有任务正在运行
    global _is_syncing
    with _sync_lock:
        if _is_syncing:
            return {
                "status": "error",
                "message": "已有同步任务正在运行，请等待当前任务完成后再试"
            }
    
    # 启动新任务...
```

### 3. 状态设置

```python
def batch_sync_background(start_date_str, end_date_str, task_id):
    global _is_syncing
    
    try:
        # 设置同步状态
        with _sync_lock:
            _is_syncing = True
        
        # 执行同步...
        
    finally:
        # 释放同步状态（确保总是执行）
        with _sync_lock:
            _is_syncing = False
```

## 🎯 工作流程

### 场景1：正常启动

```
用户A点击"开始同步"
↓
检查 _is_syncing = False
↓
允许启动，设置 _is_syncing = True
↓
执行同步...
↓
完成后设置 _is_syncing = False
```

### 场景2：并发冲突

```
用户A的任务正在运行 (_is_syncing = True)
↓
用户B点击"开始同步"
↓
检查 _is_syncing = True
↓
返回错误："已有同步任务正在运行"
↓
用户B看到提示，等待A完成
```

### 场景3：异常处理

```
任务开始 (_is_syncing = True)
↓
执行过程中发生异常
↓
finally 块执行
↓
设置 _is_syncing = False
↓
下一个任务可以启动
```

## 🔍 技术细节

### 1. 线程安全

使用 `threading.Lock()` 确保状态检查和设置的原子性：

```python
with _sync_lock:
    if _is_syncing:
        # 这里是线程安全的
        return error
```

### 2. 异常安全

使用 `finally` 块确保状态总是被释放：

```python
try:
    _is_syncing = True
    # 同步逻辑...
finally:
    _is_syncing = False  # 总是执行
```

### 3. 全局状态

使用 `global` 关键字修改全局变量：

```python
global _is_syncing
with _sync_lock:
    _is_syncing = True
```

## 📊 用户体验

### 第一个用户
```
点击"开始同步" → ✅ 任务已启动 → 看到进度更新
```

### 第二个用户（任务运行中）
```
点击"开始同步" → ❌ 已有同步任务正在运行，请等待当前任务完成后再试
```

### 第二个用户（任务完成后）
```
点击"开始同步" → ✅ 任务已启动 → 看到进度更新
```

## 🧪 测试场景

### 测试1：单任务正常运行
```bash
# 启动任务
curl -X POST http://localhost:8000/api/v1/sync-status/sync/batch \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-01", "end_date": "2025-10-03"}'

# 预期：返回 task_id，任务开始运行
```

### 测试2：并发冲突检测
```bash
# 第一个任务
curl -X POST http://localhost:8000/api/v1/sync-status/sync/batch \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-01", "end_date": "2025-10-03"}'

# 立即启动第二个任务（第一个还在运行）
curl -X POST http://localhost:8000/api/v1/sync-status/sync/batch \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-04", "end_date": "2025-10-06"}'

# 预期：第二个返回错误 "已有同步任务正在运行"
```

### 测试3：异常后状态恢复
```bash
# 启动一个会失败的任务
# 等待失败
# 再次启动新任务

# 预期：新任务可以正常启动（状态已释放）
```

## ⚠️ 注意事项

### 1. 服务重启
- 状态存储在内存中
- 服务重启后 `_is_syncing` 重置为 `False`
- 如果任务在运行中重启，状态会丢失

### 2. 多实例部署
- 当前方案只适用于单实例
- 如果部署多个后端实例，需要使用分布式锁
- 建议使用 Redis 实现分布式锁

### 3. 超时处理
- 如果任务异常终止（进程被杀死）
- 状态可能不会被释放
- 建议添加超时机制或健康检查

## 🚀 未来优化

### 选项1：分布式锁（Redis）
```python
import redis

redis_client = redis.Redis()

def acquire_sync_lock():
    return redis_client.set('sync_lock', '1', nx=True, ex=3600)

def release_sync_lock():
    redis_client.delete('sync_lock')
```

### 选项2：数据库锁
```sql
-- 创建锁表
CREATE TABLE sync_locks (
    lock_name VARCHAR(50) PRIMARY KEY,
    locked_at TIMESTAMP,
    locked_by VARCHAR(100)
);

-- 获取锁
INSERT INTO sync_locks (lock_name, locked_at, locked_by)
VALUES ('batch_sync', NOW(), 'instance-1')
ON CONFLICT DO NOTHING;
```

### 选项3：任务队列
```python
# 使用 Celery 或 RQ
# 任务队列自动处理并发
@celery.task
def batch_sync_task(start_date, end_date):
    # 同步逻辑
    pass
```

## ✅ 总结

并发控制功能已完成：

1. **✅ 线程安全** - 使用 threading.Lock
2. **✅ 异常安全** - finally 块释放状态
3. **✅ 用户友好** - 清晰的错误提示
4. **✅ 可靠性** - 确保状态总是被释放

**限制**：
- 仅适用于单实例部署
- 服务重启会丢失状态
- 需要手动处理超时情况

**建议**：
- 短期使用当前方案即可
- 长期考虑引入 Redis 分布式锁
- 或使用任务队列（Celery/RQ）
