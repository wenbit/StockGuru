# 统一的数据同步管理

## ✅ 已完成的统一改造

### 核心问题
之前两个启动方式使用了**不同的同步方法和不同的锁机制**：
- Web界面批量同步：使用 `test_copy_sync.CopySyncTester` + `_is_syncing` 锁
- 定时任务：使用 `daily_data_sync_service` + `self.sync_in_progress` 锁

这导致它们可以同时运行，造成数据库连接冲突！

### 解决方案
创建**统一的同步管理器** (`SyncManager`)，确保：
1. ✅ 所有同步任务使用同一个同步方法
2. ✅ 使用全局锁，同一时间只能有1个同步进程运行
3. ✅ 不能启动多个进程

## 🔧 技术实现

### 1. 统一的同步管理器

**文件**: `stockguru-web/backend/app/services/sync_manager.py`

```python
class SyncManager:
    """统一的同步管理器"""
    
    @staticmethod
    def is_syncing() -> bool:
        """检查是否有同步任务正在运行"""
        global _is_syncing
        with _sync_lock:
            return _is_syncing
    
    @staticmethod
    def acquire_sync_lock(task_type: str, task_info: Dict) -> bool:
        """尝试获取同步锁"""
        global _is_syncing, _current_task_info
        
        with _sync_lock:
            if _is_syncing:
                logger.warning(f"同步任务正在进行中，拒绝新任务: {task_type}")
                return False
            
            _is_syncing = True
            _current_task_info = {
                'task_type': task_type,
                'start_time': datetime.now().isoformat(),
                **task_info
            }
            return True
    
    @staticmethod
    def sync_date_range(
        start_date: date,
        end_date: date,
        task_type: str,
        progress_callback=None
    ) -> Dict:
        """统一的同步方法"""
        # 尝试获取锁
        if not SyncManager.acquire_sync_lock(task_type, task_info):
            return {
                'status': 'rejected',
                'message': '已有同步任务正在运行'
            }
        
        try:
            # 使用 test_copy_sync 的同步逻辑
            # ... 同步代码 ...
        finally:
            SyncManager.release_sync_lock()
```

### 2. Web批量同步改造

**文件**: `stockguru-web/backend/app/api/sync_status.py`

**改造前**：
```python
def batch_sync_background(...):
    global _is_syncing
    with _sync_lock:
        _is_syncing = True
    
    # 直接调用 test_copy_sync
    from test_copy_sync import CopySyncTester
    tester = CopySyncTester()
    tester.test_sync(...)
```

**改造后**：
```python
def batch_sync_background(...):
    sync_manager = get_sync_manager()
    
    # 使用统一的同步管理器
    result = sync_manager.sync_date_range(
        start_date=start_date,
        end_date=end_date,
        task_type='web_batch',
        progress_callback=progress_callback
    )
    
    if result['status'] == 'rejected':
        # 任务被拒绝（已有任务在运行）
        logger.warning(f"批量同步任务被拒绝")
        return
```

### 3. 定时任务改造

**文件**: `stockguru-web/backend/app/services/scheduler.py`

**改造前**：
```python
async def sync_today_data(self):
    if self.sync_in_progress:
        return
    
    self.sync_in_progress = True
    
    # 调用 daily_data_sync_service
    sync_service = get_sync_service()
    result = await sync_service.sync_date_data(today)
```

**改造后**：
```python
async def sync_today_data(self):
    sync_manager = get_sync_manager()
    
    # 检查是否有任务正在运行
    if sync_manager.is_syncing():
        current_task = sync_manager.get_current_task()
        logger.info(f"同步任务正在进行中，跳过: {current_task}")
        return
    
    # 使用统一的同步管理器
    result = sync_manager.sync_date_range(
        start_date=today,
        end_date=today,
        task_type='scheduler_daily'
    )
```

## 🎯 统一管理的特性

### 1. 全局锁机制

```python
# 全局同步锁和状态
_sync_lock = threading.Lock()
_is_syncing = False
_current_task_info: Optional[Dict] = None
```

**特点**：
- ✅ 所有同步任务共享同一个锁
- ✅ 同一时间只能有1个任务获取锁
- ✅ 其他任务会被拒绝

### 2. 任务类型标识

```python
task_type:
- 'web_batch'        # Web界面批量同步
- 'scheduler_daily'  # 定时任务每日同步
- 'scheduler_missing' # 定时任务补充缺失数据
```

**用途**：
- 记录当前运行的任务类型
- 便于日志追踪
- 便于问题排查

### 3. 任务信息追踪

```python
_current_task_info = {
    'task_type': 'web_batch',
    'start_time': '2025-10-18T16:00:00',
    'start_date': '2025-10-01',
    'end_date': '2025-10-10',
    'total_days': 10
}
```

**用途**：
- 查看当前运行的任务
- 拒绝新任务时返回当前任务信息
- 监控和调试

### 4. 拒绝机制

```python
if sync_manager.is_syncing():
    current_task = sync_manager.get_current_task()
    return {
        "status": "error",
        "message": "已有同步任务正在运行",
        "current_task": current_task
    }
```

