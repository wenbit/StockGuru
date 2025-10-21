# 🚀 StockGuru Neon 部署检查清单

> 按顺序完成以下步骤，确保部署顺利

---

## ✅ 准备阶段

### 1. 账号准备
- [ ] Neon 账号（https://console.neon.tech/）
- [ ] Render 账号（https://dashboard.render.com/）
- [ ] Vercel 账号（https://vercel.com/dashboard）
- [ ] GitHub 仓库已推送最新代码

### 2. 代码检查
- [ ] 所有 Supabase 相关代码已移除或注释
- [ ] `requirements.txt` 包含所有依赖
- [ ] `package.json` 包含所有依赖
- [ ] 数据库脚本文件完整

---

## 🗄️ 数据库部署 (Neon)

### 3. 创建 Neon 项目
- [ ] 登录 Neon Console
- [ ] 创建新项目 `stockguru`
- [ ] 选择区域（推荐：Singapore）
- [ ] 复制连接字符串并保存

### 4. 初始化数据库
- [ ] 方法1：使用自动化脚本
  ```bash
  ./scripts/deploy/init_neon_database.sh 'postgresql://...'
  ```
- [ ] 方法2：手动执行 SQL
  - [ ] 执行 `daily_stock_data_schema.sql`
  - [ ] 执行 `daily_sync_status_schema.sql`
  - [ ] 执行 `sync_progress_schema.sql`

### 5. 验证数据库
- [ ] 检查所有表已创建
  ```sql
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public';
  ```
- [ ] 确认索引已创建
- [ ] 测试数据库连接

---

## 🔧 后端部署 (Render)

### 6. 创建 Render 服务
- [ ] 登录 Render Dashboard
- [ ] 点击 "New +" → "Web Service"
- [ ] 连接 GitHub 仓库
- [ ] 选择分支：`main`

### 7. 配置 Render 服务
- [ ] **Name**: `stockguru-api`
- [ ] **Region**: `Singapore`
- [ ] **Root Directory**: `stockguru-web/backend`
- [ ] **Runtime**: `Python 3`
- [ ] **Build Command**: `pip install -r requirements.txt`
- [ ] **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] **Instance Type**: `Free`

### 8. 配置环境变量
在 Render 添加以下环境变量：

- [ ] `DATABASE_URL` = `postgresql://...`（Neon 连接字符串）
- [ ] `NEON_DATABASE_URL` = `postgresql://...`（同上）
- [ ] `PYTHON_VERSION` = `3.12.0`
- [ ] `LOG_LEVEL` = `INFO`

### 9. 部署后端
- [ ] 点击 "Create Web Service"
- [ ] 等待部署完成（3-5分钟）
- [ ] 复制后端 URL：`https://stockguru-api.onrender.com`

### 10. 验证后端
- [ ] 访问健康检查：`https://stockguru-api.onrender.com/health`
- [ ] 测试 API：`https://stockguru-api.onrender.com/api/v1/daily/stats`
- [ ] 检查日志确认定时任务启动

---

## 🌐 前端部署 (Vercel)

### 11. 创建 Vercel 项目
- [ ] 登录 Vercel Dashboard
- [ ] 点击 "Add New..." → "Project"
- [ ] 导入 GitHub 仓库
- [ ] 选择分支：`main`

### 12. 配置 Vercel 项目
- [ ] **Framework Preset**: `Next.js`
- [ ] **Root Directory**: `frontend`
- [ ] **Build Command**: 自动检测
- [ ] **Output Directory**: 自动检测

### 13. 配置环境变量
在 Vercel 添加以下环境变量：

- [ ] `NEXT_PUBLIC_API_URL` = `https://stockguru-api.onrender.com`

### 14. 部署前端
- [ ] 点击 "Deploy"
- [ ] 等待部署完成（2-3分钟）
- [ ] 复制前端 URL：`https://stockguru.vercel.app`

