# 同步状态页面问题排查与修复

## 🔍 问题现象

1. **后台进度面板不显示** - 即使有同步任务在运行
2. **查询按钮一直转圈** - 同步记录列表无法加载

## 🐛 根本原因

### 问题1：后台进度不显示

**原因**：命令行启动的同步任务（`test_copy_sync.py`）不会被记录到Web API的进度追踪字典中

**详细说明**：
- 后台进度监控功能只能检测通过Web API启动的批量同步任务
- 命令行直接运行的脚本不会调用 `/sync/batch` API
- 因此 `_batch_sync_progress` 字典中没有记录
- `/sync/batch/active` API 返回空数据
- 前端检测不到活跃任务

### 问题2：查询一直转圈

**原因**：数据库连接池耗尽或连接超时

**详细说明**：
- 长时间运行的同步任务占用数据库连接
- 连接池中的连接可能已超时但未释放
- 新的查询请求无法获取可用连接
- 导致请求挂起，前端一直等待

## ✅ 解决方案

### 解决方案1：重启后端

**操作**：
```bash
# 杀死旧进程
lsof -ti:8000 | xargs kill -9

# 重启后端
cd stockguru-web/backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**效果**：
- 重置数据库连接池
- 清除所有挂起的连接
- 恢复正常查询功能

### 解决方案2：使用Web界面启动同步

**操作**：
1. 打开 http://localhost:3000/sync-status
2. 在"批量同步"区域选择日期范围
3. 点击"开始同步"按钮
4. 后台进度面板会自动显示

**效果**：
- 任务会被记录到 `_batch_sync_progress`
- 前端可以检测并显示进度
- 实时更新同步状态

## 🔧 长期优化建议

### 1. 统一进度追踪

**问题**：命令行和Web API的同步任务分离

**建议**：
- 创建统一的进度追踪服务
- 使用Redis或数据库存储进度
- 所有同步方式都写入同一个进度存储
- 前端可以检测任何来源的同步任务

**实现示例**：
```python
# 使用数据库表存储进度
CREATE TABLE sync_progress (
    task_id VARCHAR(100) PRIMARY KEY,
    status VARCHAR(20),
    total INT,
    current INT,
    success INT,
    failed INT,
    skipped INT,
    current_date DATE,
    message TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2. 连接池优化

**问题**：长时间任务导致连接耗尽

**建议**：
- 增加连接池大小
- 设置连接超时和自动回收
- 使用连接健康检查

**实现示例**：
```python
connection_pool = ThreadedConnectionPool(
    minconn=5,
    maxconn=30,  # 增加最大连接数
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password,
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5,
    connect_timeout=10  # 添加连接超时
)
```

### 3. 查询超时处理

**问题**：查询挂起时前端无限等待

**建议**：
- 前端添加请求超时
- 显示友好的错误提示
- 提供重试按钮

**实现示例**：
```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

try {
  const res = await fetch(url, {
    signal: controller.signal
  });
  clearTimeout(timeoutId);
  // 处理响应...
} catch (err) {
  if (err.name === 'AbortError') {
    setError('请求超时，请重试');
  }
}
```

## 📝 使用建议

### 开发环境

**推荐方式**：使用Web界面启动同步
```
1. 访问 http://localhost:3000/sync-status
2. 选择日期范围
3. 点击"开始同步"
4. 实时查看进度
```

**命令行方式**：仅用于测试和调试
```bash
# 命令行同步（不会在Web界面显示进度）
python3 scripts/test_copy_sync.py --all --date 2025-10-18
```

### 生产环境

**推荐方式**：
- 使用Web API启动批量同步
- 或使用定时任务（会记录到数据库）
- 避免直接运行命令行脚本

## ⚠️ 故障排查步骤

### 如果查询一直转圈：

1. **检查后端日志**
   ```bash
   # 查看是否有数据库连接错误
   tail -f logs/app.log | grep -i error
   ```

2. **检查数据库连接**
   ```bash
   # 测试数据库连接
   python3 -c "import psycopg2; conn = psycopg2.connect('your_db_url'); print('OK')"
   ```

3. **重启后端**
   ```bash
   # 重置连接池
   lsof -ti:8000 | xargs kill -9
   cd stockguru-web/backend
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **清除浏览器缓存**
   ```
   Cmd+Shift+R (Mac) 或 Ctrl+Shift+R (Windows)
   ```

### 如果后台进度不显示：

1. **确认任务来源**
   - 是通过Web界面启动的吗？
   - 还是命令行启动的？

2. **检查API响应**
   ```bash
   curl http://localhost:8000/api/v1/sync-status/sync/batch/active
   ```

3. **查看浏览器控制台**
   - 打开开发者工具 (F12)
   - 查看Console标签的错误信息
   - 查看Network标签的API请求

## ✅ 验证修复

### 1. 测试查询功能
```
1. 刷新页面
2. 查看同步记录列表是否正常加载
3. 统计卡片是否显示正确数字
```

### 2. 测试批量同步
```
1. 选择日期范围（如今天和明天）
2. 点击"开始同步"
3. 观察后台进度面板是否出现
4. 进度是否实时更新
```

### 3. 测试并发
```
1. 启动一个同步任务
2. 尝试启动第二个任务
3. 应该看到"已有同步任务正在运行"的提示
```

## 📊 当前状态

- ✅ 后端已重启，连接池已重置
- ✅ 前端已重启，代码已更新
- ✅ 查询功能应该恢复正常
- ⚠️ 后台进度监控仅支持Web API启动的任务

## 🎯 下一步

1. **立即操作**：刷新浏览器页面，验证功能
2. **短期**：使用Web界面启动同步任务
3. **长期**：实现统一的进度追踪系统
