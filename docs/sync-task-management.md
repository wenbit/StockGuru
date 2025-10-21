# 数据同步任务管理规范

## 📋 同步任务启动规则

### ✅ 允许的启动方式

数据同步任务**只能**通过以下2种方式启动：

#### 1. 前端页面批量同步
```
访问: http://localhost:3000/sync-status
操作: 选择日期范围 → 点击"开始同步"按钮
```

**特点**：
- ✅ 用户主动触发
- ✅ 可视化进度显示
- ✅ 实时更新状态
- ✅ 写入数据库记录

#### 2. 后台定时任务
```
时间: 每晚 20:00
触发: APScheduler 自动执行
```

**特点**：
- ✅ 自动执行
- ✅ 同步当日数据
- ✅ 失败自动重试（每小时）
- ✅ 写入数据库记录

### ❌ 禁止的启动方式

#### 1. 命令行直接运行
```bash
# ❌ 不要这样做
python3 scripts/test_copy_sync.py --all --date 2025-10-18
```

**问题**：
- ❌ 不会在Web界面显示进度
- ❌ 可能与Web任务冲突
- ❌ 占用数据库连接
- ❌ 难以监控和管理

#### 2. 后端启动时自动执行
```python
# ❌ 不要在启动事件中执行同步
@app.on_event("startup")
async def startup_event():
    # ❌ 不要这样做
    sync_service.sync_all_data()
```

**问题**：
- ❌ 启动时间过长
- ❌ 可能导致启动失败
- ❌ 无法控制同步时机

## 🔧 当前配置

### 后端启动流程

```python
@app.on_event("startup")
async def startup_event():
    # ✅ 数据库连接池 - 延迟初始化
    logger.info("数据库连接池将在首次使用时初始化")
    
    # ✅ 定时任务调度器 - 仅注册定时任务，不立即执行
    try:
        scheduler = get_scheduler()
        scheduler.start()  # 只启动调度器，不执行同步
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}")
        # 缺少 apscheduler 模块时会失败，这是正常的
```

### 定时任务配置

```python
# 每天19点执行
scheduler.add_job(
    sync_today_data,
    trigger=CronTrigger(hour=19, minute=0),
    id='daily_sync',
    name='每日19点同步数据'
)

# 每天早上8点检查缺失数据
scheduler.add_job(
    check_and_sync_missing_days,
    trigger=CronTrigger(hour=8, minute=0),
    id='check_missing',
    name='每日8点检查缺失数据'
)
```

## 🚫 停止不当的同步任务

### 检查运行中的同步任务

```bash
# 查看所有同步相关进程
ps aux | grep -E "(test_copy_sync|baostock)" | grep -v grep
```

### 停止命令行同步任务

```bash
# 停止 test_copy_sync
pkill -f "test_copy_sync"

# 强制停止（如果上面不行）
pkill -9 -f "test_copy_sync"

# 停止所有 baostock 相关进程
pkill -f "baostock"
```

### 停止后端中的同步任务

如果通过Web API启动了任务但想停止：

```bash
# 重启后端（会中断所有任务）
lsof -ti:8000 | xargs kill -9
cd stockguru-web/backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 监控同步任务

### 1. Web界面监控

```
访问: http://localhost:3000/sync-status
查看: 
- 后台进度面板（有任务时自动显示）
- 同步记录列表
- 统计卡片
```

### 2. API监控

```bash
# 查看活跃任务
curl http://localhost:8000/api/v1/sync-status/sync/batch/active

# 查看任务进度
curl http://localhost:8000/api/v1/sync-status/sync/batch/progress/{task_id}

# 查看同步记录
curl "http://localhost:8000/api/v1/sync-status/list?page=1&page_size=50"
```

### 3. 数据库监控

```sql
-- 查看正在进行的同步
SELECT * FROM daily_sync_status 
WHERE status = 'syncing'
ORDER BY start_time DESC;

-- 查看批量同步记录
SELECT * FROM daily_sync_status 
WHERE remarks LIKE '%批量同步%'
ORDER BY start_time DESC;

-- 查看最近的同步记录
SELECT * FROM daily_sync_status 
ORDER BY created_at DESC 
LIMIT 20;
```

### 4. 日志监控

```bash
# 查看后端日志
tail -f logs/app.log | grep -i sync

# 查看错误日志
tail -f logs/app.log | grep -i error
```

## ⚠️ 常见问题

### Q1: 为什么不能用命令行启动同步？

**原因**：
1. 命令行任务不会写入 `_batch_sync_progress` 字典
2. Web界面无法检测和显示进度
3. 可能与Web任务竞争数据库连接
4. 难以统一管理和监控

**解决**：使用Web界面启动

### Q2: 如何测试同步功能？

**推荐方式**：
```
1. 访问 http://localhost:3000/sync-status
2. 选择小范围日期（如今天和明天）
3. 点击"开始同步"
4. 观察进度面板和数据库记录
```

**不推荐**：
```bash
# ❌ 不要这样测试
python3 scripts/test_copy_sync.py --all
```

### Q3: 定时任务什么时候执行？

**执行时间**：
- 每晚 20:00 - 同步当日数据
- 每天 08:00 - 检查缺失数据

**前提条件**：
- 安装 apscheduler: `pip install apscheduler`
- 后端正常运行
- 数据库连接正常

### Q4: 如何确保没有冲突的同步任务？

**启动前检查**：
```bash
# 1. 检查进程
ps aux | grep -E "(test_copy_sync|baostock)" | grep -v grep

# 2. 停止所有同步进程
pkill -f "test_copy_sync"

# 3. 检查Web任务
curl http://localhost:8000/api/v1/sync-status/sync/batch/active

# 4. 如果有活跃任务，等待完成或重启后端
```

## ✅ 正确的使用流程

### 开发环境

```
1. 启动后端
   cd stockguru-web/backend
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

2. 启动前端
   cd frontend
   npm run dev

3. 访问同步页面
   http://localhost:3000/sync-status

4. 使用Web界面启动同步
   选择日期 → 点击"开始同步"

5. 监控进度
   - 查看进度面板
   - 查看数据库记录
   - 查看后端日志
```

### 生产环境

```
1. 确保 apscheduler 已安装
   pip install apscheduler

2. 启动后端（定时任务自动注册）
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

3. 定时任务自动执行
   - 每天19点同步当日数据
   - 每天8点检查缺失数据

4. 手动同步（如需要）
   - 访问Web界面
   - 选择日期范围
   - 启动批量同步
```

## 📝 最佳实践

### 1. 启动后端前

```bash
# 检查并停止所有同步进程
ps aux | grep -E "(test_copy_sync|baostock)" | grep -v grep
pkill -f "test_copy_sync"
```

### 2. 使用Web界面

```
✅ 总是使用Web界面启动同步
✅ 观察进度面板
✅ 检查数据库记录
✅ 查看错误信息
```

### 3. 避免并发

```
✅ 同一时间只运行一个同步任务
✅ 等待当前任务完成再启动新任务
✅ 使用同步锁防止并发
```

### 4. 监控和日志

```
✅ 定期检查同步记录
✅ 监控数据库连接状态
✅ 查看后端日志
✅ 设置错误告警
```

## 🎯 总结

**核心原则**：
1. ✅ 只通过Web界面或定时任务启动同步
2. ❌ 不要使用命令行直接运行同步脚本
3. ✅ 启动前检查并停止冲突的进程
4. ✅ 使用Web界面监控进度
5. ✅ 定期检查数据库记录

遵循这些规范，可以确保同步任务的稳定性和可管理性！🎉
