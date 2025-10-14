# 📈 StockGuru Web 版

股票短线复盘助手 - 前后端分离 Web 应用

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Python 3.11+
- Git

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/stockguru-web.git
cd stockguru-web
```

#### 2. 配置 Supabase
1. 访问 https://supabase.com 创建项目
2. 在 SQL Editor 执行 `database/schema.sql`
3. 获取 URL 和 Key

#### 3. 配置环境变量

**后端**
```bash
cd backend
cp .env.example .env
# 编辑 .env 填入 Supabase 信息
```

**前端**
```bash
cd frontend
cp .env.local.example .env.local
# 编辑 .env.local 填入配置
```

#### 4. 启动服务

**后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs
```

**前端**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

## 📦 部署

### 后端部署到 Render
1. 连接 GitHub 仓库
2. 选择 backend 目录
3. 添加环境变量
4. 自动部署

### 前端部署到 Vercel
1. 导入 GitHub 仓库
2. Root Directory: frontend
3. 添加环境变量
4. 一键部署

## 📚 文档

- [迁移方案](../web-migration-plan.md)
- [实现指南](../web-implementation-guide.md)
- [API 文档](http://localhost:8000/docs)

## 🛠️ 技术栈

- 前端: Next.js 14 + TypeScript + TailwindCSS
- 后端: FastAPI + Python
- 数据库: Supabase (PostgreSQL)
- 部署: Vercel + Render

## 📝 许可证

MIT License
