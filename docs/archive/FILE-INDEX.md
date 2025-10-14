# 📁 StockGuru 文件索引

本文档列出了项目中所有重要文件及其说明。

## 📚 文档文件

### 核心文档
| 文件 | 说明 | 位置 |
|------|------|------|
| README.md | 项目介绍 | 根目录 |
| PROJECT-COMPLETE.md | 项目完成总结 | 根目录 |
| PROJECT-SUMMARY.md | 项目总结（详细） | 根目录 |
| FEATURE-UPDATE.md | 功能更新说明 | 根目录 |
| FILE-INDEX.md | 文件索引（本文件） | 根目录 |

### 技术文档
| 文件 | 说明 | 位置 |
|------|------|------|
| web-migration-plan.md | Web 迁移方案 | 根目录 |
| web-implementation-guide.md | 实现指南 | 根目录 |
| IMPLEMENTATION-STATUS.md | 实现状态 | 根目录 |
| prd.md | 产品需求文档 | 根目录 |

### 问题修复
| 文件 | 说明 | 位置 |
|------|------|------|
| FIXES.md | Hydration 错误修复 | 根目录 |
| FIXES-2.md | 后端启动问题修复 | 根目录 |

### 使用指南
| 文件 | 说明 | 位置 |
|------|------|------|
| QUICKSTART.md | 快速开始 | stockguru-web/ |
| PROJECT-STATUS.md | 项目状态 | stockguru-web/ |
| backend/README.md | 后端说明 | stockguru-web/backend/ |
| frontend/README.md | 前端说明 | frontend/ |

### 开发故事
| 文件 | 说明 | 位置 |
|------|------|------|
| docs/README.md | 文档导航 | docs/ |
| docs/开发故事-短线助手开发记录.md | 灵感来源 | docs/ |

---

## 🛠️ 工具脚本

| 文件 | 说明 | 用途 |
|------|------|------|
| start-all.sh | 一键启动 | 启动前后端服务 |
| stop-all.sh | 一键停止 | 停止所有服务 |
| test-system.sh | 系统测试 | 测试系统状态 |
| diagnose.sh | 系统诊断 | 诊断系统问题 |
| setup-frontend.sh | 前端设置 | 创建前端项目 |
| fix-npm-network.sh | npm 修复 | 修复 npm 网络 |
| check-frontend-status.sh | 前端状态 | 检查前端状态 |

### 后端脚本
| 文件 | 说明 | 位置 |
|------|------|------|
| start.sh | 启动后端 | stockguru-web/backend/ |
| verify-installation.sh | 验证安装 | stockguru-web/backend/ |
| test-api.sh | 测试 API | stockguru-web/backend/ |
| setup-python312.sh | Python 设置 | stockguru-web/backend/ |
| fix-python-version.sh | Python 修复 | stockguru-web/backend/ |
| check-status.sh | 状态检查 | stockguru-web/backend/ |

---

## 💻 代码文件

### 后端代码
```
stockguru-web/backend/app/
├── main.py                 # 入口文件
├── api/
│   └── screening.py        # 筛选 API
├── services/
│   ├── screening_service.py    # 筛选服务
│   └── modules/
│       ├── data_fetcher.py     # 数据获取
│       ├── stock_filter.py     # 股票筛选
│       ├── momentum_calculator.py  # 动量计算
│       └── report_generator.py     # 报告生成
├── core/
│   ├── config.py           # 配置
│   └── supabase.py         # Supabase 客户端
└── schemas/
    └── (数据模型)
```

### 前端代码
```
frontend/
├── app/
│   ├── page.tsx            # 首页
│   ├── layout.tsx          # 布局
│   └── globals.css         # 全局样式
├── lib/
│   └── api-client.ts       # API 客户端
├── public/                 # 静态资源
└── (配置文件)
```

---

## 📊 配置文件

### 后端配置
| 文件 | 说明 | 位置 |
|------|------|------|
| .env | 环境变量 | stockguru-web/backend/ |
| requirements.txt | Python 依赖 | stockguru-web/backend/ |
| Dockerfile | Docker 配置 | stockguru-web/backend/ |

### 前端配置
| 文件 | 说明 | 位置 |
|------|------|------|
| .env.local | 环境变量 | frontend/ |
| package.json | npm 依赖 | frontend/ |
| tsconfig.json | TypeScript 配置 | frontend/ |
| tailwind.config.ts | Tailwind 配置 | frontend/ |
| next.config.ts | Next.js 配置 | frontend/ |

---

## 🗄️ 数据库文件

| 文件 | 说明 | 位置 |
|------|------|------|
| schema.sql | 数据库表结构 | stockguru-web/database/ |

---

## 📝 其他文件

### Git 相关
| 文件 | 说明 | 位置 |
|------|------|------|
| .gitignore | Git 忽略规则 | 根目录 |

### 临时文件
| 文件 | 说明 | 位置 |
|------|------|------|
| .backend.pid | 后端进程 ID | 根目录 |
| .frontend.pid | 前端进程 ID | 根目录 |
| backend.log | 后端日志 | stockguru-web/backend/ |
| frontend.log | 前端日志 | frontend/ |

---

## 📂 目录结构

```
StockGuru/
├── docs/                   # 文档目录
├── stockguru-web/         # Web 版后端
│   ├── backend/           # FastAPI 后端
│   ├── database/          # 数据库设计
│   ├── frontend-examples/ # 前端示例
│   └── docs/              # 后端文档
├── frontend/              # Next.js 前端
├── output/                # 输出目录（原版）
├── *.sh                   # 工具脚本
└── *.md                   # 文档文件
```

---

## 🔍 快速查找

### 我想查看...

**项目介绍** → README.md  
**快速开始** → QUICKSTART.md  
**完整总结** → PROJECT-SUMMARY.md  
**功能更新** → FEATURE-UPDATE.md  
**技术架构** → web-migration-plan.md  
**实现细节** → web-implementation-guide.md  
**问题修复** → FIXES.md, FIXES-2.md  
**开发故事** → docs/开发故事-短线助手开发记录.md  

### 我想运行...

**启动服务** → ./start-all.sh  
**停止服务** → ./stop-all.sh  
**测试系统** → ./test-system.sh  
**诊断问题** → ./diagnose.sh  

### 我想修改...

**后端 API** → stockguru-web/backend/app/api/screening.py  
**筛选逻辑** → stockguru-web/backend/app/services/screening_service.py  
**前端页面** → frontend/app/page.tsx  
**API 客户端** → frontend/lib/api-client.ts  
**环境变量** → .env, .env.local  

---

## 📊 文件统计

- **文档文件**: 20+ 个
- **代码文件**: 30+ 个
- **配置文件**: 10+ 个
- **脚本文件**: 15+ 个
- **总计**: 80+ 个文件

---

**最后更新**: 2025-10-15 00:10
