#!/bin/bash

# 创建目录结构
mkdir -p docs/reports docs/guides docs/releases docs/archive
mkdir -p scripts/setup scripts/start scripts/test
mkdir -p tests logs

# 移动报告文档
mv Excel导出功能实现报告.md docs/reports/ 2>/dev/null
mv PDF导出功能实现报告.md docs/reports/ 2>/dev/null
mv PDF导出功能实现说明.md docs/reports/ 2>/dev/null
mv HTML报告导出完成报告.md docs/reports/ 2>/dev/null
mv 历史记录Hydration错误修复报告.md docs/reports/ 2>/dev/null
mv 历史记录字段名错误修复报告.md docs/reports/ 2>/dev/null
mv 导出报告和历史记录修复报告.md docs/reports/ 2>/dev/null
mv 导出功能更新说明.md docs/reports/ 2>/dev/null
mv 筛选规则说明更新.md docs/reports/ 2>/dev/null
mv 系统架构与功能需求分析报告.md docs/reports/ 2>/dev/null
mv K线图修复完成报告.md docs/reports/ 2>/dev/null
mv K线图修复说明.md docs/reports/ 2>/dev/null
mv 技术指标功能完成报告.md docs/reports/ 2>/dev/null
mv 股票详情页优化完成报告.md docs/reports/ 2>/dev/null
mv 股票详情页完成报告.md docs/reports/ 2>/dev/null
mv CLI工具完成报告.md docs/reports/ 2>/dev/null
mv PRD需求核对报告.md docs/reports/ 2>/dev/null

# 移动指南文档
mv CLI使用指南.md docs/guides/ 2>/dev/null
mv GIT使用说明.md docs/guides/ 2>/dev/null
mv QUICK-REFERENCE.md docs/guides/ 2>/dev/null
mv web-implementation-guide.md docs/guides/ 2>/dev/null
mv web-migration-plan.md docs/guides/ 2>/dev/null

# 移动发布文档
mv RELEASE-v0.8.md docs/releases/ 2>/dev/null
mv RELEASE-v0.9.md docs/releases/ 2>/dev/null
mv v0.9发布说明.md docs/releases/ 2>/dev/null
mv ROADMAP.md docs/releases/ 2>/dev/null

# 移动归档文档
mv CLAUDE.md docs/archive/ 2>/dev/null
mv CLI工具开发总结.txt docs/archive/ 2>/dev/null
mv DEVELOPMENT-PLAN.md docs/archive/ 2>/dev/null
mv FEATURE-GAP-ANALYSIS.md docs/archive/ 2>/dev/null
mv FEATURE-UPDATE.md docs/archive/ 2>/dev/null
mv FILE-INDEX.md docs/archive/ 2>/dev/null
mv FIXES.md docs/archive/ 2>/dev/null
mv FIXES-2.md docs/archive/ 2>/dev/null
mv FIXES-3.md docs/archive/ 2>/dev/null
mv Git保存完成.txt docs/archive/ 2>/dev/null
mv IMPLEMENTATION-STATUS.md docs/archive/ 2>/dev/null
mv PERFORMANCE-OPTIMIZATION.md docs/archive/ 2>/dev/null
mv PRD-CHANGELOG.md docs/archive/ 2>/dev/null
mv PRD需求完成情况.txt docs/archive/ 2>/dev/null
mv PROGRESS-2025-10-15.md docs/archive/ 2>/dev/null
mv PROGRESS-FINAL.md docs/archive/ 2>/dev/null
mv PROJECT-COMPLETE.md docs/archive/ 2>/dev/null
mv PROJECT-SUMMARY.md docs/archive/ 2>/dev/null
mv TODO.md docs/archive/ 2>/dev/null
mv 开发进度-2025-10-15.md docs/archive/ 2>/dev/null
mv 最终开发总结.md docs/archive/ 2>/dev/null
mv 未完成需求清单.md docs/archive/ 2>/dev/null
mv 本次开发总结.md docs/archive/ 2>/dev/null
mv 项目100%完成报告.txt docs/archive/ 2>/dev/null
mv 项目开发完成总结.md docs/archive/ 2>/dev/null
mv 项目最终状态.md docs/archive/ 2>/dev/null
mv 验收清单.md docs/archive/ 2>/dev/null

# 移动脚本文件
mv start-all.sh scripts/start/ 2>/dev/null
mv stop-all.sh scripts/start/ 2>/dev/null
mv setup-cli.sh scripts/setup/ 2>/dev/null
mv setup-frontend.sh scripts/setup/ 2>/dev/null
mv fix-npm-network.sh scripts/setup/ 2>/dev/null
mv check-frontend-status.sh scripts/test/ 2>/dev/null
mv diagnose.sh scripts/test/ 2>/dev/null
mv test-real-data.sh scripts/test/ 2>/dev/null
mv test-system.sh scripts/test/ 2>/dev/null
mv 验证v0.9功能.sh scripts/test/ 2>/dev/null
mv 验证新功能.sh scripts/test/ 2>/dev/null
mv test_e2e_kline.sh scripts/test/ 2>/dev/null

# 移动测试文件
mv test-momentum.py tests/ 2>/dev/null
mv test_data.py tests/ 2>/dev/null
mv test_kline_api.py tests/ 2>/dev/null
mv debug-data-fields.py tests/ 2>/dev/null
mv debug_df.py tests/ 2>/dev/null

# 移动日志文件
mv *.log logs/ 2>/dev/null
mv .*.pid logs/ 2>/dev/null

# 删除临时文件
rm -f test_kline_frontend.html 2>/dev/null
rm -f .DS_Store 2>/dev/null
rm -rf __pycache__ 2>/dev/null

echo "✅ 文件整理完成！"
