# ⚡ StockGuru 快速部署指南

> 5分钟完成 Neon 部署

---

## 🎯 三步部署

### 第一步：Neon 数据库 (2分钟)

```bash
# 1. 创建 Neon 项目
访问: https://console.neon.tech/
点击: Create Project → 输入 "stockguru" → Create

# 2. 复制连接字符串
格式: postgresql://user:pass@host/db?sslmode=require

# 3. 初始化数据库
./scripts/deploy/init_neon_database.sh 'postgresql://...'
```

### 第二步：Render 后端 (2分钟)

```bash
# 1. 创建服务
访问: https://dashboard.render.com/
点击: New + → Web Service → 连接 GitHub

# 2. 配置
Root Directory: stockguru-web/backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 3. 环境变量
DATABASE_URL=postgresql://...
NEON_DATABASE_URL=postgresql://...
PYTHON_VERSION=3.12.0

# 4. 部署
点击: Create Web Service
```

### 第三步：Vercel 前端 (1分钟)

```bash
# 1. 创建项目
访问: https://vercel.com/dashboard
点击: Add New → Project → 导入 GitHub

# 2. 配置
Root Directory: frontend
Framework: Next.js (自动检测)

# 3. 环境变量
NEXT_PUBLIC_API_URL=https://your-app.onrender.com

# 4. 部署
点击: Deploy
```

---

## ✅ 验证部署

```bash
# 1. 测试后端
curl https://your-app.onrender.com/health

# 2. 访问前端
https://your-app.vercel.app

# 3. 检查功能
- 查询页面
- 同步页面
- 数据导出
```

---

## 📋 环境变量速查

### Render (后端)
```
DATABASE_URL=postgresql://[neon-connection-string]
NEON_DATABASE_URL=postgresql://[neon-connection-string]
PYTHON_VERSION=3.12.0
LOG_LEVEL=INFO
```

### Vercel (前端)
```
NEXT_PUBLIC_API_URL=https://your-app.onrender.com
```

---

## 🚨 常见问题

### 问题1：Render 部署失败
```bash
# 检查 requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 问题2：前端无法连接后端
```bash
# 1. 检查环境变量
NEXT_PUBLIC_API_URL 必须以 NEXT_PUBLIC_ 开头

# 2. 重新部署
修改环境变量后必须重新部署
```

### 问题3：数据库连接超时
```bash
# 已在代码中添加 keepalives 参数
# 无需额外配置
```

---

## 📞 获取帮助

详细文档：
- 📖 完整部署指南：`NEON_DEPLOYMENT_GUIDE.md`
- ✅ 部署检查清单：`DEPLOYMENT_CHECKLIST.md`

在线文档：
- Neon: https://neon.tech/docs
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs

---

## 🎉 完成！

**访问地址**：
- 前端：https://your-app.vercel.app
- 后端：https://your-app.onrender.com

**下一步**：
1. 初始化历史数据
2. 配置监控
3. 开始使用
