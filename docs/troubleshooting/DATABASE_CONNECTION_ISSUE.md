# 🔍 数据库连接问题说明

## 问题现象

Web界面查询2025-10-16的数据时，显示"**不满足返回所有结果**"，查不到任何数据。

## 根本原因

**数据在两个不同的数据库中！**

### 当前状态

| 组件 | 使用的数据库 | 连接方式 | 数据量 |
|------|------------|---------|--------|
| **测试脚本** (`test_copy_sync.py`) | Neon PostgreSQL | psycopg2直连 | ✅ 31690条 |
| **Web API** (`daily_stock.py`) | Supabase | REST API | ❌ 0条（或旧数据） |

### 问题详解

1. **测试脚本写入Neon数据库**
   ```python
   # test_copy_sync.py
   database_url = os.getenv('DATABASE_URL')  # Neon数据库
   conn = psycopg2.connect(database_url)
   # 数据写入Neon: 5274条 (2025-10-16)
   ```

2. **Web API查询Supabase数据库**
   ```python
   # daily_stock.py
   from app.core.supabase import get_supabase_client
   supabase = get_supabase_client()  # Supabase REST API
   # 查询Supabase: 0条或旧数据
   ```

3. **结果**: 数据和查询不在同一个数据库！

---

## 解决方案

### 方案1: 统一使用Neon数据库（推荐）✅

**优点**:
- ✅ 性能更好（直连比REST API快3-5倍）
- ✅ 功能更强（支持COPY等高级特性）
- ✅ 成本更低（Neon免费额度更大）

**实施步骤**:

#### 1. 修改API使用PostgreSQL直连

创建新的数据库连接模块：

```python
# app/core/database.py
import os
import psycopg2
from psycopg2 import pool

_connection_pool = None

def get_db_pool():
    """获取数据库连接池"""
    global _connection_pool
    if _connection_pool is None:
        database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        _connection_pool = pool.ThreadedConnectionPool(
            1, 20,  # 最小/最大连接数
            database_url
        )
    return _connection_pool

def get_db_connection():
    """获取数据库连接"""
    pool = get_db_pool()
    return pool.getconn()

def return_db_connection(conn):
    """归还数据库连接"""
    pool = get_db_pool()
    pool.putconn(conn)
```

#### 2. 修改daily_stock.py

```python
# 替换
from app.core.supabase import get_supabase_client

# 为
from app.core.database import get_db_connection, return_db_connection

# 查询示例
@router.post("/query")
async def query_daily_stock_data(request: QueryRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 构建SQL查询
        sql = """
            SELECT * FROM daily_stock_data
            WHERE trade_date >= %s AND trade_date <= %s
        """
        params = [request.start_date, request.end_date]
        
        if request.change_pct_min is not None:
            sql += " AND change_pct >= %s"
            params.append(request.change_pct_min)
        
        if request.change_pct_max is not None:
            sql += " AND change_pct <= %s"
            params.append(request.change_pct_max)
        
        sql += f" ORDER BY {request.sort_by} {request.sort_order}"
        sql += " LIMIT %s OFFSET %s"
        params.extend([request.page_size, (request.page - 1) * request.page_size])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        cursor.close()
        return {"data": results, "total": len(results)}
        
    finally:
        return_db_connection(conn)
```

---

### 方案2: 数据同步到Supabase

**优点**:
- ✅ 无需修改API代码
- ✅ 保持现有架构

**缺点**:
- ❌ 需要维护两个数据库
- ❌ 数据同步延迟
- ❌ 额外的同步成本

**实施步骤**:

```python
# scripts/sync_to_supabase.py
import os
import psycopg2
from supabase import create_client

# 从Neon读取
neon_url = os.getenv('DATABASE_URL')
neon_conn = psycopg2.connect(neon_url)
cursor = neon_conn.cursor()

cursor.execute("""
    SELECT * FROM daily_stock_data
    WHERE trade_date = '2025-10-16'
""")
data = cursor.fetchall()

# 写入Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

for row in data:
    supabase.table('daily_stock_data').insert({
        'stock_code': row[1],
        'stock_name': row[2],
        'trade_date': str(row[3]),
        # ... 其他字段
    }).execute()
```

---

### 方案3: 修改测试脚本写入Supabase

**优点**:
- ✅ 无需修改API

**缺点**:
- ❌ 性能差（REST API慢）
- ❌ 功能受限（不支持COPY）
- ❌ 不推荐

---

## 推荐方案

**✅ 方案1: 统一使用Neon数据库**

理由：
1. 性能最好（直连 vs REST API）
2. 功能最强（支持COPY、事务等）
3. 成本最低（Neon免费额度大）
4. 架构最简单（只维护一个数据库）

---

## 快速验证

### 1. 确认数据在哪里

```bash
# 查询Neon数据库
python scripts/check_database_data.py
# 输出: 31690条，2025-10-16有5274条 ✅

# 查询Supabase数据库
# 通过Web界面查询
# 结果: 0条或旧数据 ❌
```

### 2. 临时解决方案

在修改API之前，可以：

**选项A**: 直接连接Neon数据库查询
```bash
# 使用psql或DBeaver等工具
psql "$DATABASE_URL" -c "SELECT * FROM daily_stock_data WHERE trade_date = '2025-10-16' LIMIT 10"
```

**选项B**: 使用测试脚本查询
```bash
python scripts/test_query.py
```

---

## 后续步骤

1. ✅ **确认**: 数据在Neon，API查询Supabase
2. 🔄 **决策**: 选择方案1（推荐）
3. 🛠️ **实施**: 修改API使用PostgreSQL直连
4. ✅ **测试**: 验证Web界面可以查询到数据
5. 📝 **文档**: 更新部署文档

---

## 相关文件

- 测试脚本: `scripts/test_copy_sync.py` (写入Neon)
- Web API: `stockguru-web/backend/app/api/daily_stock.py` (查询Supabase)
- 数据库配置: `stockguru-web/backend/app/core/supabase.py`
- 环境变量: `stockguru-web/backend/.env`

---

**创建时间**: 2025-10-17  
**问题状态**: 已识别  
**推荐方案**: 方案1 - 统一使用Neon数据库  
**优先级**: 高