### 15. 验证前端
- [ ] 访问首页
- [ ] 测试查询页面
- [ ] 测试同步页面
- [ ] 检查浏览器控制台无错误

---

## 📊 数据初始化（可选）

### 16. 初始化历史数据
选择以下方法之一：

#### 方法1：本地脚本
- [ ] 配置环境变量
  ```bash
  export NEON_DATABASE_URL='postgresql://...'
  ```
- [ ] 运行同步脚本
  ```bash
  python3 scripts/test_copy_sync.py --date 2025-10-18 --all
  ```

#### 方法2：Web 界面
- [ ] 访问 `https://stockguru.vercel.app/sync-status`
- [ ] 选择日期范围
- [ ] 点击"开始同步"

#### 方法3：从 Supabase 迁移
- [ ] 导出 Supabase 数据
  ```bash
  pg_dump "postgresql://[supabase-url]" \
    --table=daily_stock_data \
    --data-only > data.sql
  ```
- [ ] 导入到 Neon
  ```bash
  psql "postgresql://[neon-url]" < data.sql
  ```

---

## 🔍 功能验证

### 17. 核心功能测试
- [ ] **数据查询**
  - [ ] 按日期查询
  - [ ] 按涨跌幅筛选
  - [ ] 分页功能
  - [ ] Excel 导出

- [ ] **数据同步**
  - [ ] 手动同步单日
  - [ ] 批量同步
  - [ ] 进度显示
  - [ ] 状态更新

- [ ] **定时任务**
  - [ ] 检查后端日志
  - [ ] 确认任务已注册
  - [ ] 等待19:00验证自动同步

### 18. 性能测试
- [ ] 查询响应时间 < 2秒
- [ ] 同步速度 > 4股/秒
- [ ] 页面加载时间 < 3秒

---

## 🔒 安全检查

### 19. 环境变量安全
- [ ] 数据库密码未泄露
- [ ] `.env` 文件已加入 `.gitignore`
- [ ] GitHub 仓库无敏感信息

### 20. CORS 配置
- [ ] 后端 CORS 仅允许前端域名
- [ ] 生产环境禁用 `allow_origins=["*"]`

---

## 📝 文档更新

### 21. 更新文档
- [ ] README.md 更新部署说明
- [ ] 环境变量示例文件已更新
- [ ] 部署指南已完善

---

## 🎯 上线后任务

### 22. 监控设置
- [ ] 配置 Neon 数据库监控
- [ ] 配置 Render 日志监控
- [ ] 配置 Vercel Analytics

### 23. 备份策略
- [ ] 启用 Neon 自动备份
- [ ] 设置定期数据导出
- [ ] 测试恢复流程

### 24. 性能优化
- [ ] 检查慢查询
- [ ] 优化数据库索引
- [ ] 配置 CDN（如需要）

---

## ✅ 最终检查

### 25. 全面测试
- [ ] 所有页面可访问
- [ ] 所有 API 正常工作
- [ ] 定时任务正常执行
- [ ] 数据同步正常
- [ ] 无控制台错误

### 26. 文档归档
- [ ] 保存所有连接字符串（安全存储）
- [ ] 记录部署日期和版本
- [ ] 更新部署文档

---

## 🎉 部署完成！

**访问地址**：
- 🌐 前端：https://stockguru.vercel.app
- 🔧 后端：https://stockguru-api.onrender.com
- 🗄️ 数据库：Neon Console

**下一步**：
1. 分享给用户测试
2. 收集反馈
3. 持续优化

---

## 📞 问题排查

如遇到问题，检查：
1. 环境变量是否正确
2. 数据库连接是否正常
3. 后端日志是否有错误
4. 前端控制台是否有错误
5. CORS 配置是否正确

**常用命令**：
```bash
# 查看后端日志
curl https://stockguru-api.onrender.com/health

# 测试数据库连接
psql "postgresql://..." -c "SELECT 1;"

# 重新部署前端
vercel --prod

# 重新部署后端
# 在 Render Dashboard 点击 "Manual Deploy"
```
