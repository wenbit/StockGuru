# 📚 股票数据同步方案完整指南

## 📋 方案概述

### 方案 A: 本地数据初始化（一次性）
**用途**: 在本地电脑同步近1年历史数据  
**速度**: 约 30-60 分钟（取决于网络）  
**技术**: PostgreSQL COPY 命令（最快）

### 方案 B: 云端每日自动同步
**用途**: 部署在 Render，每日自动同步当日数据  
**速度**: 约 5-8 分钟/天  
**技术**: psycopg2 + execute_values

---

## 🚀 方案 A: 本地数据初始化

### 1. 环境准备

#### 安装依赖
```bash
pip install psycopg2-binary baostock pandas numpy
```

#### 设置环境变量
```bash
# macOS/Linux
export SUPABASE_DB_HOST="db.xxx.supabase.co"
export SUPABASE_DB_PASSWORD="your_password"
export SUPABASE_DB_PORT="6543"  # 使用 Pooler

# Windows (PowerShell)
$env:SUPABASE_DB_HOST="db.xxx.supabase.co"
$env:SUPABASE_DB_PASSWORD="your_password"
$env:SUPABASE_DB_PORT="6543"
```

#### 获取 Supabase 连接信息
1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 选择项目 → Settings → Database
3. 复制 **Connection string** (使用 **Pooler** 模式)
4. 格式: `postgresql://postgres:[password]@db.xxx.supabase.co:6543/postgres`

### 2. 运行初始化脚本

#### 同步近1年数据（默认）
```bash
cd /Users/van/dev/source/claudecode_src/StockGuru
python scripts/init_historical_data.py
```

#### 自定义同步天数
```bash
# 同步近180天
python scripts/init_historical_data.py --days 180

# 同步近30天
python scripts/init_historical_data.py --days 30
```

### 3. 监控进度

脚本会输出详细日志：
```
2025-10-17 02:30:00 [INFO] 数据库连接池已创建: db.xxx.supabase.co:6543
2025-10-17 02:30:01 [INFO] baostock 登录成功
2025-10-17 02:30:05 [INFO] 获取到 250 个交易日
2025-10-17 02:30:10 [INFO] 获取到 5158 只A股
2025-10-17 02:30:15 [INFO] 同步 2024-10 月数据 (21 个交易日)
2025-10-17 02:31:00 [INFO] 进度: 1000/5158, 成功: 1000, 失败: 0
2025-10-17 02:35:00 [INFO] 成功入库 108318 条记录
```

### 4. 预期结果

- **总耗时**: 30-60 分钟（取决于网络和数据量）
- **数据量**: 约 130万条记录（5158只股票 × 250个交易日）
- **成功率**: 95%+ （部分停牌股票可能无数据）

---

## ☁️ 方案 B: 云端每日自动同步

### 1. 代码集成

#### 更新 API 路由
编辑 `stockguru-web/backend/app/api/daily_stock.py`:

```python
from app.services.daily_data_sync_service_v3 import get_sync_service_v3

@router.post("/sync-v3", response_model=SyncResponse)
async def trigger_sync_v3(request: SyncRequest):
    """使用 V3 服务同步（PostgreSQL 直连）"""
    try:
        sync_service = get_sync_service_v3()
        sync_date = request.sync_date or date.today()
        
        logger.info(f"开始同步 {sync_date} 的数据 (V3)...")
        result = await sync_service.sync_date_data(sync_date)
        
        return SyncResponse(
            status=result['status'],
            message=f"同步完成: {result.get('inserted', 0)} 条记录",
            data=result
        )
    except Exception as e:
        logger.error(f"同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### 更新定时任务
编辑 `stockguru-web/backend/app/services/scheduler.py`:

```python
from app.services.daily_data_sync_service_v3 import get_sync_service_v3

async def daily_sync_job():
    """每日数据同步任务（使用 V3）"""
    try:
        logger.info("开始每日数据同步任务...")
        sync_service = get_sync_service_v3()
        
        yesterday = date.today() - timedelta(days=1)
        result = await sync_service.sync_date_data(yesterday)
        
        logger.info(f"每日同步完成: {result}")
    except Exception as e:
        logger.error(f"每日同步失败: {e}", exc_info=True)

# 修改调度器配置
scheduler.add_job(
    daily_sync_job,
    'cron',
    hour=2,  # 凌晨2点
    minute=0,
    id='daily_sync_v3'
)
```

### 2. Render 部署配置

#### 环境变量设置
在 Render Dashboard 中设置：

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_DB_HOST=db.xxx.supabase.co
SUPABASE_DB_PASSWORD=your_db_password
SUPABASE_DB_PORT=6543
```

