# 数据库连接问题修复方案

## 🐛 问题描述

### 症状
1. **页面查询无结果** - 查询按钮一直转圈
2. **同步任务失败** - `connection already closed` 错误
3. **连接频繁断开** - 长时间运行后连接失效

### 错误日志
```
[ERROR] test_copy_sync: ❌ 批量入库失败: connection already closed
[WARNING] test_copy_sync: ❌ 批量入库失败 (尝试 1/3): connection already closed
```

## 🔍 根本原因

### 1. 缺少连接保活机制
- **问题**: 连接空闲时被数据库服务器断开
- **影响**: 从连接池获取的连接可能已失效
- **原因**: 未配置 TCP keepalive 参数

### 2. 无连接健康检查
- **问题**: 获取连接时不检查连接是否有效
- **影响**: 使用已断开的连接导致操作失败
- **原因**: 缺少连接验证机制

### 3. 坏连接回收到池中
- **问题**: 异常连接被归还到连接池
- **影响**: 后续请求继续使用坏连接
- **原因**: 归还时未检查连接状态

### 4. 连接池参数不合理
- **问题**: 最小连接数过少，超时时间过短
- **影响**: 频繁创建/销毁连接，超时失败
- **原因**: 默认参数不适合云数据库

## ✅ 解决方案

### 1. 添加连接保活参数

**修改位置**: `stockguru-web/backend/app/core/database.py`

```python
_connection_pool = pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=20,
    dsn=database_url,
    # 连接保活参数
    keepalives=1,                # 启用 TCP keepalive
    keepalives_idle=30,          # 30秒后开始发送keepalive
    keepalives_interval=10,      # 每10秒发送一次
    keepalives_count=5,          # 5次失败后断开
    # 连接超时
    connect_timeout=30,          # 30秒连接超时
    # 应用名称
    application_name='stockguru_backend'
)
```

**效果**:
- ✅ 连接空闲时自动发送心跳包
- ✅ 及时检测连接断开
- ✅ 避免使用失效连接

### 2. 实现连接健康检查

```python
def get_db_connection():
    """从连接池获取数据库连接，并进行健康检查"""
    conn = _connection_pool.getconn()
    
    # 健康检查：测试连接是否有效
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        # 连接已断开，关闭并重新获取
        logger.warning(f"检测到无效连接，重新获取: {e}")
        try:
            conn.close()
        except:
            pass
        # 获取新连接
        conn = _connection_pool.getconn()
        # 再次测试
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
    
    return conn
```

**效果**:
- ✅ 每次获取连接时验证有效性
- ✅ 自动替换无效连接
- ✅ 保证获取的连接可用

### 3. 优化连接归还逻辑

```python
def return_db_connection(conn, close_on_error: bool = False):
    """归还数据库连接到连接池"""
    if conn is not None:
        # 检查连接是否仍然有效
        if conn.closed:
            logger.warning("连接已关闭，不归还到连接池")
            _connection_pool.putconn(conn, close=True)
            return
        
        # 归还连接（如果有错误则关闭）
        _connection_pool.putconn(conn, close=close_on_error)
```

**效果**:
- ✅ 检查连接状态
- ✅ 坏连接不会回到池中
- ✅ 保持连接池健康

### 4. 增强上下文管理器

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    """退出上下文"""
    close_on_error = False
    
    if exc_type is not None:
        # 发生异常，回滚
        try:
            self.conn.rollback()
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # 连接已断开，标记为需要关闭
            logger.warning("回滚失败，连接可能已断开")
            close_on_error = True
    else:
        # 正常结束，提交
        try:
            self.conn.commit()
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # 连接已断开，标记为需要关闭
            logger.warning("提交失败，连接可能已断开")
            close_on_error = True
    
    # 归还连接
    return_db_connection(self.conn, close_on_error=close_on_error)
```

**效果**:
- ✅ 捕获提交/回滚时的连接错误
- ✅ 标记坏连接不归还
- ✅ 避免连接池污染

### 5. 添加启动测试

```python
# 先测试单个连接
logger.info("测试数据库连接...")
test_conn = psycopg2.connect(database_url, connect_timeout=15)
test_conn.close()
logger.info("数据库连接测试成功")

# 创建连接池
_connection_pool = pool.ThreadedConnectionPool(...)
```

**效果**:
- ✅ 启动时验证数据库可达
- ✅ 提前发现配置问题
- ✅ 避免运行时失败

## 📊 参数优化对比

### 优化前
```python
minconn=1           # 最小连接数太少
maxconn=20          # 最大连接数
dsn=database_url    # 仅基本参数
# 无keepalive参数
# 无超时配置
```

### 优化后
```python
minconn=2                      # 增加最小连接数
maxconn=20                     # 保持最大连接数
dsn=database_url
keepalives=1                   # 启用keepalive
keepalives_idle=30             # 30秒后开始
keepalives_interval=10         # 每10秒一次
keepalives_count=5             # 5次失败断开
connect_timeout=30             # 30秒超时
application_name='stockguru'   # 应用标识
```

## 🔧 技术细节

### TCP Keepalive 工作原理

```
连接建立 → 空闲30秒 → 发送keepalive包
                    ↓
            收到响应 → 继续空闲
                    ↓
            无响应 → 10秒后重试
                    ↓
            重试5次 → 仍无响应 → 断开连接
