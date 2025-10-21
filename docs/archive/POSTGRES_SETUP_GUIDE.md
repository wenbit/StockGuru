# 📦 本地 PostgreSQL 安装指南

## 🚀 快速安装（正在进行中...）

当前正在自动安装 PostgreSQL 15，预计需要 10-15 分钟。

---

## 📋 安装步骤

### 自动安装（推荐）✅ 进行中

```bash
# 运行自动安装脚本
./scripts/setup_local_postgres.sh
```

**状态**: 🔄 正在安装...

---

### 手动安装（备选方案）

如果自动安装时间过长，可以手动执行：

#### 1. 安装 PostgreSQL
```bash
brew install postgresql@15
```

#### 2. 启动服务
```bash
brew services start postgresql@15
```

#### 3. 创建数据库
```bash
createdb stockguru_test
```

#### 4. 导入表结构
```bash
psql stockguru_test < stockguru-web/database/daily_stock_data_schema.sql
```

#### 5. 配置环境变量
```bash
export DATABASE_URL='postgresql://localhost/stockguru_test'
```

#### 6. 重启后端服务
```bash
cd stockguru-web/backend
pkill -f uvicorn
uvicorn app.main:app --reload --port 8000 &
cd ../..
```

---

## 🧪 测试 COPY 命令

### 方法 1: 使用测试脚本
```bash
chmod +x scripts/test_local_postgres.sh
./scripts/test_local_postgres.sh
```

### 方法 2: 手动测试
```bash
# 1. 设置环境变量
export DATABASE_URL='postgresql://localhost/stockguru_test'

# 2. 清空测试数据
psql stockguru_test -c "TRUNCATE TABLE daily_stock_data;"

# 3. 运行同步
curl -X POST 'http://localhost:8000/api/v1/daily/sync' \
  -H 'Content-Type: application/json' \
  -d '{"sync_date": "2025-10-10"}'

# 4. 查看结果
psql stockguru_test -c "SELECT COUNT(*) FROM daily_stock_data;"

# 5. 查看 COPY 命令日志
tail -f stockguru-web/backend/backend.log | grep COPY
```

---

## 📊 预期结果

### 本地 PostgreSQL 优势
- ✅ 无网络延迟
- ✅ COPY 命令更稳定
- ✅ 性能提升 2-3倍

### 性能对比

| 环境 | 单批写入 | 单日同步 | 稳定性 |
|------|---------|---------|--------|
| **本地 PostgreSQL** | **200-300ms** | **8-10分钟** | ⭐⭐⭐⭐⭐ |
| Neon (新加坡) | 400-900ms | 12-15分钟 | ⭐⭐⭐⭐ |

---

## 🔍 验证清单

### 安装验证
- [ ] PostgreSQL 已安装
- [ ] 服务已启动
- [ ] 数据库已创建
- [ ] 表结构已导入

### 功能验证
- [ ] COPY 命令成功执行
- [ ] 数据正确入库
- [ ] 无 SSL 错误
- [ ] 性能符合预期

---

## 💡 常用命令

### 数据库管理
```bash
# 查看数据库列表
psql -l

# 连接数据库
psql stockguru_test

# 查看表结构
\d daily_stock_data

# 查看数据量
SELECT COUNT(*) FROM daily_stock_data;

# 查看最新数据
SELECT * FROM daily_stock_data ORDER BY created_at DESC LIMIT 10;
```

### 服务管理
```bash
# 启动服务
brew services start postgresql@15

# 停止服务
brew services stop postgresql@15

# 重启服务
brew services restart postgresql@15

# 查看状态
brew services list | grep postgresql
```

---

## 🎯 下一步

安装完成后：

1. ✅ 验证 PostgreSQL 运行正常
2. ✅ 配置环境变量
3. ✅ 重启后端服务
4. ✅ 运行测试
5. ✅ 对比性能

---

**当前状态**: 🔄 正在安装 PostgreSQL...  
**预计完成**: 10-15 分钟  
**进度**: 正在编译依赖包...
