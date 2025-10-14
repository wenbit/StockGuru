# 📈 StockGuru Web 版迁移方案（最终优化版）

**版本**: V2.0  
**日期**: 2025-10-14  
**状态**: 已优化，可执行  

---

## 一、方案概述

### 核心目标
- ✅ 简便易用：最小化配置，开箱即用
- ✅ 敏捷开发：8天完成，快速迭代
- ✅ 前后端分离：职责清晰，独立部署
- ✅ 完全免费：使用免费服务，零成本运行
- ✅ GitHub管理：版本控制 + 自动化CI/CD
- ✅ 一键部署：Vercel + Render 自动部署

### 技术栈

| 层级 | 技术 | 版本 | 理由 |
|------|------|------|------|
| 前端 | Next.js | 14.x | Vercel原生支持 |
| UI | TailwindCSS + shadcn/ui | latest | 快速开发 |
| 图表 | Lightweight Charts | latest | 专业金融图表 |
| 后端 | FastAPI | 0.110+ | Python生态 |
| 数据库 | Supabase | latest | 免费 |
| 前端部署 | Vercel | - | 自动部署 |
| 后端部署 | Render | - | 免费额度大 |

---

## 二、架构设计

```
GitHub Repository
    ├── frontend/  (Next.js)
    ├── backend/   (FastAPI)
    └── database/  (SQL)
         ↓
    Vercel + Render
         ↓
      Supabase
```

---

## 三、项目结构

```
stockguru/
├── frontend/           # Next.js
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/            # FastAPI
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   └── core/
│   └── requirements.txt
├── database/           # SQL
│   └── schema.sql
└── docs/
```

---

## 四、数据库设计

### 核心表

```sql
-- 任务表
CREATE TABLE tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  date date NOT NULL,
  status text DEFAULT 'pending',
  params jsonb NOT NULL,
  progress int DEFAULT 0,
  result_count int,
  error_message text,
  created_at timestamptz DEFAULT now()
);

-- 结果表
CREATE TABLE results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id uuid REFERENCES tasks(id),
  stock_code text NOT NULL,
  stock_name text NOT NULL,
  momentum_score decimal,
  final_rank int,
  created_at timestamptz DEFAULT now()
);

-- 索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_results_task_id ON results(task_id);
```

---

## 五、部署步骤

### 1. 创建 Supabase 项目
- 访问 supabase.com
- 创建项目
- 执行 database/schema.sql
- 复制 URL 和 Key

### 2. 部署后端到 Render
- 访问 render.com
- 连接 GitHub
- 选择 backend 目录
- 添加环境变量
- 自动部署

### 3. 部署前端到 Vercel
- 访问 vercel.com
- 导入 GitHub 仓库
- 设置 Root Directory: frontend
- 添加环境变量
- 一键部署

---

## 六、开发工作流

```bash
# 克隆仓库
git clone https://github.com/your-username/stockguru.git

# 前端开发
cd frontend
npm install
npm run dev

# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 提交代码
git push
# 自动部署
```

---

## 七、时间估算

| 阶段 | 时间 | 内容 |
|------|------|------|
| Sprint 1 | 3天 | 基础功能 |
| Sprint 2 | 3天 | 完善功能 |
| Sprint 3 | 2天 | 优化部署 |
| **总计** | **8天** | - |

---

## 八、成本清单

| 服务 | 成本 |
|------|------|
| Vercel | $0 |
| Render | $0 |
| Supabase | $0 |
| **总计** | **$0/月** |

---

## 九、关键优化点

### 相比原方案的改进

1. **后端部署**: Railway → Render（免费额度更大）
2. **任务执行**: BackgroundTasks → 同步执行（更可靠）
3. **数据库**: 增加 progress 和 logs 字段
4. **完全免费**: 所有服务都在免费额度内

---

## 十、下一步行动

1. ✅ 创建 GitHub 仓库
2. ✅ 配置 Supabase
3. ✅ 部署后端到 Render
4. ✅ 部署前端到 Vercel
5. ✅ 测试完整流程

---

**详细代码实现请参考项目仓库**