#### requirements.txt 添加
```txt
psycopg2-binary==2.9.9
```

#### Build Command
```bash
pip install -r requirements.txt
```

#### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3. 验证部署

#### 手动触发测试
```bash
curl -X POST "https://your-app.onrender.com/api/v1/daily/sync-v3" \
  -H "Content-Type: application/json" \
  -d '{"sync_date": "2025-10-16"}'
```

#### 查看日志
```bash
# Render Dashboard → Logs
# 查找关键词: "PostgreSQL 连接池已创建"
```

### 4. 定时任务验证

- 每日凌晨 2:00 自动触发
- 检查 Render Logs 确认执行
- 预计耗时: 5-8 分钟

---

## 📊 性能对比

| 指标 | 方案 A (本地初始化) | 方案 B (云端每日) | 原方案 (REST API) |
|------|-------------------|------------------|------------------|
| **技术** | PostgreSQL COPY | execute_values | Supabase REST API |
| **速度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **单日耗时** | 2-3 分钟 | 5-8 分钟 | 24 分钟 |
| **1年数据** | 30-60 分钟 | - | 约 100 小时 |
| **适用场景** | 数据初始化 | 每日增量 | 小批量查询 |

---

## 🧪 快速测试

### 运行同步测试
```bash
# 进入项目目录
cd /Users/van/dev/source/claudecode_src/StockGuru

# 测试 15 只股票（推荐）
./scripts/run_sync_test.sh 15 2025-10-16

# 测试 5 只股票（快速验证）
./scripts/run_sync_test.sh 5 2025-10-16
```

### 预期结果
```
✅ 环境变量已加载
✅ 数据库连接成功 (DATABASE_URL)
✅ baostock 登录成功
✅ 获取到 15 只股票
✅ 成功: 15, 失败: 0
✅ 成功入库: 10-15 条

⏱️  总耗时: 3-5 秒
🚀 速度: 250-300 股/分钟
```

---

## 🔧 故障排查

### 问题 1: 连接失败
```
ERROR: 无法获取数据库连接
```

**解决方案**:
1. 检查 `.env` 文件中的 `DATABASE_URL` 是否正确
2. 确认数据库服务是否正常运行
3. 对于 Supabase: 检查项目是否暂停（Free Tier 7天无活动会暂停）
4. 对于 Neon: 检查连接字符串格式是否正确

### 问题 2: 权限错误
```
ERROR: permission denied for table daily_stock_data
```

**解决方案**:
1. 确认使用 `postgres` 用户（非 anon 用户）
2. 检查数据库密码是否正确

### 问题 3: 数据重复
```
ERROR: duplicate key value violates unique constraint
```

**解决方案**:
- 这是正常的，脚本使用 `ON CONFLICT DO NOTHING` 自动跳过重复数据

### 问题 4: baostock 限速
```
WARNING: 获取数据失败次数过多
```

**解决方案**:
- 降低并发数（脚本已优化为串行）
- 增加重试间隔
- 分批次运行（按月同步）

---

## 📝 最佳实践

### 1. 数据初始化流程
```bash
# Step 1: 本地初始化历史数据
python scripts/init_historical_data.py --days 365

# Step 2: 部署到 Render
git push

# Step 3: 验证云端同步
curl -X POST "https://your-app.onrender.com/api/v1/daily/sync-v3"
```

### 2. 日常维护
- 每日检查 Render Logs 确认自动同步成功
- 每周检查数据完整性
- 每月备份数据库

### 3. 成本优化
- Render Free Tier: 750小时/月（足够）
- Supabase Free Tier: 500MB 数据库（约可存储 200万条记录）
- 预计成本: **$0/月**

---

## 🎯 总结

| 场景 | 推荐方案 | 预计耗时 |
|------|---------|---------|
| **首次部署** | 方案 A (本地初始化) | 30-60 分钟 |
| **日常运维** | 方案 B (云端自动) | 5-8 分钟/天 |
| **数据补全** | 方案 A (指定日期范围) | 按需 |

**最佳实践**: 
1. 使用方案 A 在本地完成历史数据初始化
2. 部署方案 B 到 Render 实现每日自动同步
3. 两套方案互补，确保数据完整性

---

## 📞 技术支持

遇到问题？
1. 查看日志文件: `init_historical_data.log`
2. 检查 Render Logs
3. 参考本文档的故障排查章节
