# 📚 StockGuru 文档目录

本目录包含 StockGuru 项目的所有文档，按类别组织。

## 📁 目录结构

```
docs/
├── README.md                    # 本文件
├── deployment/                  # 🚀 部署文档
├── sync/                        # 🔄 数据同步
├── optimization/                # ⚡ 性能优化
├── troubleshooting/             # 🔧 故障排查
├── reports/                     # 📊 开发报告
├── guides/                      # 📖 使用指南
├── releases/                    # 📋 版本发布
└── archive/                     # 📦 历史归档
```

## 🚀 deployment/ - 部署文档

生产环境部署相关文档：

- `NEON_DEPLOYMENT_GUIDE.md` - Neon 数据库部署指南
- `SUPABASE_TO_NEON_MIGRATION.md` - Supabase 迁移到 Neon
- `CUSTOM_DOMAIN_SETUP.md` - 自定义域名配置（详细版）
- `DOMAIN_CONFIG_GUIDE.md` - 域名配置快速指南
- `DEPLOYMENT_CHECKLIST.md` - 部署检查清单
- `QUICK_DEPLOY.md` - 快速部署指南
- `部署指南-快速开始.md` - 中文快速部署
- `阿里云部署指南.md` - 阿里云部署方案

## 🔄 sync/ - 数据同步

数据同步功能相关文档：

- `SYNC_GUIDE.md` - 数据同步使用指南
- `RESUMABLE_SYNC_GUIDE.md` - 断点续传功能说明
- `RESUMABLE_SYNC_SUMMARY.md` - 断点续传总结
- `SYNC_RECORD_OPTIMIZATION.md` - 同步记录优化
- `SYNC_STATUS_SUMMARY.md` - 同步状态管理
- `BATCH_SYNC_EXPLANATION.md` - 批量同步说明
- `TIMEZONE_FIX.md` - 时区问题修复
- `FIX_SYNC_STATUS.md` - 同步状态修复

## ⚡ optimization/ - 性能优化

性能优化相关文档：

- `FINAL_OPTIMIZATION_PLAN.md` - 最终优化方案
- `FINAL_OPTIMIZATION_SUMMARY.md` - 优化总结
- `OPTIMIZATION_IMPLEMENTED.md` - 已实施优化
- `ADVANCED_OPTIMIZATIONS_COMPLETE.md` - 高级优化完成
- `COPY_OPTIMIZATION_COMPLETE.md` - COPY 命令优化
- `PRIORITY_OPTIMIZATION_REPORT.md` - 优先级优化报告

## 🔧 troubleshooting/ - 故障排查

常见问题和解决方案：

- `FRONTEND_TROUBLESHOOTING.md` - 前端故障排查
- `DATABASE_CONNECTION_ISSUE.md` - 数据库连接问题
- `NETWORK_FIX_REPORT.md` - 网络问题修复
- `EXPORT_FIX.md` - 导出功能修复
- `EXPORT_FIX_422.md` - 422 错误修复
- `COPY_SSL_FIX.md` - SSL 连接修复

## 📊 reports/ - 开发报告

功能开发和问题修复的详细报告：

### 最新报告
- `项目文件整理完成报告.md` - 项目文件规范化整理
- `删除历史记录功能说明.md` - 历史记录功能删除
- `筛选规则说明更新.md` - 筛选规则完善
- `导出功能更新说明.md` - 导出功能更新

### 功能实现
- `Excel导出功能实现报告.md` - Excel 导出功能实现
- `系统架构与功能需求分析报告.md` - 完整的系统架构分析
- `技术指标功能完成报告.md` - 技术指标实现
- `股票详情页完成报告.md` - 详情页功能实现
- `CLI工具完成报告.md` - CLI 工具开发

### 问题修复
- `历史记录Hydration错误修复报告.md` - Hydration 错误修复
- `历史记录字段名错误修复报告.md` - 字段名不匹配修复
- `导出报告和历史记录修复报告.md` - 导出功能修复
- `K线图修复完成报告.md` - K线图功能修复
- `PRD需求核对报告.md` - 需求核对报告

## 📖 guides/ - 使用指南

用户和开发者指南：

- `CLI使用指南.md` - 命令行工具使用说明
- `GIT使用说明.md` - Git 操作指南
- `QUICK-REFERENCE.md` - 快速参考手册
- `web-implementation-guide.md` - Web 实现指南
- `web-migration-plan.md` - Web 迁移计划

## 🚀 releases/ - 版本发布

版本发布说明和路线图：

- `RELEASE-v0.8.md` - v0.8 版本发布说明
- `RELEASE-v0.9.md` - v0.9 版本发布说明
- `v0.9发布说明.md` - v0.9 详细发布说明
- `ROADMAP.md` - 项目路线图

## 📦 archive/ - 历史归档

历史开发文档和总结：

- `DEVELOPMENT-PLAN.md` - 开发计划
- `PROJECT-COMPLETE.md` - 项目完成报告
- `PROJECT-SUMMARY.md` - 项目总结
- `PROGRESS-*.md` - 进度报告
- `TODO.md` - 待办事项
- `FIXES-*.md` - 修复记录
- `FEATURE-*.md` - 功能分析
- 其他历史文档...

## 🔍 快速查找

### 想了解系统架构？
👉 `reports/系统架构与功能需求分析报告.md`

### 想学习如何使用？
👉 `guides/CLI使用指南.md`  
👉 `guides/QUICK-REFERENCE.md`

### 想查看最新版本？
👉 `releases/RELEASE-v0.9.md`

### 想了解某个功能的实现？
👉 `reports/` 目录下查找对应的报告

---

## 📌 重要文档推荐

### 🚀 部署项目
1. `deployment/NEON_DEPLOYMENT_GUIDE.md` - 完整部署流程
2. `deployment/DOMAIN_CONFIG_GUIDE.md` - 域名配置（5分钟）
3. `deployment/DEPLOYMENT_CHECKLIST.md` - 部署检查清单

### 🔄 数据同步
1. `sync/SYNC_GUIDE.md` - 同步功能使用
2. `sync/RESUMABLE_SYNC_GUIDE.md` - 断点续传
3. `sync/SYNC_RECORD_OPTIMIZATION.md` - 同步优化

### 🔧 遇到问题
1. `troubleshooting/FRONTEND_TROUBLESHOOTING.md` - 前端问题
2. `troubleshooting/DATABASE_CONNECTION_ISSUE.md` - 数据库问题
3. `troubleshooting/NETWORK_FIX_REPORT.md` - 网络问题

### ⚡ 性能优化
1. `optimization/FINAL_OPTIMIZATION_PLAN.md` - 优化方案
2. `optimization/FINAL_OPTIMIZATION_SUMMARY.md` - 优化总结

---

*最后更新: 2025-10-21*
