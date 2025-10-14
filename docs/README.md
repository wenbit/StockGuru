# StockGuru 文档中心

欢迎来到 StockGuru 文档中心！这里包含了项目的所有文档和资料。

## 📚 文档导航

### 🚀 快速开始
- [快速启动指南](../stockguru-web/QUICKSTART.md) - 5分钟快速开始
- [项目完成总结](../PROJECT-COMPLETE.md) - 项目整体介绍
- [功能更新说明](../FEATURE-UPDATE.md) - 最新功能介绍

### 📖 开发文档
- [Web 迁移方案](../web-migration-plan.md) - 技术架构设计
- [实现指南](../web-implementation-guide.md) - 详细实现步骤
- [项目状态](../stockguru-web/PROJECT-STATUS.md) - 开发进度追踪

### 🔧 技术文档
- [后端 README](../stockguru-web/backend/README.md) - 后端使用说明
- [前端 README](../frontend/README.md) - 前端开发指南
- [数据库 Schema](../stockguru-web/database/schema.sql) - 数据库表结构

### 🐛 问题修复
- [修复记录 #1](../FIXES.md) - React Hydration 错误修复
- [修复记录 #2](../FIXES-2.md) - 后端启动问题修复
- [实现状态](../IMPLEMENTATION-STATUS.md) - 真实数据接口实现

### 📝 开发故事
- [短线助手开发记录](./开发故事-短线助手开发记录.md) - 项目灵感来源和核心思路

### 🛠️ 工具脚本
- [一键启动](../start-all.sh) - 启动所有服务
- [一键停止](../stop-all.sh) - 停止所有服务
- [系统测试](../test-system.sh) - 测试系统状态
- [系统诊断](../diagnose.sh) - 诊断系统问题

---

## 🎯 按需求查找

### 我想快速开始使用
→ [快速启动指南](../stockguru-web/QUICKSTART.md)

### 我想了解技术架构
→ [Web 迁移方案](../web-migration-plan.md)

### 我遇到了问题
→ [系统诊断](../diagnose.sh) + [问题修复记录](../FIXES.md)

### 我想参与开发
→ [实现指南](../web-implementation-guide.md) + [项目状态](../stockguru-web/PROJECT-STATUS.md)

### 我想了解项目背景
→ [开发故事](./开发故事-短线助手开发记录.md)

---

## 📊 项目概览

### 核心功能
- ✅ 自动筛选强势股
- ✅ 成交量和热度综合评分
- ✅ 动量因子计算
- ✅ 实时进度显示
- ✅ 可视化结果展示

### 技术栈
- **前端**: Next.js 14 + TypeScript + Tailwind CSS
- **后端**: FastAPI + Python 3.12
- **数据库**: Supabase (PostgreSQL)
- **数据源**: pywencai + akshare

### 项目结构
```
StockGuru/
├── docs/                    # 📚 文档中心
├── stockguru-web/          # 🔧 Web 版后端
│   ├── backend/            # FastAPI 后端
│   ├── database/           # 数据库设计
│   └── frontend-examples/  # 前端示例
├── frontend/               # 🎨 Next.js 前端
├── *.sh                    # 🛠️ 工具脚本
└── *.md                    # 📝 文档文件
```

---

## 🚀 快速命令

```bash
# 启动所有服务
./start-all.sh

# 停止所有服务
./stop-all.sh

# 测试系统
./test-system.sh

# 诊断问题
./diagnose.sh

# 查看后端日志
tail -f stockguru-web/backend/backend.log

# 查看前端日志
tail -f frontend/frontend.log
```

---

## 📞 获取帮助

遇到问题时：
1. 查看对应的文档
2. 运行 `./diagnose.sh` 诊断系统
3. 查看日志文件
4. 参考问题修复记录

---

## 🎉 贡献指南

欢迎贡献代码和文档！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

---

**StockGuru - 让短线复盘更高效！** 🚀
