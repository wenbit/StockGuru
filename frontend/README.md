# StockGuru 前端

基于 Next.js 14 + TypeScript + Tailwind CSS 的现代化前端应用。

## 🚀 快速开始

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本
```bash
npm run build
npm start
```

## 📁 项目结构

```
frontend/
├── app/                # Next.js App Router
│   ├── page.tsx       # 首页
│   └── layout.tsx     # 布局
├── lib/               # 工具库
│   └── api-client.ts  # API 客户端
├── public/            # 静态资源
└── .env.local         # 环境变量
```

## 🔧 环境变量

在 `.env.local` 中配置：

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=你的Supabase URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=你的Supabase Key
```

## 📚 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **数据库**: Supabase
- **API**: RESTful API

## 🎯 功能特性

- ✅ 一键筛选股票
- ✅ 实时数据展示
- ✅ 响应式设计
- ✅ 类型安全

## 📝 开发说明

### API 客户端

使用 `lib/api-client.ts` 与后端通信：

```typescript
import { apiClient } from '@/lib/api-client';

// 创建筛选任务
const result = await apiClient.createScreening({
  date: '2024-10-14',
});

// 获取结果
const task = await apiClient.getScreeningResult(taskId);
```

### 添加新页面

在 `app/` 目录下创建新文件夹和 `page.tsx`：

```
app/
├── page.tsx          # /
├── results/
│   └── page.tsx      # /results
└── history/
    └── page.tsx      # /history
```

## 🐛 调试

```bash
# 查看详细日志
npm run dev -- --turbo

# 检查类型错误
npx tsc --noEmit

# 格式化代码
npx prettier --write .
```

## 📦 部署

### Vercel（推荐）

1. 推送代码到 GitHub
2. 在 Vercel 导入项目
3. 添加环境变量
4. 自动部署

### 其他平台

```bash
# 构建
npm run build

# 启动
npm start
```

## ❓ 常见问题

### Q: API 连接失败？
A: 检查 `NEXT_PUBLIC_API_URL` 是否正确，确保后端服务已启动。

### Q: 样式不生效？
A: 检查 Tailwind CSS 配置，运行 `npm run dev` 重新编译。

### Q: 类型错误？
A: 运行 `npm install` 确保所有依赖已安装。

---

**更多信息请查看项目根目录的文档**
