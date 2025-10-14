# StockGuru Web 版设置指南

## 第一步：初始化前端项目

由于 Next.js 项目文件较多，建议使用官方脚手架创建：

```bash
cd stockguru-web

# 创建 Next.js 项目
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir

# 进入前端目录
cd frontend

# 安装额外依赖
npm install @supabase/supabase-js lightweight-charts
npm install -D @types/node

# 安装 shadcn/ui
npx shadcn-ui@latest init
```

## 第二步：配置 Supabase

1. 访问 https://supabase.com
2. 创建新项目
3. 在 SQL Editor 中执行 `../database/schema.sql`
4. 复制项目 URL 和 anon key

## 第三步：配置环境变量

### 后端 (.env)
```bash
cd ../backend
cp .env.example .env

# 编辑 .env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
FRONTEND_URL=http://localhost:3000
```

### 前端 (.env.local)
```bash
cd ../frontend

# 创建 .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
EOF
```

## 第四步：启动开发服务器

### 终端1 - 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 终端2 - 前端
```bash
cd frontend
npm run dev
```

## 第五步：测试

1. 访问 http://localhost:3000 （前端）
2. 访问 http://localhost:8000/docs （后端 API 文档）
3. 测试筛选功能

## 常见问题

### Q: 后端启动失败？
A: 检查 Python 版本（需要 3.11+）和依赖安装

### Q: 前端无法连接后端？
A: 检查 NEXT_PUBLIC_API_URL 是否正确

### Q: Supabase 连接失败？
A: 检查 URL 和 Key 是否正确复制

## 下一步

完成本地开发后，参考 `web-implementation-guide.md` 进行部署。