**特点**：
- ✅ 新任务被拒绝
- ✅ 返回当前任务信息
- ✅ 前端显示友好提示

## 📊 工作流程

### 场景1：Web启动批量同步

```
用户点击"开始同步"
    ↓
检查 sync_manager.is_syncing()
    ├─ False → 获取锁 → 开始同步
    └─ True → 拒绝 → 返回错误信息
```

### 场景2：定时任务触发

```
20:00 定时任务触发
    ↓
检查 sync_manager.is_syncing()
    ├─ False → 获取锁 → 开始同步
    └─ True → 跳过 → 记录日志
```

### 场景3：Web任务运行时定时任务触发

```
15:00 用户启动Web批量同步
    ↓
sync_manager 获取锁
    ↓
20:00 定时任务触发
    ↓
检查 sync_manager.is_syncing() → True
    ↓
跳过本次执行
    ↓
记录日志: "同步任务正在进行中，跳过: web_batch"
```

### 场景4：定时任务运行时用户启动Web同步

```
20:00 定时任务启动
    ↓
sync_manager 获取锁
    ↓
20:05 用户点击"开始同步"
    ↓
检查 sync_manager.is_syncing() → True
    ↓
返回错误: "已有同步任务正在运行"
    ↓
前端显示: "已有同步任务正在运行，请等待当前任务完成后再试"
```

## ✅ 验证方法

### 1. 测试并发控制

```bash
# 终端1：启动Web批量同步
curl -X POST "http://localhost:8000/api/v1/sync-status/sync/batch" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-01", "end_date": "2025-10-10"}'

# 终端2：立即再次启动（应该被拒绝）
curl -X POST "http://localhost:8000/api/v1/sync-status/sync/batch" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-11", "end_date": "2025-10-20"}'

# 预期结果：第二个请求返回错误
{
  "status": "error",
  "message": "已有同步任务正在运行，请等待当前任务完成后再试",
  "current_task": {
    "task_type": "web_batch",
    "start_time": "2025-10-18T16:00:00",
    "start_date": "2025-10-01",
    "end_date": "2025-10-10",
    "total_days": 10
  }
}
```

### 2. 查看当前任务

```python
from app.services.sync_manager import get_sync_manager

sync_manager = get_sync_manager()

# 检查是否有任务运行
if sync_manager.is_syncing():
    current_task = sync_manager.get_current_task()
    print(f"当前任务: {current_task}")
else:
    print("没有任务运行")
```

### 3. 查看日志

```bash
# 查看同步管理器日志
tail -f logs/app.log | grep -i "sync_manager\|获取同步锁\|释放同步锁"

# 预期日志：
# [INFO] sync_manager: 获取同步锁成功: web_batch, 任务信息: {...}
# [INFO] sync_manager: 释放同步锁: {...}
# [WARNING] sync_manager: 同步任务正在进行中，拒绝新任务: scheduler_daily
```

## 🎨 前端显示

### 任务被拒绝时的提示

```typescript
// API 返回
{
  "status": "error",
  "message": "已有同步任务正在运行，请等待当前任务完成后再试",
  "current_task": {
    "task_type": "web_batch",
    "start_time": "2025-10-18T16:00:00",
    "start_date": "2025-10-01",
    "end_date": "2025-10-10"
  }
}

// 前端显示
alert(`已有同步任务正在运行
类型: ${current_task.task_type}
范围: ${current_task.start_date} 至 ${current_task.end_date}
开始时间: ${current_task.start_time}
请等待当前任务完成后再试`);
```

## 📝 代码清单

### 新增文件

1. **`stockguru-web/backend/app/services/sync_manager.py`**
   - 统一的同步管理器
   - 全局锁机制
   - 统一的同步方法

### 修改文件

1. **`stockguru-web/backend/app/api/sync_status.py`**
   - 导入 `sync_manager`
   - 移除局部锁 `_sync_lock`, `_is_syncing`
   - 使用 `sync_manager.sync_date_range()`
   - 使用 `sync_manager.is_syncing()` 检查

2. **`stockguru-web/backend/app/services/scheduler.py`**
   - 导入 `sync_manager`
   - 移除局部锁 `self.sync_in_progress`
   - 使用 `sync_manager.sync_date_range()`
   - 使用 `sync_manager.is_syncing()` 检查

## 🎯 总结

### 改造前的问题

❌ **两个独立的同步系统**：
- Web批量同步：自己的锁 + 自己的方法
- 定时任务：自己的锁 + 自己的方法
- 可以同时运行，造成冲突

### 改造后的优势

✅ **统一的同步管理**：
1. ✅ 所有任务使用同一个同步方法
2. ✅ 全局锁，同一时间只能有1个任务
3. ✅ 任务被拒绝时返回当前任务信息
4. ✅ 完整的日志追踪
5. ✅ 便于监控和调试

### 核心保证

1. **同一时间只能有1个同步进程运行** ✅
2. **不能启动多个进程** ✅
3. **两个启动方式调用同一个同步方法** ✅
4. **统一管理，统一监控** ✅

现在系统已经实现了完整的统一同步管理！🎉
