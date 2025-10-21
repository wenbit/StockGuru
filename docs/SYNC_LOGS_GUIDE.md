# 数据同步日志查看指南

## 📋 概述

`view_sync_logs.sh` 是一个方便的日志查看工具，用于实时监控和查看数据同步进度。

## 🚀 快速开始

### 基本使用

```bash
# 进入项目目录
cd /Users/van/dev/source/claudecode_src/StockGuru

# 实时查看同步进度（默认）
./scripts/view_sync_logs.sh

# 或者使用完整路径
bash scripts/view_sync_logs.sh
```

## 📖 使用方法

### 1. 实时跟踪进度（推荐）

```bash
./scripts/view_sync_logs.sh
# 或
./scripts/view_sync_logs.sh -f
# 或
./scripts/view_sync_logs.sh --follow
```

**显示内容**：
- 最近 5 条进度记录
- 实时更新的进度信息
- 自动刷新，按 Ctrl+C 停止

**示例输出**：
```
📋 实时跟踪同步进度
按 Ctrl+C 停止

最近进度：
2025-10-21 15:31:50 [INFO] test_copy_sync: 进度: 1240/5378 (23%), 成功: 1240, 失败: 0...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
实时日志：

2025-10-21 15:32:00 [INFO] test_copy_sync: 进度: 1250/5378 (23%), 成功: 1250...
```

### 2. 查看当前状态

```bash
./scripts/view_sync_logs.sh -s
# 或
./scripts/view_sync_logs.sh --status
```

**显示内容**：
- 最新的同步进度
- 成功/失败统计
- 同步速度
- 预计剩余时间

**示例输出**：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
当前同步状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

最新进度：
2025-10-21 15:31:50 [INFO] test_copy_sync: 进度: 1240/5378 (23%)...

  📊 进度: 1240/5378 (23%)
  ✅ 成功: 1240
  ❌ 失败: 0
  🚀 速度: 1.8 股/秒
  ⏳ 预计剩余: 39 分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. 查看最近的日志

```bash
# 查看最近 50 行（默认）
./scripts/view_sync_logs.sh -l

# 查看最近 100 行
./scripts/view_sync_logs.sh -l 100

# 查看最近 200 行
./scripts/view_sync_logs.sh --last 200
```

**适用场景**：
- 快速查看历史进度
- 检查是否有错误
- 分析同步性能

### 4. 实时跟踪所有日志

```bash
./scripts/view_sync_logs.sh -a
# 或
./scripts/view_sync_logs.sh --all
```

**显示内容**：
- 所有同步相关日志（不仅是进度）
- 包括入库信息、重连信息等
- 实时更新

**适用场景**：
- 详细监控同步过程
- 调试问题
- 查看完整的同步流程

### 5. 查看帮助

```bash
./scripts/view_sync_logs.sh -h
# 或
./scripts/view_sync_logs.sh --help
```

## 📊 选项说明

| 选项 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--follow` | `-f` | 实时跟踪进度日志（默认） | `./scripts/view_sync_logs.sh -f` |
| `--status` | `-s` | 显示当前同步状态 | `./scripts/view_sync_logs.sh -s` |
| `--last N` | `-l N` | 查看最近 N 行日志 | `./scripts/view_sync_logs.sh -l 100` |
| `--all` | `-a` | 实时跟踪所有同步日志 | `./scripts/view_sync_logs.sh -a` |
| `--progress` | `-p` | 只显示进度信息（同 -f） | `./scripts/view_sync_logs.sh -p` |
| `--help` | `-h` | 显示帮助信息 | `./scripts/view_sync_logs.sh -h` |

## 🎯 使用场景

### 场景 1：监控正在运行的同步任务

```bash
# 打开终端，实时查看进度
./scripts/view_sync_logs.sh

# 看到进度正常更新，按 Ctrl+C 退出
```

### 场景 2：快速检查同步状态

```bash
# 查看当前状态
./scripts/view_sync_logs.sh -s

