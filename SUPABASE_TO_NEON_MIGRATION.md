# Supabase 到 Neon 迁移配置指南

## 📋 概述

从 Supabase 迁移到 Neon，Vercel 和 Render 需要调整的配置。

---

## 🔧 Render (后端) 配置调整

### 需要修改的环境变量

#### ❌ 删除 Supabase 相关变量

```bash
# 删除这些环境变量
SUPABASE_URL
SUPABASE_KEY
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_DB_PASSWORD
```

#### ✅ 添加 Neon 数据库连接

```bash
# 主数据库连接（必需）
DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require

# Neon 专用连接（必需）
NEON_DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require

# Python 版本（推荐）
PYTHON_VERSION=3.12.0

# 日志级别（可选）
LOG_LEVEL=INFO
```

### 获取 Neon 连接字符串

1. 登录 [Neon Console](https://console.neon.tech/)
2. 选择你的项目
3. 点击 "Connection Details"
4. 复制连接字符串，格式如下：

```
postgresql://username:password@ep-xxx-xxx.region.aws.neon.tech/dbname?sslmode=require
```

### Render 配置步骤

1. 进入 Render Dashboard
2. 选择你的后端服务（如 `stockguru-api`）
3. 点击 "Environment" 标签页
4. **删除** 所有 Supabase 相关变量
5. **添加** Neon 连接变量
6. 点击 "Save Changes"
7. 服务会自动重新部署

### 其他设置（无需修改）

以下设置保持不变：

```bash
# 构建配置
Root Directory: stockguru-web/backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 实例配置
Instance Type: Free
Region: Singapore (或你选择的区域)
```

---

## 🌐 Vercel (前端) 配置调整

### 需要修改的环境变量

#### ❌ 删除 Supabase 相关变量

```bash
# 删除这些环境变量
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

#### ✅ 保留/确认后端 API 地址

```bash
# 后端 API 地址（保持不变）
NEXT_PUBLIC_API_URL=https://stockguru-api.onrender.com
```

**注意**：如果你的 Render 服务名称不同，需要更新这个 URL。

### Vercel 配置步骤

1. 进入 Vercel Dashboard
2. 选择你的前端项目（如 `stockguru`）
3. 点击 "Settings" → "Environment Variables"
4. **删除** 所有 Supabase 相关变量
5. **确认** `NEXT_PUBLIC_API_URL` 指向正确的 Render 后端
6. 点击 "Save"
7. 重新部署前端（Settings → Deployments → Redeploy）

### 其他设置（无需修改）

以下设置保持不变：

```bash
# 项目配置
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Node.js Version: 18.x (或更高)
```

---

## 📝 代码调整（如果需要）

### 后端代码检查

#### 1. 数据库连接配置

检查 `stockguru-web/backend/app/core/database.py`：

```python
# ✅ 确保使用 Neon 连接
import os

DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')

# ✅ 确保有 SSL 和 keepalives 配置
conn = psycopg2.connect(
    DATABASE_URL,
    sslmode='require',
    keepalives=1,
    keepalives_idle=30,
    keepalives_interval=10,
    keepalives_count=5
)
```

#### 2. 移除 Supabase 客户端

检查是否有使用 Supabase 客户端的代码：

```python
# ❌ 删除这些导入
from supabase import create_client, Client

# ❌ 删除 Supabase 初始化
supabase: Client = create_client(supabase_url, supabase_key)
```

如果有使用 Supabase 的地方，改用直接的 PostgreSQL 查询。

### 前端代码检查

#### 1. 移除 Supabase 客户端

检查 `frontend/lib/` 目录：

```typescript
// ❌ 删除 Supabase 相关文件
// frontend/lib/supabase.ts
// frontend/lib/supabaseClient.ts

// ✅ 确保只使用 API 客户端
// frontend/lib/api-client.ts
```

#### 2. API 调用检查

确保所有数据请求都通过后端 API：

```typescript
// ✅ 正确的方式
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/daily/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(queryParams)
});

// ❌ 不要直接使用 Supabase
// const { data } = await supabase.from('daily_stock_data').select('*');
```

---

## 🗄️ 数据库迁移

### 方案 1：从零开始（推荐）

如果数据量不大或可以重新同步：

1. 在 Neon 创建新数据库
2. 执行数据库脚本创建表结构
3. 通过同步功能重新获取数据

```bash
# 通过 Web 界面同步
访问: https://stockguru.vercel.app/sync-status
选择日期范围，点击"开始同步"

# 或通过脚本同步
python3 scripts/test_copy_sync.py --date 2025-10-18 --all
```

### 方案 2：数据迁移（如果需要保留历史数据）

#### Step 1: 从 Supabase 导出数据

```bash
# 使用 pg_dump 导出
pg_dump "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres" \
  --table=daily_stock_data \
  --table=daily_sync_status \
  --data-only \
  --no-owner \
  --no-privileges \
  --file=stockguru_data.sql
```

#### Step 2: 导入到 Neon

```bash
# 使用 psql 导入
psql "postgresql://[user]:[password]@[host]/[database]?sslmode=require" \
  < stockguru_data.sql
```

#### Step 3: 验证数据

```sql
-- 检查记录数
SELECT COUNT(*) FROM daily_stock_data;
SELECT COUNT(*) FROM daily_sync_status;

-- 检查日期范围
SELECT 
    MIN(trade_date) as earliest,
    MAX(trade_date) as latest,
    COUNT(DISTINCT trade_date) as total_days
FROM daily_stock_data;
```

---

## ✅ 部署验证清单

### 1. Render 后端验证

```bash
# 健康检查
curl https://stockguru-api.onrender.com/health
# 预期: {"status":"healthy"}

