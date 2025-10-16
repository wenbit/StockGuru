# 🚀 PostgreSQL 直连方案设置指南

## 步骤 1: 获取 Supabase 数据库密码

### 方法 1: 从 Dashboard 获取

1. 访问 [Supabase Dashboard](https://supabase.com/dashboard/project/mislyhozlviaedinpnfa/settings/database)
2. 找到 **Connection string** 部分
3. 选择 **URI** 标签
4. 复制连接字符串，格式如下：
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.mislyhozlviaedinpnfa.supabase.co:6543/postgres
   ```
5. 提取 `[YOUR-PASSWORD]` 部分

### 方法 2: 重置密码

如果忘记密码：
1. 进入 **Database Settings**
2. 找到 **Reset Database Password**
3. 输入新密码并确认
4. 保存新密码

## 步骤 2: 设置环境变量

### macOS/Linux

```bash
# 临时设置（当前终端会话有效）
export SUPABASE_DB_HOST="db.mislyhozlviaedinpnfa.supabase.co"
export SUPABASE_DB_PASSWORD="your_password_here"
export SUPABASE_DB_PORT="6543"

# 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）
echo 'export SUPABASE_DB_HOST="db.mislyhozlviaedinpnfa.supabase.co"' >> ~/.zshrc
echo 'export SUPABASE_DB_PASSWORD="your_password_here"' >> ~/.zshrc
echo 'export SUPABASE_DB_PORT="6543"' >> ~/.zshrc
source ~/.zshrc
```

### Windows (PowerShell)

```powershell
# 临时设置
$env:SUPABASE_DB_HOST="db.mislyhozlviaedinpnfa.supabase.co"
$env:SUPABASE_DB_PASSWORD="your_password_here"
$env:SUPABASE_DB_PORT="6543"

# 永久设置
[System.Environment]::SetEnvironmentVariable('SUPABASE_DB_HOST', 'db.mislyhozlviaedinpnfa.supabase.co', 'User')
[System.Environment]::SetEnvironmentVariable('SUPABASE_DB_PASSWORD', 'your_password_here', 'User')
[System.Environment]::SetEnvironmentVariable('SUPABASE_DB_PORT', '6543', 'User')
```

## 步骤 3: 测试连接

```bash
cd /Users/van/dev/source/claudecode_src/StockGuru
python scripts/test_db_connection.py
```

**预期输出**:
```
🔌 测试数据库连接...
Host: db.mislyhozlviaedinpnfa.supabase.co
Port: 6543
Database: postgres
User: postgres

✅ 连接成功！

📊 PostgreSQL 版本:
PostgreSQL 15.x on ...

✅ daily_stock_data 表存在
📈 当前记录数: 15,474 条
📅 最新数据日期: 2025-10-16

🎉 所有测试通过！可以开始使用 PostgreSQL 直连方案。
```

## 步骤 4: 性能测试

测试 50 只股票的同步性能：

```bash
python scripts/test_copy_sync.py --stocks 50 --date 2025-10-09
```

**预期输出**:
```
============================================================
📊 性能测试结果
============================================================
股票数量: 50
成功获取: 50
数据记录: 50
成功入库: 50

⏱️  耗时统计:
  数据获取: 25.3 秒
  数据入库: 0.2 秒
  总耗时:   25.5 秒

🚀 速度:
  平均: 117.6 股/分钟
  入库速度: 250 条/秒
============================================================
```

## 步骤 5: 运行完整初始化

同步近 1 年数据：

```bash
python scripts/init_historical_data.py --days 365
```

## 故障排查

### 问题 1: ModuleNotFoundError: No module named 'psycopg2'

```bash
pip install psycopg2-binary
```

### 问题 2: 连接超时

- 检查网络连接
- 确认 Supabase 项目未暂停
- 尝试使用 VPN

### 问题 3: 密码错误

```
FATAL: password authentication failed for user "postgres"
```

- 重新检查密码是否正确
- 尝试重置数据库密码

### 问题 4: SSL 错误

```
FATAL: no pg_hba.conf entry for host
```

- 确保使用 `sslmode='require'`
- 检查防火墙设置

## 安全提示

⚠️ **不要将密码提交到 Git**

```bash
# 添加到 .gitignore
echo '.env' >> .gitignore
echo '*.log' >> .gitignore
```

## 下一步

完成设置后，参考 [SYNC_GUIDE.md](../SYNC_GUIDE.md) 了解完整的同步方案。
