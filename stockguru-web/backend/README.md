# StockGuru 后端

## ⚠️ 重要：必须使用虚拟环境

**不要直接运行 `pip install`！** 必须先激活虚拟环境。

## 🚀 快速启动

### 方法1：使用启动脚本（推荐）

```bash
./start.sh
```

这个脚本会自动：
- 激活虚拟环境
- 检查依赖
- 启动服务

### 方法2：手动启动

```bash
# 1. 激活虚拟环境（重要！）
source venv/bin/activate

# 2. 验证 Python 版本
python --version  # 应该显示 3.12.x

# 3. 启动服务
uvicorn app.main:app --reload
```

## 📦 安装依赖

### ⚠️ 错误方式（不要这样做）
```bash
# ❌ 错误：直接安装会安装到系统 Python 3.13
pip install -r requirements.txt
```

### ✅ 正确方式
```bash
# ✅ 正确：先激活虚拟环境
source venv/bin/activate
pip install -r requirements.txt
```

## 🔍 验证安装

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行验证脚本
./verify-installation.sh
```

## 🛠️ 常用命令

```bash
# 激活虚拟环境
source venv/bin/activate

# 查看已安装的包
pip list

# 查看 Python 路径
which python

# 退出虚拟环境
deactivate
```

## 📝 环境变量

确保 `.env` 文件已配置：

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
FRONTEND_URL=http://localhost:3000
```

## 🌐 访问 API

启动后访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## ❓ 常见问题

### Q: 为什么必须使用虚拟环境？
A: 因为系统使用 Python 3.13，但项目需要 Python 3.12。虚拟环境提供了隔离的 Python 3.12 环境。

### Q: 如何确认在虚拟环境中？
A: 命令行前面会显示 `(venv)`，或者运行 `which python` 应该显示 venv 路径。

### Q: 依赖安装失败怎么办？
A: 确保：
1. 已激活虚拟环境
2. Python 版本是 3.12.x
3. pip 已升级：`pip install --upgrade pip`

## 🔧 重新设置环境

如果环境出问题，可以重新设置：

```bash
# 删除旧环境
rm -rf venv

# 重新创建
/usr/local/bin/python3.12 -m venv venv

# 激活
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```
