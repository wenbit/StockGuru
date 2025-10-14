# Git 使用说明

**项目**: StockGuru  
**版本**: v0.9  
**初始化时间**: 2025-10-15 02:29

---

## 📋 Git 仓库信息

### 当前状态
- ✅ Git 仓库已初始化
- ✅ 所有文件已提交
- ✅ 提交数量: 1
- ✅ 文件数量: 138
- ✅ 代码行数: 22,589+

### 初始提交
```
commit: 44c67f7
message: feat: StockGuru v0.9 - 完整可视化版本
date: 2025-10-15
files: 138 files changed, 22589 insertions(+)
```

---

## 🚀 常用 Git 命令

### 查看状态
```bash
# 查看当前状态
git status

# 查看提交历史
git log

# 查看简洁历史
git log --oneline

# 查看文件变更
git diff
```

### 提交更改
```bash
# 添加所有更改
git add .

# 添加特定文件
git add <file>

# 提交更改
git commit -m "描述信息"

# 查看提交详情
git show
```

### 分支管理
```bash
# 查看分支
git branch

# 创建分支
git branch <branch-name>

# 切换分支
git checkout <branch-name>

# 创建并切换分支
git checkout -b <branch-name>

# 合并分支
git merge <branch-name>
```

### 远程仓库
```bash
# 添加远程仓库
git remote add origin <url>

# 查看远程仓库
git remote -v

# 推送到远程
git push -u origin main

# 拉取更新
git pull origin main
```

---

## 📝 提交规范

### Commit Message 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例
```bash
# 新功能
git commit -m "feat: 添加 HTML 报告导出功能"

# 修复 bug
git commit -m "fix: 修复 K线图数据获取失败问题"

# 文档更新
git commit -m "docs: 更新 README 文档"

# 代码重构
git commit -m "refactor: 优化数据获取模块"
```

---

## 🔄 工作流程

### 日常开发流程
```bash
# 1. 查看当前状态
git status

# 2. 拉取最新代码
git pull origin main

# 3. 创建功能分支
git checkout -b feature/new-feature

# 4. 进行开发...

# 5. 添加更改
git add .

# 6. 提交更改
git commit -m "feat: 添加新功能"

# 7. 切换回主分支
git checkout main

# 8. 合并功能分支
git merge feature/new-feature

# 9. 推送到远程
git push origin main
```

### 版本发布流程
```bash
# 1. 创建版本标签
git tag -a v0.9 -m "版本 v0.9 发布"

# 2. 查看标签
git tag

# 3. 推送标签
git push origin v0.9

# 4. 查看标签详情
git show v0.9
```

---

## 🛠️ 实用技巧

### 撤销操作
```bash
# 撤销工作区更改
git checkout -- <file>

# 撤销暂存区更改
git reset HEAD <file>

# 撤销最后一次提交（保留更改）
git reset --soft HEAD^

# 撤销最后一次提交（丢弃更改）
git reset --hard HEAD^
```

### 查看历史
```bash
# 查看文件历史
git log -- <file>

# 查看某次提交的更改
git show <commit-id>

# 查看两次提交的差异
git diff <commit1> <commit2>
```

### 暂存工作
```bash
# 暂存当前工作
git stash

# 查看暂存列表
git stash list

# 恢复暂存
git stash pop

# 删除暂存
git stash drop
```

---

## 📦 .gitignore 配置

当前已忽略的文件/目录:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Node
node_modules/
.next/
out/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 系统
.DS_Store
Thumbs.db

# 日志
*.log
logs/

# 数据
data/cache/*
!data/cache/.gitkeep

# 输出
output/*
!output/.gitkeep

# 环境变量
.env
.env.local

# PID 文件
*.pid
```

---

## 🔗 连接远程仓库

### GitHub
```bash
# 1. 在 GitHub 创建仓库

# 2. 添加远程仓库
git remote add origin https://github.com/username/StockGuru.git

# 3. 推送代码
git push -u origin main

# 4. 后续推送
git push
```

### GitLab
```bash
# 添加 GitLab 远程仓库
git remote add origin https://gitlab.com/username/StockGuru.git
git push -u origin main
```

### Gitee (码云)
```bash
# 添加 Gitee 远程仓库
git remote add origin https://gitee.com/username/StockGuru.git
git push -u origin main
```

---

## 📊 项目统计

### 代码统计
```bash
# 查看代码行数
git ls-files | xargs wc -l

# 查看文件数量
git ls-files | wc -l

# 查看提交统计
git shortlog -sn

# 查看代码贡献
git log --author="<name>" --oneline | wc -l
```

### 当前统计
- **总文件数**: 138
- **总代码行**: 22,589+
- **提交数**: 1
- **分支数**: 1 (main)

---

## 🎯 最佳实践

### 1. 频繁提交
- 每完成一个小功能就提交
- 提交信息要清晰明确
- 避免一次提交过多更改

### 2. 使用分支
- 主分支保持稳定
- 新功能在独立分支开发
- 测试通过后再合并

### 3. 代码审查
- 重要更改前先 review
- 使用 Pull Request
- 团队协作时必须

### 4. 定期备份
- 定期推送到远程仓库
- 重要节点打标签
- 保持远程同步

---

## 📝 快速参考

### 初始化
```bash
git init                    # 初始化仓库
git add .                   # 添加所有文件
git commit -m "message"     # 提交
```

### 日常使用
```bash
git status                  # 查看状态
git add <file>              # 添加文件
git commit -m "message"     # 提交
git push                    # 推送
git pull                    # 拉取
```

### 分支操作
```bash
git branch                  # 查看分支
git checkout -b <branch>    # 创建并切换
git merge <branch>          # 合并分支
git branch -d <branch>      # 删除分支
```

---

## 🔍 故障排除

### 问题 1: 推送失败
```bash
# 先拉取远程更改
git pull origin main

# 解决冲突后再推送
git push origin main
```

### 问题 2: 合并冲突
```bash
# 1. 查看冲突文件
git status

# 2. 手动解决冲突

# 3. 标记为已解决
git add <file>

# 4. 完成合并
git commit
```

### 问题 3: 误提交
```bash
# 撤销最后一次提交
git reset --soft HEAD^

# 修改后重新提交
git commit -m "new message"
```

---

## 📞 相关资源

- **Git 官方文档**: https://git-scm.com/doc
- **GitHub 指南**: https://guides.github.com
- **Pro Git 书籍**: https://git-scm.com/book/zh/v2

---

**文档更新**: 2025-10-15  
**Git 版本**: 已初始化  
**项目版本**: v0.9