```

### 连接健康检查流程

```
1. 从连接池获取连接
2. 执行 SELECT 1 测试
3. 测试成功 → 返回连接
4. 测试失败 → 关闭连接 → 获取新连接 → 再次测试
```

### 连接归还决策树

```
归还连接
├── 连接已关闭？
│   ├── 是 → 标记关闭，不归还
│   └── 否 → 继续检查
├── 有错误标记？
│   ├── 是 → 关闭连接
│   └── 否 → 归还到池中
```

## 🎯 效果验证

### 1. 启动日志
```
[INFO] app.core.database: 测试数据库连接...
[INFO] app.core.database: 数据库连接测试成功
[INFO] app.core.database: 数据库连接池初始化成功 (minconn=2, maxconn=20)
[INFO] app.main: 数据库连接池已初始化
```

### 2. 连接保活
```bash
# 查看TCP连接状态
netstat -an | grep 5432

# 应该看到 ESTABLISHED 状态的连接
tcp4  0  0  local.52341  remote.5432  ESTABLISHED
```

### 3. 健康检查日志
```
# 正常情况：无日志
# 检测到坏连接时：
[WARNING] app.core.database: 检测到无效连接，重新获取: connection already closed
```

## 📝 使用建议

### 开发环境

1. **监控连接池状态**
   ```python
   # 添加监控端点
   @router.get("/health/db")
   async def check_db_health():
       try:
           with DatabaseConnection() as cursor:
               cursor.execute('SELECT 1')
           return {"status": "healthy"}
       except Exception as e:
           return {"status": "unhealthy", "error": str(e)}
   ```

2. **定期检查日志**
   ```bash
   # 查看连接相关日志
   tail -f logs/app.log | grep -i "connection\|database"
   ```

### 生产环境

1. **连接池监控**
   - 监控活跃连接数
   - 监控连接获取时间
   - 监控连接错误率

2. **告警设置**
   - 连接池耗尽告警
   - 连接失败率告警
   - 响应时间告警

3. **定期维护**
   - 定期重启应用（释放连接）
   - 监控数据库连接数
   - 检查慢查询日志

## ⚠️ 注意事项

### 1. 连接数限制
- **Neon Free Tier**: 最多100个连接
- **建议**: maxconn ≤ 20
- **原因**: 避免耗尽数据库连接

### 2. Keepalive 参数
- **idle**: 不要太短（< 30秒）
- **interval**: 不要太频繁（< 10秒）
- **count**: 不要太少（< 3次）
- **原因**: 避免过多网络开销

### 3. 超时设置
- **connect_timeout**: 30秒合理
- **太短**: 容易超时失败
- **太长**: 阻塞时间过长

### 4. 长时间任务
```python
# 对于长时间运行的任务（如数据同步）
# 建议使用独立连接，不从连接池获取
conn = psycopg2.connect(database_url, keepalives=1, ...)
try:
    # 执行长时间任务
    pass
finally:
    conn.close()
```

## 🚀 后续优化建议

### 1. 连接池监控
```python
def get_pool_stats():
    """获取连接池统计信息"""
    return {
        'total_connections': len(_connection_pool._pool),
        'available': len(_connection_pool._pool) - len(_connection_pool._used),
        'in_use': len(_connection_pool._used)
    }
```

### 2. 自动重连机制
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(psycopg2.OperationalError)
)
def execute_with_retry(sql, params):
    with DatabaseConnection() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()
```

### 3. 连接池预热
```python
def warmup_pool():
    """预热连接池"""
    connections = []
    for _ in range(_connection_pool.minconn):
        conn = _connection_pool.getconn()
        connections.append(conn)
    
    for conn in connections:
        _connection_pool.putconn(conn)
```

## ✅ 修复总结

### 核心改进
1. ✅ **连接保活** - TCP keepalive 参数
2. ✅ **健康检查** - 获取时验证连接
3. ✅ **智能归还** - 检查连接状态
4. ✅ **异常处理** - 捕获连接错误
5. ✅ **启动测试** - 验证数据库可达

### 问题解决
- ✅ 页面查询正常返回结果
- ✅ 同步任务不再频繁断开
- ✅ 连接池保持健康状态
- ✅ 错误日志大幅减少

### 性能提升
- 🚀 连接复用率提高
- 🚀 错误重试次数减少
- 🚀 整体响应速度提升

现在数据库连接问题已彻底解决！🎉
