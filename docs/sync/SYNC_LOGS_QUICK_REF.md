# 数据同步日志查看 - 快速参考

## 🚀 一键命令

```bash
# 进入项目目录
cd /Users/van/dev/source/claudecode_src/StockGuru

# 查看当前状态（最常用）
./scripts/view_sync_logs.sh -s

# 实时跟踪进度
./scripts/view_sync_logs.sh

# 查看最近 100 行
./scripts/view_sync_logs.sh -l 100

# 查看所有详细日志
./scripts/view_sync_logs.sh -a
```

## 📋 常用命令速查

| 命令 | 说明 | 使用场景 |
|------|------|----------|
| `./scripts/view_sync_logs.sh -s` | 查看当前状态 | 快速检查进度 |
| `./scripts/view_sync_logs.sh` | 实时跟踪进度 | 监控同步过程 |
| `./scripts/view_sync_logs.sh -l 100` | 查看最近100行 | 查看历史记录 |
| `./scripts/view_sync_logs.sh -a` | 查看所有日志 | 详细调试 |
| `./scripts/view_sync_logs.sh -h` | 查看帮助 | 了解所有选项 |

## 📊 状态输出示例

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
当前同步状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

最新进度：
2025-10-21 15:38:27 [INFO] test_copy_sync: 进度: 1910/5378 (35%)...

  📊 进度: 1910/5378 (35%)
  ✅ 成功: 1910
  ❌ 失败: 0
  🚀 速度: 1.7 股/秒
  ⏳ 预计剩余: 33 分钟
```

## 🎯 使用技巧

### 1. 快速检查
```bash
# 每隔几分钟检查一次状态
watch -n 60 './scripts/view_sync_logs.sh -s'
```

### 2. 后台监控
```bash
# 在后台持续监控并保存到文件
nohup ./scripts/view_sync_logs.sh -f > sync_monitor.log 2>&1 &

# 查看监控日志
tail -f sync_monitor.log
```

### 3. 查找错误
```bash
# 查找失败记录
./scripts/view_sync_logs.sh -l 500 | grep "失败: [1-9]"
```

## ⚡ 快捷别名（可选）

添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
# StockGuru 日志查看别名
alias sync-status='cd /Users/van/dev/source/claudecode_src/StockGuru && ./scripts/view_sync_logs.sh -s'
alias sync-watch='cd /Users/van/dev/source/claudecode_src/StockGuru && ./scripts/view_sync_logs.sh'
alias sync-logs='cd /Users/van/dev/source/claudecode_src/StockGuru && ./scripts/view_sync_logs.sh -l 100'
```

使用：
```bash
sync-status  # 查看状态
sync-watch   # 实时监控
sync-logs    # 查看历史
```

## 📁 文件位置

- **脚本**: `scripts/view_sync_logs.sh`
- **日志**: `logs/backend.log`
- **文档**: `docs/SYNC_LOGS_GUIDE.md`

## 🆘 快速故障排除

| 问题 | 解决方法 |
|------|----------|
| 日志文件不存在 | 启动后端服务 |
| 权限被拒绝 | `chmod +x scripts/view_sync_logs.sh` |
| 没有进度信息 | 同步任务未开始或已完成 |

## 📚 完整文档

详细使用说明请查看：`docs/SYNC_LOGS_GUIDE.md`

---

**提示**: 按 Ctrl+C 可以停止实时跟踪