# 数据库连接测试
curl https://stockguru-api.onrender.com/api/v1/daily/stats
# 预期: 返回数据统计信息

# 检查日志
# 在 Render Dashboard 查看日志，确认：
# ✅ 数据库连接成功
# ✅ 定时任务启动
# ✅ 无 Supabase 相关错误
```

### 2. Vercel 前端验证

```bash
# 访问页面
https://stockguru.vercel.app/

# 测试功能
✅ 查询页面能正常加载
✅ 数据能正常显示
✅ 同步功能正常工作
✅ 无控制台错误
```

### 3. 数据库验证

```sql
-- 在 Neon Console 执行
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT stock_code) as unique_stocks,
    MIN(trade_date) as earliest_date,
    MAX(trade_date) as latest_date
FROM daily_stock_data;
```

---

## 🚨 常见问题

### 1. Render 部署后无法连接数据库

**症状**：
```
psycopg2.OperationalError: could not connect to server
```

**解决**：
1. 检查 `DATABASE_URL` 是否正确
2. 确保连接字符串包含 `?sslmode=require`
3. 检查 Neon 数据库是否处于活动状态

### 2. Vercel 前端无法连接后端

**症状**：
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**解决**：
1. 检查 `NEXT_PUBLIC_API_URL` 是否正确
2. 确保 Render 服务正在运行（Free tier 可能休眠）
3. 检查 CORS 配置

### 3. 环境变量不生效

**症状**：
- 代码中读取不到环境变量
- 使用了旧的 Supabase 配置

**解决**：
1. **Render**: 修改环境变量后会自动重新部署
2. **Vercel**: 修改环境变量后需要手动重新部署
3. 确保环境变量名称正确（前端必须以 `NEXT_PUBLIC_` 开头）

### 4. Render Free Tier 休眠

**症状**：
- 首次请求很慢（15-30秒）
- 15分钟无请求后服务休眠

**解决方案**：

#### 方案 A: 使用 UptimeRobot（推荐）

1. 注册 [UptimeRobot](https://uptimerobot.com/)
2. 添加监控：
   - URL: `https://stockguru-api.onrender.com/health`
   - 监控间隔: 5分钟
   - 监控类型: HTTP(s)

#### 方案 B: 使用 Vercel Cron Job

在 `vercel.json` 添加：

```json
{
  "crons": [{
    "path": "/api/ping-backend",
    "schedule": "*/5 * * * *"
  }]
}
```

创建 `frontend/app/api/ping-backend/route.ts`：

```typescript
export async function GET() {
  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
    return Response.json({ success: true });
  } catch (error) {
    return Response.json({ success: false }, { status: 500 });
  }
}
```

---

## 📊 性能对比

### Supabase vs Neon

| 指标 | Supabase | Neon | 说明 |
|------|----------|------|------|
| 连接方式 | REST API + Direct | Direct PostgreSQL | Neon 更灵活 |
| 连接池 | 限制较多 | 更灵活 | Neon 支持更多并发 |
| 冷启动 | 较快 | 较快 | 相近 |
| 查询性能 | 良好 | 优秀 | Neon 略快 |
| 免费额度 | 500MB | 512MB | 相近 |
| 地理位置 | 多区域 | 多区域 | 都支持 |

### 迁移后的优势

✅ **更简单的架构**
- 不需要 Supabase 客户端
- 直接使用 PostgreSQL
- 减少依赖

✅ **更好的性能**
- 连接池优化
- 更快的查询速度
- 更稳定的连接

✅ **更灵活的配置**
- 完全控制数据库
- 自定义连接参数
- 更好的监控

---

## 🎯 迁移步骤总结

### 快速迁移（30分钟）

1. **创建 Neon 数据库**（5分钟）
   - 注册 Neon
   - 创建项目
   - 复制连接字符串

2. **初始化数据库**（5分钟）
   - 执行 SQL 脚本
   - 创建表结构

3. **更新 Render 配置**（5分钟）
   - 删除 Supabase 变量
   - 添加 Neon 连接
   - 等待重新部署

4. **更新 Vercel 配置**（5分钟）
   - 删除 Supabase 变量
   - 确认 API URL
   - 重新部署

5. **验证部署**（5分钟）
   - 测试后端 API
   - 测试前端页面
   - 验证数据库连接

6. **同步数据**（5分钟）
   - 通过 Web 界面同步
   - 或运行同步脚本

### 完整迁移（包含数据迁移，1-2小时）

如果需要迁移历史数据，额外增加：

1. **导出 Supabase 数据**（15-30分钟）
2. **导入到 Neon**（15-30分钟）
3. **验证数据完整性**（10分钟）

---

## 📞 支持资源

### 官方文档

- **Neon**: https://neon.tech/docs
- **Render**: https://render.com/docs
- **Vercel**: https://vercel.com/docs

### 项目文档

- [完整部署指南](NEON_DEPLOYMENT_GUIDE.md)
- [数据同步指南](SYNC_GUIDE.md)
- [故障排除](TROUBLESHOOTING.md)

---

## ✅ 迁移完成检查

- [ ] Neon 数据库已创建并初始化
- [ ] Render 环境变量已更新
- [ ] Vercel 环境变量已更新
- [ ] 后端健康检查通过
- [ ] 前端页面正常访问
- [ ] 数据查询功能正常
- [ ] 数据同步功能正常
- [ ] 定时任务正常运行
- [ ] 无 Supabase 相关错误
- [ ] 数据已迁移（如需要）

---

**迁移时间**: 2025-10-21  
**文档版本**: v1.0  
**状态**: ✅ 可用
