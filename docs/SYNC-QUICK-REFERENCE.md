# 数据同步快速参考

## 🚀 快速开始

```bash
# 同步单个日期
python3 scripts/batch_sync_dates.py --dates 2025-10-14

# 同步日期范围
python3 scripts/batch_sync_dates.py --start 2025-10-10 --end 2025-10-16

# 同步多个日期
python3 scripts/batch_sync_dates.py --dates 2025-10-14 2025-10-16 2025-10-17
```

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 断点续传 | 自动跳过已同步股票，节省时间 |
| 🔌 定期重连 | 每5分钟主动重连，避免超时 |
| 🔁 智能重试 | 每个日期最多重试3次 |
| 👁️ 实时监控 | 检测持续错误并及时中断 |
| 📊 自动更新 | 同步完成后自动更新状态表 |
| ⏭️ 失败继续 | 某个日期失败后继续下一个 |

## 📋 执行流程

```
检查交易日 → 检查已同步 → 尝试同步(3次) → 更新状态表 → 下一个日期
```

## ⚙️ 关键参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最大重试次数 | 3 | 每个日期的重试次数 |
| 错误阈值 | 10 | 30秒内错误次数上限 |
| 重连间隔 | 300秒 | 定期重连的时间间隔 |
| 重试等待 | 5秒 | 失败后等待时间 |

## 📊 状态表字段

```sql
daily_sync_status
├── sync_date          -- 同步日期
├── status             -- success / failed
├── total_records      -- 总记录数
├── success_count      -- 成功数量
├── start_time         -- 开始时间
├── end_time           -- 结束时间
├── duration_seconds   -- 耗时（秒）
└── error_message      -- 错误信息
```

## 🔍 查询命令

```sql
-- 查看同步状态
SELECT sync_date, status, success_count, duration_seconds
FROM daily_sync_status
WHERE sync_date BETWEEN '2025-10-10' AND '2025-10-16'
ORDER BY sync_date;

-- 查看失败记录
SELECT sync_date, error_message
FROM daily_sync_status
WHERE status = 'failed';

-- 查看某日数据量
SELECT COUNT(*) 
FROM daily_stock_data 
WHERE trade_date = '2025-10-14';
```

## 🛠️ 故障处理

### 问题1: 连接超时
✅ **已自动处理** - 每5分钟主动重连

### 问题2: 持续错误
✅ **已自动处理** - 30秒内10次错误自动终止并重试

### 问题3: 数据不完整
```bash
# 1. 删除该日期数据
DELETE FROM daily_stock_data WHERE trade_date = '2025-10-14';
DELETE FROM daily_sync_status WHERE sync_date = '2025-10-14';

# 2. 重新同步
python3 scripts/batch_sync_dates.py --dates 2025-10-14
```

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 平均速度 | 5.5 股/秒 |
| 单日耗时 | 8-15 分钟 |
| 断点续传节省 | 最高 87% |
| 成功率 | 95%+ |

## 📁 相关文件

```
scripts/
├── batch_sync_dates.py      # 批量同步脚本
├── test_copy_sync.py         # 单日同步脚本
└── test_batch_sync.sh        # 测试脚本

docs/
├── 批量同步使用说明.md      # 详细文档
└── 数据同步优化总结.md      # 优化总结
```

## 💡 最佳实践

1. **日常同步**: 每天同步前一天数据
2. **批量补充**: 使用日期范围同步多天
3. **失败重试**: 删除数据后重新同步
4. **定期检查**: 查询状态表确认完整性

## 🎯 快速诊断

```bash
# 检查本周同步状态
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('stockguru-web/backend/.env'))
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()
cursor.execute('''
    SELECT sync_date, status, success_count
    FROM daily_sync_status
    WHERE sync_date >= CURRENT_DATE - INTERVAL '7 days'
    ORDER BY sync_date
''')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]:8s} - {row[2]:,} 条')
cursor.close()
conn.close()
"
```

---

**提示**: 详细文档请查看 `docs/批量同步使用说明.md`