# 如果显示正在同步，可以继续实时跟踪
./scripts/view_sync_logs.sh -f
```

### 场景 3：查看历史同步记录

```bash
# 查看最近 200 行日志
./scripts/view_sync_logs.sh -l 200

# 分析同步性能和问题
```

### 场景 4：调试同步问题

```bash
# 查看所有详细日志
./scripts/view_sync_logs.sh -a

# 查找错误信息和异常
```

## 🔧 高级用法

### 结合其他命令

```bash
# 只查看失败的记录
./scripts/view_sync_logs.sh -l 500 | grep "失败: [1-9]"

# 统计同步速度
./scripts/view_sync_logs.sh -l 100 | grep "速度" | tail -10

# 导出日志到文件
./scripts/view_sync_logs.sh -l 1000 > sync_history.log
```

### 在后台运行

```bash
# 将日志输出到文件
nohup ./scripts/view_sync_logs.sh -f > sync_monitor.log 2>&1 &

# 查看输出
tail -f sync_monitor.log
```

## 📝 日志格式说明

### 进度日志格式

```
2025-10-21 15:31:50,360 [INFO] test_copy_sync: 进度: 1240/5378 (23%), 成功: 1240, 失败: 0, 已入库: 1000, 速度: 1.8股/秒, 预计剩余: 2364秒
```

**字段解释**：
- `2025-10-21 15:31:50,360`: 时间戳
- `[INFO]`: 日志级别
- `test_copy_sync`: 日志来源
- `进度: 1240/5378 (23%)`: 当前进度和百分比
- `成功: 1240`: 成功获取数据的股票数
- `失败: 0`: 失败的股票数
- `已入库: 1000`: 实际插入数据库的记录数
- `速度: 1.8股/秒`: 当前同步速度
- `预计剩余: 2364秒`: 预计还需要的时间

### 其他重要日志

```bash
# 批量入库
✅ 已入库 500 只股票，500 条新记录，累计: 1000

# 数据库重连
⚠️  连接已持续 572 秒，主动重连以避免超时...

# 同步完成
数据获取完成: 耗时 45.2 分钟
```

## ⚠️ 注意事项

1. **日志文件位置**：脚本默认读取 `logs/backend.log`
2. **权限问题**：确保脚本有执行权限（`chmod +x`）
3. **后端服务**：确保后端服务正在运行，否则日志文件可能不存在
4. **实时跟踪**：使用 Ctrl+C 停止实时跟踪
5. **大文件**：如果日志文件很大，查看历史记录可能较慢

## 🛠️ 故障排除

### 问题 1：日志文件不存在

```bash
错误：日志文件不存在 (logs/backend.log)
```

**解决方法**：
1. 检查后端服务是否运行：`ps aux | grep uvicorn`
2. 启动后端服务：`cd stockguru-web/backend && uvicorn app.main:app --reload`
3. 确认日志目录存在：`mkdir -p logs`

### 问题 2：没有同步进度信息

```bash
没有找到同步进度信息
```

**解决方法**：
1. 同步任务可能尚未开始
2. 同步任务可能已完成
3. 使用 `-a` 选项查看所有日志

### 问题 3：权限被拒绝

```bash
Permission denied: ./scripts/view_sync_logs.sh
```

**解决方法**：
```bash
chmod +x scripts/view_sync_logs.sh
```

## 📚 相关工具

- **watch_sync_detailed.py**: Python 版详细监控工具
- **watch_sync_progress.sh**: 简化版进度监控
- **monitor_sync_progress.py**: 数据库实时监控

## 💡 最佳实践

1. **日常监控**：使用 `-s` 快速查看状态
2. **同步中**：使用 `-f` 实时跟踪进度
3. **问题排查**：使用 `-a` 查看详细日志
4. **性能分析**：使用 `-l 500` 查看历史记录

## 🔗 相关文档

- [数据同步指南](../SYNC_GUIDE.md)
- [同步进度显示优化](../SYNC_PROGRESS_DISPLAY.md)
- [问题修复报告](../SYNC_ISSUE_ANALYSIS.md)

---

**创建时间**: 2025-10-21  
**最后更新**: 2025-10-21  
**维护者**: StockGuru Team
