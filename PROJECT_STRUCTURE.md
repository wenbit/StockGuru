# StockGuru 项目结构说明

## 📁 项目目录结构

```
StockGuru/
├── README.md                      # 项目说明
├── PROJECT_STRUCTURE.md           # 本文件 - 项目结构说明
├── prd.md                         # 产品需求文档
├── design.md                      # 系统设计文档
├── cascade_rules.md               # Cascade AI 规则配置
│
├── frontend/                      # 前端项目 (Next.js)
│   ├── app/                       # Next.js App Router
│   │   ├── page.tsx              # 首页
│   │   ├── query/                # 查询页面
│   │   ├── screening/            # 筛选页面
│   │   ├── stock/                # 股票详情页
│   │   └── sync-status/          # 数据同步页
│   ├── components/               # React 组件
│   ├── lib/                      # 工具库
│   └── package.json
│
├── stockguru-web/                # Web 完整项目
│   ├── backend/                  # 后端项目 (FastAPI)
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI 入口
│   │   │   ├── api/             # API 路由
│   │   │   ├── core/            # 核心配置
│   │   │   ├── services/        # 业务逻辑
│   │   │   └── schemas/         # 数据模型
│   │   ├── requirements.txt
│   │   └── .env                 # 环境变量（不提交）
│   └── database/                # 数据库脚本
│       ├── daily_stock_data_schema.sql
│       └── daily_sync_status_schema.sql
│
├── scripts/                      # 辅助脚本
│   ├── start/                   # 启动脚本
│   │   ├── start-all.sh        # 一键启动
│   │   └── stop-all.sh         # 停止服务
│   ├── setup/                   # 安装脚本
│   ├── test/                    # 测试脚本
│   └── deploy/                  # 部署脚本
│
├── docs/                         # 📚 文档目录
│   ├── README.md                # 文档索引
│   ├── deployment/              # 🚀 部署文档
│   ├── sync/                    # 🔄 数据同步
│   ├── optimization/            # ⚡ 性能优化
│   ├── troubleshooting/         # 🔧 故障排查
│   ├── reports/                 # 📊 开发报告
│   ├── guides/                  # 📖 使用指南
│   ├── releases/                # 📋 版本发布
│   └── archive/                 # 📦 历史归档
│
├── tests/                        # 测试文件
├── data/                         # 数据目录
│   └── cache/                   # 缓存数据
├── output/                       # 输出目录
│   └── reports/                 # 生成的报告
├── logs/                         # 日志目录
│
├── cli.py                        # CLI 工具入口
├── config.py                     # 全局配置
├── requirements.txt              # Python 依赖
└── .gitignore                   # Git 忽略规则
```

## 📚 核心文档

### 项目文档
- `README.md` - 项目介绍和快速开始
- `prd.md` - 产品需求文档
- `design.md` - 系统设计文档
- `PROJECT_STRUCTURE.md` - 项目结构说明（本文件）

### 部署文档
- `docs/deployment/NEON_DEPLOYMENT_GUIDE.md` - Neon 部署指南
- `docs/deployment/DOMAIN_CONFIG_GUIDE.md` - 域名配置指南
- `docs/deployment/SUPABASE_TO_NEON_MIGRATION.md` - 数据库迁移指南

### 使用指南
- `docs/guides/CLI使用指南.md` - CLI 工具使用
- `docs/guides/QUICK-REFERENCE.md` - 快速参考
- `docs/sync/SYNC_GUIDE.md` - 数据同步指南

## 🚀 快速开始

### 1. 本地开发

```bash
# 启动所有服务
./scripts/start/start-all.sh

# 或分别启动
cd stockguru-web/backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

### 2. 生产部署

参考文档：
- `docs/deployment/NEON_DEPLOYMENT_GUIDE.md`
- `docs/deployment/QUICK_DEPLOY.md`

### 3. 数据同步

```bash
# 手动同步
python scripts/manual_daily_sync.py --date 2025-10-21

# 查看同步状态
python scripts/view_sync_logs.sh
```

## 🔧 开发工具

### 启动脚本
- `scripts/start/start-all.sh` - 一键启动前后端
- `scripts/start/stop-all.sh` - 停止所有服务

### 测试脚本
- `scripts/test/test-real-data.sh` - 测试真实数据
- `scripts/test/diagnose.sh` - 系统诊断

### 部署脚本
- `scripts/deploy/init_neon_database.sh` - 初始化数据库
- `deploy-to-github.sh` - 部署到 GitHub

## 📊 技术栈

### 前端
- **框架**: Next.js 15.5.5 + React 19
- **语言**: TypeScript
- **样式**: Tailwind CSS 4.0
- **图表**: Recharts
- **部署**: Vercel

### 后端
- **框架**: FastAPI
- **语言**: Python 3.12
- **数据库**: PostgreSQL (Neon)
- **部署**: Render

### 数据源
- **pywencai** - 成交额和热度数据
- **akshare** - K线行情数据
- **baostock** - 历史数据同步

## 🌐 在线访问

- **生产环境**: https://stockguru.520178.xyz
- **Vercel 默认**: https://stockguru.vercel.app
- **后端 API**: https://stockguru-api.onrender.com

## 📝 环境变量

### 后端 (.env)
```bash
DATABASE_URL=postgresql://...
NEON_DATABASE_URL=postgresql://...
LOG_LEVEL=INFO
```

### 前端 (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://stockguru-api.onrender.com
```

## 🔍 常用命令

### 开发
```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 启动开发服务器
cd stockguru-web/backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

### 数据同步
```bash
# 同步指定日期
python scripts/manual_daily_sync.py --date 2025-10-21

# 批量同步
python scripts/batch_sync_dates.py --start 2025-10-01 --end 2025-10-21
```

### 部署
```bash
# 提交到 GitHub
git add .
git commit -m "feat: 新功能"
git push origin main

# Vercel 和 Render 会自动部署
```

## 📖 更多文档

查看 `docs/README.md` 获取完整的文档索引。

---

**项目版本**: v0.5  
**最后更新**: 2025-10-21  
**维护者**: wenbit
