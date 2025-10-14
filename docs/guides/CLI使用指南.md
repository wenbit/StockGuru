# StockGuru CLI 使用指南

**版本**: v0.9  
**更新**: 2025-10-15

---

## 📦 安装

### 快速安装
```bash
# 运行安装脚本
chmod +x setup-cli.sh
./setup-cli.sh
```

### 手动安装
```bash
# 1. 安装依赖
pip3 install click requests

# 2. 设置可执行权限
chmod +x cli.py

# 3. 创建全局命令 (可选)
sudo ln -s $(pwd)/cli.py /usr/local/bin/stockguru
```

---

## 🚀 快速开始

### 查看帮助
```bash
stockguru --help
```

### 检查系统状态
```bash
stockguru status
```

输出示例:
```
🔍 检查系统状态...

✅ 后端服务: 运行中 (http://localhost:8000)
✅ 前端服务: 运行中 (http://localhost:3000)
```

---

## 📋 命令列表

### 1. screen - 运行筛选
```bash
# 基础用法
stockguru screen

# 指定日期
stockguru screen --date 2025-10-15

# 指定筛选数量
stockguru screen --top-n 20

# 自定义参数
stockguru screen \
  --date 2025-10-15 \
  --top-n 20 \
  --volume-top 150 \
  --hot-top 150 \
  --momentum-days 30
```

**参数说明**:
- `--date, -d`: 筛选日期 (默认: 今天)
- `--top-n, -n`: 筛选数量 (默认: 10)
- `--volume-top`: 成交额排名范围 (默认: 100)
- `--hot-top`: 热度排名范围 (默认: 100)
- `--momentum-days`: 动量计算天数 (默认: 25)
- `--output, -o`: 输出文件路径
- `--format, -f`: 输出格式 (table/json/csv)

---

### 2. history - 查看历史
```bash
# 查看最近 10 条记录
stockguru history

# 查看最近 20 条记录
stockguru history --limit 20

# 只看已完成的记录
stockguru history --status completed
```

**参数说明**:
- `--limit, -l`: 显示数量 (默认: 10)
- `--status, -s`: 筛选状态 (all/completed/failed/running)

---

### 3. stock - 查看股票详情
```bash
# 查看股票详情
stockguru stock 000001

# 指定 K线天数
stockguru stock 600000 --days 90
```

**参数说明**:
- `CODE`: 股票代码 (必填)
- `--days, -d`: K线天数 (默认: 60)

---

### 4. status - 检查系统状态
```bash
stockguru status
```

检查项目:
- ✅ 后端服务状态
- ✅ 前端服务状态
- ✅ 服务地址

---

### 5. config - 显示配置
```bash
stockguru config
```

显示内容:
- 成交额 Top N
- 热度 Top N
- 综合评分 Top N
- 动量计算天数
- 动量 Top N
- 前端地址

---

### 6. web - 打开 Web 界面
```bash
stockguru web
```

自动在浏览器中打开:
- 主页
- 历史记录
- API 文档

---

## 💡 使用示例

### 示例 1: 每日筛选
```bash
# 运行今天的筛选
stockguru screen

# 查看结果 (在 Web 界面)
stockguru web
```

### 示例 2: 历史分析
```bash
# 查看历史记录
stockguru history --limit 20

# 查看特定股票
stockguru stock 000001
```

### 示例 3: 自定义筛选
```bash
# 更宽松的筛选条件
stockguru screen \
  --volume-top 200 \
  --hot-top 200 \
  --top-n 30

# 更长的动量周期
stockguru screen \
  --momentum-days 40 \
  --top-n 15
```

### 示例 4: 系统管理
```bash
# 检查服务状态
stockguru status

# 查看配置
stockguru config

# 打开 Web 界面
stockguru web
```

---

## 🔧 高级用法

### 输出到文件
```bash
# JSON 格式
stockguru screen --output results.json --format json

# CSV 格式
stockguru screen --output results.csv --format csv
```

### 结合其他工具
```bash
# 使用 jq 处理 JSON
stockguru screen --format json | jq '.results[] | {code, name, score}'

# 保存到文件并查看
stockguru screen --output results.json --format json
cat results.json | jq '.'
```

---

## ⚠️ 注意事项

### 1. 服务依赖
CLI 工具依赖后端服务，使用前请确保服务已启动:
```bash
# 启动所有服务
./start-all.sh

# 或检查状态
stockguru status
```

### 2. 功能限制
当前 CLI 工具主要用于:
- ✅ 快速检查系统状态
- ✅ 打开 Web 界面
- ✅ 查看配置信息
- ⚠️ 完整筛选功能建议使用 Web 界面

### 3. 环境要求
- Python 3.8+
- Click 库
- Requests 库
- 后端服务运行中

---

## 🐛 故障排除

### 问题 1: 命令未找到
```bash
# 解决方案 1: 使用完整路径
./cli.py --help

# 解决方案 2: 重新创建链接
sudo ln -sf $(pwd)/cli.py /usr/local/bin/stockguru
```

### 问题 2: 后端服务未运行
```bash
# 启动后端
cd stockguru-web/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 问题 3: 依赖缺失
```bash
# 安装依赖
pip3 install click requests
```

---

## 📚 相关文档

- `QUICK-REFERENCE.md` - 快速参考
- `v0.9发布说明.md` - 版本说明
- `未完成需求清单.md` - 功能清单

---

## 🎯 未来计划

### v1.0 计划
- [ ] 完整的筛选功能
- [ ] 数据导出功能
- [ ] 批量操作
- [ ] 配置文件支持

### 可能的增强
- [ ] 交互式模式
- [ ] 彩色输出
- [ ] 进度条动画
- [ ] 自动补全

---

## 💬 反馈

如有问题或建议，请查看项目文档或提交 Issue。

---

**文档更新**: 2025-10-15  
**CLI 版本**: v0.9.0
