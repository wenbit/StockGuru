# StockGuru Web 版实现指南

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.11+
- Git

### 本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/stockguru.git
cd stockguru
```

#### 2. 配置环境变量

**前端 (frontend/.env.local)**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

**后端 (backend/.env)**
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
FRONTEND_URL=http://localhost:3000
```

#### 3. 启动开发服务器

**前端**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

**后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs
```

---

## 部署指南

### Supabase 配置

1. 访问 https://supabase.com
2. 创建新项目
3. 在 SQL Editor 执行：

```sql
-- 复制 database/schema.sql 的内容
CREATE TABLE tasks (...);
CREATE TABLE results (...);
-- ...
```

4. 获取连接信息：
   - Project URL
   - anon/public key

### Render 部署（后端）

1. 访问 https://render.com
2. 连接 GitHub 仓库
3. 创建 Web Service
4. 配置：
   - Name: stockguru-api
   - Root Directory: backend
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 添加环境变量：
   - SUPABASE_URL
   - SUPABASE_KEY
   - FRONTEND_URL
6. 部署

### Vercel 部署（前端）

1. 访问 https://vercel.com
2. 导入 GitHub 仓库
3. 配置：
   - Framework: Next.js
   - Root Directory: frontend
4. 添加环境变量：
   - NEXT_PUBLIC_API_URL (Render 后端地址)
   - NEXT_PUBLIC_SUPABASE_URL
   - NEXT_PUBLIC_SUPABASE_ANON_KEY
5. 部署

---

## 核心功能实现

### 后端 API

#### 创建筛选任务
```python
@router.post("/screening")
async def create_screening(request: ScreeningRequest):
    # 1. 创建任务
    # 2. 同步执行筛选
    # 3. 返回结果
    pass
```

#### 获取结果
```python
@router.get("/screening/{task_id}")
async def get_screening_result(task_id: str):
    # 查询任务和结果
    pass
```

### 前端页面

#### 筛选页面
```typescript
// app/screening/page.tsx
- 日期选择
- 参数配置
- 一键筛选按钮
```

#### 结果页面
```typescript
// app/results/[id]/page.tsx
- 轮询任务状态
- 显示进度
- 展示结果列表
```

---

## 常见问题

### Q: Render 服务休眠怎么办？
A: 免费版15分钟无请求会休眠，首次访问需要等待30秒唤醒。

### Q: 筛选超时怎么办？
A: 检查 Render 日志，可能需要优化代码或升级套餐。

### Q: 如何查看日志？
A: 
- 后端：Render Dashboard → Logs
- 前端：Vercel Dashboard → Logs
- 数据库：Supabase Dashboard → Logs

---

## 性能优化

### 后端优化
- 使用数据库连接池
- 添加缓存层（可选）
- 优化查询语句

### 前端优化
- 代码分割
- 图片懒加载
- 使用 SWR 缓存

---

## 安全建议

1. 使用环境变量存储敏感信息
2. 启用 Supabase RLS（生产环境）
3. 添加 API 限流（可选）
4. 定期更新依赖

---

## 监控与维护

### 监控工具
- Render: 内置监控
- Vercel: Analytics
- Supabase: Dashboard

### 日常维护
- 定期检查日志
- 清理旧数据
- 更新依赖包

---

## 扩展功能

### 未来可以添加
- 用户认证
- 自定义筛选参数
- 邮件通知
- 数据导出
- 移动端 App

---

**更多问题请查看项目 README 或提交 Issue**
