# StockGuru Neon 部署指南

> 从 Supabase 迁移到 Neon 的完整部署流程

## 📋 部署架构

- **前端**: Vercel (Next.js)
- **后端**: Render (FastAPI)
- **数据库**: Neon PostgreSQL
- **成本**: $0/月 (全部使用免费套餐)

---

## 🗄️ 第一步：创建 Neon 数据库

### 1.1 注册并创建项目

1. 访问 [Neon Console](https://console.neon.tech/)
2. 使用 GitHub 账号登录
3. 点击 "Create Project"
4. 项目设置：
   - **Project Name**: `stockguru`
   - **Region**: 选择离你最近的区域（如 `AWS Asia Pacific (Singapore)`）
   - **PostgreSQL Version**: 16 (最新版本)

### 1.2 获取数据库连接信息

创建完成后，复制连接字符串：

```
postgresql://[user]:[password]@[host]/[database]?sslmode=require
```

示例：
```
postgresql://stockguru_owner:npg_xxxxxx@ep-xxx-xxx.ap-southeast-1.aws.neon.tech/stockguru?sslmode=require
```

**保存以下信息**：
- ✅ 完整连接字符串
- ✅ Host
- ✅ Database name
- ✅ User
- ✅ Password

---

## 🔧 第二步：初始化数据库结构

### 2.1 连接到 Neon 数据库

使用 psql 或 Neon SQL Editor：

```bash
# 方法1: 使用 psql
psql "postgresql://[user]:[password]@[host]/[database]?sslmode=require"

# 方法2: 使用 Neon Console 的 SQL Editor
# 直接在网页上执行 SQL
```

### 2.2 执行数据库脚本

按顺序执行以下 SQL 文件：

#### ① 创建主表结构
```bash
# 在 Neon SQL Editor 中执行
cat stockguru-web/database/daily_stock_data_schema.sql
```

**包含的表**：
- `daily_stock_data` - 每日股票交易数据
- `sync_logs` - 数据同步日志

#### ② 创建同步状态表
```bash
cat stockguru-web/database/daily_sync_status_schema.sql
```

**包含的表**：
- `daily_sync_status` - 每日同步状态追踪

#### ③ 创建同步进度表
```bash
cat stockguru-web/database/sync_progress_schema.sql
```

**包含的表**：
- `sync_progress` - 同步进度详情

#### ④ 优化索引（可选）
```bash
cat stockguru-web/database/optimize_indexes.sql
```

### 2.3 验证数据库结构

```sql
-- 检查所有表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 应该看到以下表：
-- ✅ daily_stock_data
-- ✅ sync_logs
-- ✅ daily_sync_status
-- ✅ sync_progress
```

---

## 🚀 第三步：部署后端到 Render

### 3.1 准备后端代码

确保以下文件存在：

```bash
stockguru-web/backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── api/
│   └── services/
├── requirements.txt
└── .env.example
```

### 3.2 创建 Render 服务

1. 访问 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New +" → "Web Service"
3. 连接 GitHub 仓库
4. 配置服务：

**基本设置**：
- **Name**: `stockguru-api`
- **Region**: `Singapore` (或离你最近的)
- **Branch**: `main`
- **Root Directory**: `stockguru-web/backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**实例类型**：
- **Instance Type**: `Free` (免费套餐)

### 3.3 配置环境变量

在 Render 的 "Environment" 标签页添加：

```bash
# 数据库连接（使用 Neon 连接字符串）
DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require
NEON_DATABASE_URL=postgresql://[user]:[password]@[host]/[database]?sslmode=require

# Python 环境
PYTHON_VERSION=3.12.0

# 日志级别
LOG_LEVEL=INFO
```

**⚠️ 重要**：
- 删除所有 Supabase 相关的环境变量：
  - ❌ `SUPABASE_URL`
  - ❌ `SUPABASE_KEY`
  - ❌ `SUPABASE_DB_PASSWORD`

### 3.4 部署并验证

1. 点击 "Create Web Service"
2. 等待部署完成（约 3-5 分钟）
3. 获取后端 URL：`https://stockguru-api.onrender.com`
4. 测试健康检查：

```bash
curl https://stockguru-api.onrender.com/health
# 应该返回: {"status": "healthy"}
```

---

## 🌐 第四步：部署前端到 Vercel

### 4.1 准备前端代码

确保以下文件存在：

```bash
frontend/
├── app/
├── components/
├── lib/
├── package.json
├── next.config.mjs
└── .env.local.example
```

### 4.2 创建 Vercel 项目

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 "Add New..." → "Project"
3. 导入 GitHub 仓库
4. 配置项目：

**项目设置**：
- **Framework Preset**: `Next.js`
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (自动检测)
- **Output Directory**: `.next` (自动检测)

### 4.3 配置环境变量

在 Vercel 的 "Environment Variables" 添加：

```bash
# 后端 API 地址（使用 Render 的 URL）
NEXT_PUBLIC_API_URL=https://stockguru-api.onrender.com
```

**⚠️ 重要**：
- 删除所有 Supabase 相关的环境变量：
  - ❌ `NEXT_PUBLIC_SUPABASE_URL`
  - ❌ `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 4.4 部署并验证

1. 点击 "Deploy"
2. 等待部署完成（约 2-3 分钟）
3. 获取前端 URL：`https://stockguru.vercel.app`
4. 访问网站验证功能

---

## 📊 第五步：初始化历史数据（可选）

### 5.1 本地初始化（推荐）

如果需要导入历史数据：

```bash
# 1. 配置本地环境变量
export NEON_DATABASE_URL="postgresql://[user]:[password]@[host]/[database]?sslmode=require"

# 2. 运行初始化脚本（同步最近30天数据）
cd /Users/van/dev/source/claudecode_src/StockGuru
python3 scripts/init_historical_data.py --days 30

# 3. 或者使用测试脚本同步指定日期
python3 scripts/test_copy_sync.py --date 2025-10-18 --all
```

### 5.2 通过 Web 界面同步

1. 访问 `https://stockguru.vercel.app/sync-status`
2. 选择日期范围
3. 点击"开始同步"
4. 等待同步完成

---

## ✅ 第六步：验证部署

### 6.1 后端健康检查

```bash
# 1. 健康检查
curl https://stockguru-api.onrender.com/health

# 2. 数据库连接测试
curl https://stockguru-api.onrender.com/api/v1/daily/stats

# 3. 同步状态查询
curl https://stockguru-api.onrender.com/api/v1/sync-status/sync/batch/active
```

### 6.2 前端功能测试

访问以下页面验证：

- ✅ 首页：`https://stockguru.vercel.app/`
- ✅ 查询页面：`https://stockguru.vercel.app/query`
- ✅ 同步页面：`https://stockguru.vercel.app/sync-status`

### 6.3 定时任务验证

检查后端日志，确认定时任务已启动：

```
[INFO] 定时任务调度器已启动
[INFO] - 每日19点: 同步当日数据
[INFO] - 每日8点: 检查缺失数据
```

---

## 🔄 第七步：数据迁移（如果需要）

### 7.1 从 Supabase 导出数据

```bash
# 使用 pg_dump 导出
pg_dump "postgresql://[supabase-connection-string]" \
  --table=daily_stock_data \
  --table=sync_logs \
  --table=daily_sync_status \
  --data-only \
  --file=stockguru_data.sql
```

### 7.2 导入到 Neon

```bash
# 使用 psql 导入
psql "postgresql://[neon-connection-string]" < stockguru_data.sql
```

### 7.3 验证数据

```sql
-- 检查记录数
SELECT COUNT(*) FROM daily_stock_data;
SELECT COUNT(*) FROM daily_sync_status;

-- 检查日期范围
SELECT MIN(trade_date), MAX(trade_date) FROM daily_stock_data;
```

---

## 🎯 第八步：配置 CORS（如果需要）

如果遇到跨域问题，检查后端 CORS 配置：

```python
# stockguru-web/backend/app/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stockguru.vercel.app",  # 生产环境
        "http://localhost:3000",         # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 环境变量总结

### Render (后端)
```bash
DATABASE_URL=postgresql://[neon-connection-string]
NEON_DATABASE_URL=postgresql://[neon-connection-string]
PYTHON_VERSION=3.12.0
LOG_LEVEL=INFO
```

### Vercel (前端)
```bash
NEXT_PUBLIC_API_URL=https://stockguru-api.onrender.com
```

### 本地开发
```bash
# .env
DATABASE_URL=postgresql://[neon-connection-string]
NEON_DATABASE_URL=postgresql://[neon-connection-string]

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚨 常见问题

### 1. Render 部署失败

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 确保 requirements.txt 包含所有依赖
pip freeze > requirements.txt
```

### 2. 数据库连接超时

**问题**: `SSL connection has been closed unexpectedly`

**解决**: 已在代码中添加 keepalives 参数
```python
# app/core/database.py
keepalives=1,
keepalives_idle=30,
keepalives_interval=10,
keepalives_count=5
```

### 3. Vercel 环境变量不生效

**问题**: 前端无法连接后端

**解决**:
1. 确保环境变量以 `NEXT_PUBLIC_` 开头
2. 重新部署前端（环境变量修改后需要重新部署）

### 4. Render Free Tier 休眠

**问题**: 15分钟无请求后服务休眠

**解决**: 
- 使用 UptimeRobot 等服务定期 ping
- 或升级到付费套餐

---

## 📊 性能监控

### Neon 数据库监控

1. 访问 [Neon Console](https://console.neon.tech/)
2. 查看 "Monitoring" 标签页
3. 监控指标：
   - 连接数
   - 查询性能
   - 存储使用量

### Render 服务监控

1. 访问 [Render Dashboard](https://dashboard.render.com/)
2. 查看服务日志
3. 监控指标：
   - CPU 使用率
   - 内存使用率
   - 请求响应时间

### Vercel 部署监控

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 查看 "Analytics" 标签页
3. 监控指标：
   - 页面访问量
   - 响应时间
   - 错误率

---

## ✅ 部署检查清单

### 数据库 (Neon)
- [ ] 创建 Neon 项目
- [ ] 执行所有数据库脚本
- [ ] 验证表结构
- [ ] 测试数据库连接

### 后端 (Render)
- [ ] 连接 GitHub 仓库
- [ ] 配置环境变量
- [ ] 部署成功
- [ ] 健康检查通过
- [ ] 定时任务启动

### 前端 (Vercel)
- [ ] 连接 GitHub 仓库
- [ ] 配置环境变量
- [ ] 部署成功
- [ ] 页面访问正常
- [ ] API 调用成功

### 功能验证
- [ ] 数据查询功能
- [ ] 数据同步功能
- [ ] 定时任务执行
- [ ] Excel 导出功能

---

## 🎉 完成！

恭喜！你已经成功将 StockGuru 从 Supabase 迁移到 Neon 并部署上线。

**访问地址**：
- 🌐 前端：`https://stockguru.vercel.app`
- 🔧 后端：`https://stockguru-api.onrender.com`
- 🗄️ 数据库：Neon Console

**下一步**：
1. 配置定时任务监控
2. 设置数据备份策略
3. 优化查询性能
4. 添加更多功能

---

## 📞 支持

如有问题，请查看：
- Neon 文档：https://neon.tech/docs
- Render 文档：https://render.com/docs
- Vercel 文档：https://vercel.com/docs
