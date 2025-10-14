# 🔧 StockGuru 脚本目录

本目录包含项目的各类脚本文件。

## 📁 目录结构

```
scripts/
├── README.md           # 本文件
├── setup/              # 安装配置脚本
├── start/              # 启动停止脚本
└── test/               # 测试验证脚本
```

## 🛠️ setup/ - 安装配置

项目初始化和环境配置脚本：

- `setup-cli.sh` - CLI 工具安装脚本
- `setup-frontend.sh` - 前端环境安装脚本
- `fix-npm-network.sh` - NPM 网络问题修复

**使用方法**:
```bash
cd scripts/setup
./setup-cli.sh        # 安装 CLI 工具
./setup-frontend.sh   # 安装前端依赖
```

## 🚀 start/ - 启动停止

服务启动和停止脚本：

- `start-all.sh` - 启动所有服务（前端+后端）
- `stop-all.sh` - 停止所有服务

**使用方法**:
```bash
cd scripts/start
./start-all.sh    # 启动服务
./stop-all.sh     # 停止服务
```

## 🧪 test/ - 测试验证

功能测试和验证脚本：

- `check-frontend-status.sh` - 检查前端状态
- `diagnose.sh` - 系统诊断
- `test-real-data.sh` - 真实数据测试
- `test-system.sh` - 系统测试
- `验证v0.9功能.sh` - v0.9 功能验证
- `验证新功能.sh` - 新功能验证
- `test_e2e_kline.sh` - K线图端到端测试

**使用方法**:
```bash
cd scripts/test
./diagnose.sh              # 运行系统诊断
./test-system.sh           # 运行系统测试
./验证v0.9功能.sh          # 验证 v0.9 功能
```

## 📝 脚本规范

### 文件命名
- 使用小写字母和连字符
- 描述性的文件名
- `.sh` 扩展名

### 脚本结构
```bash
#!/bin/bash

# 脚本说明
# 功能描述

# 设置错误处理
set -e

# 主要逻辑
...

# 完成提示
echo "✅ 完成！"
```

### 执行权限
```bash
chmod +x script-name.sh
```

---

*最后更新: 2025-10-15*
