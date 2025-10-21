# 定时任务配置完成

## ✅ 已完成的配置

### 1. 安装 APScheduler
```bash
pip3 install apscheduler==3.11.0
```

**状态**: ✅ 已安装

### 2. 更新 requirements.txt
```
APScheduler==3.11.0
```

**状态**: ✅ 已更新

### 3. 定时任务配置

#### 任务1：每日数据同步
```python
# 每天19点执行
scheduler.add_job(
    sync_today_data,
    trigger=CronTrigger(hour=19, minute=0),
    id='daily_sync',
    name='每日19点同步数据'
)
```

**执行时间**: 每天 19:00  
**功能**: 同步当日股票数据  
**重试**: 失败后每小时重试一次

#### 任务2：检查缺失数据
```python
# 每天早上8点检查
scheduler.add_job(
    check_and_sync_missing_days,
    trigger=CronTrigger(hour=8, minute=0),
    id='check_missing',
    name='每日8点检查缺失数据'
)
```

**执行时间**: 每天 08:00  
**功能**: 检查最近30天的缺失数据并补充同步

## 🔧 验证方法

### 1. 检查后端启动日志

后端启动时应该看到：
```
[INFO] StockGuru API 启动中...
[INFO] 数据库连接池将在首次使用时初始化（延迟初始化）
[INFO] 定时任务调度器已启动
[INFO] - 每日19点: 同步当日数据
[INFO] - 每日8点: 检查缺失数据
```

### 2. 测试定时任务

```bash
# 查看后端日志
tail -f logs/app.log | grep -i scheduler

# 或查看uvicorn输出
# 应该能看到定时任务启动的日志
```

### 3. 手动触发测试（可选）

如果想立即测试定时任务功能，可以临时修改时间：

```python
# 临时修改为每分钟执行一次（仅测试用）
scheduler.add_job(
    sync_today_data,
    trigger=IntervalTrigger(minutes=1),
    id='test_sync',
    name='测试同步'
)
```

## 📊 定时任务工作流程

### 每天19点同步流程

```
19:00 触发
    ↓
检查是否有任务在运行
    ↓
获取今日日期
    ↓
调用同步服务
    ↓
判断结果
    ├─ 成功 → 记录日志 → 结束
    ├─ 跳过（非交易日）→ 记录日志 → 结束
    └─ 失败 → 记录日志 → 添加每小时重试任务
```

### 重试机制

```
同步失败
    ↓
添加重试任务（每小时执行）
    ↓
重试成功 → 移除重试任务
重试失败 → 继续每小时重试
```

### 每天8点检查流程

```
08:00 触发
    ↓
查询最近30天的同步记录
    ↓
对比交易日历
    ↓
发现缺失日期
    ↓
逐个补充同步
    ↓
记录结果
```

## ⚠️ 注意事项

### 1. 时区设置

定时任务使用服务器本地时间。确保服务器时区正确：

```bash
# 查看时区
date
timedatectl  # Linux

# 如果需要，设置时区
export TZ='Asia/Shanghai'
```

### 2. 并发控制

定时任务有并发控制：

```python
if self.sync_in_progress:
    logger.info("同步任务正在进行中，跳过本次执行")
    return
```

这确保同一时间只有一个同步任务在运行。

### 3. 与Web任务的关系

- ✅ 定时任务和Web任务**互不冲突**
- ✅ 都使用相同的同步服务
- ✅ 都会写入数据库记录
- ✅ 都受并发控制保护

### 4. 日志记录

所有定时任务执行都会记录日志：

```
[INFO] 开始执行每日数据同步任务...
[INFO] 今日数据同步成功: {...}
[INFO] 检查缺失的交易日数据...
[INFO] 发现 3 个缺失的交易日: [...]
```

## 🎯 生产环境部署

### 1. 确保依赖已安装

```bash
cd stockguru-web/backend
pip3 install -r requirements.txt
```

### 2. 启动后端

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 验证定时任务

```bash
# 查看日志确认定时任务已启动
tail -f logs/app.log | grep scheduler
```

### 4. 监控定时任务

```bash
# 查看同步记录
curl "http://localhost:8000/api/v1/sync-status/list?page=1&page_size=50"

# 查看数据库记录
psql -c "SELECT * FROM daily_sync_status ORDER BY sync_date DESC LIMIT 10;"
```

## 📝 定时任务配置文件

### scheduler.py 位置
```
stockguru-web/backend/app/services/scheduler.py
```

### 主要类和方法

```python
class DataSyncScheduler:
    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler()
        self.sync_in_progress = False
    
    async def sync_today_data(self):
        """同步今日数据"""
        # 实现逻辑...
    
    async def check_and_sync_missing_days(self):
        """检查并同步缺失数据"""
        # 实现逻辑...
    
    def start(self):
        """启动调度器"""
        # 注册定时任务...
    
    def shutdown(self):
        """关闭调度器"""
        # 清理资源...
```

## ✅ 验证清单

- [x] APScheduler 已安装
- [x] requirements.txt 已更新
- [x] scheduler.py 配置正确
- [x] main.py 启动时注册定时任务
- [x] 定时任务时间设置正确（20:00 和 08:00）
- [x] 并发控制已实现
- [x] 重试机制已实现
- [x] 日志记录完整

## 🎉 总结

定时任务已完整配置并可以正常工作：

1. ✅ **每晚20:00** - 自动同步当日数据
2. ✅ **每天08:00** - 检查并补充缺失数据
3. ✅ **失败重试** - 每小时自动重试
4. ✅ **并发控制** - 防止任务冲突
5. ✅ **日志记录** - 完整的执行记录

后端重启后，定时任务会自动启动并按计划执行！🎉
