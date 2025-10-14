#!/bin/bash

# StockGuru GitHub 部署脚本
# 使用方法: ./deploy-to-github.sh YOUR_GITHUB_USERNAME

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  StockGuru GitHub 部署脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}请提供您的 GitHub 用户名:${NC}"
    echo "使用方法: ./deploy-to-github.sh YOUR_GITHUB_USERNAME"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="StockGuru"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo -e "${GREEN}✓${NC} GitHub 用户名: ${GITHUB_USERNAME}"
echo -e "${GREEN}✓${NC} 仓库名称: ${REPO_NAME}"
echo -e "${GREEN}✓${NC} 仓库地址: ${REPO_URL}"
echo ""

# 检查是否已有远程仓库
if git remote | grep -q "origin"; then
    echo -e "${YELLOW}⚠${NC}  检测到已存在的远程仓库"
    CURRENT_URL=$(git remote get-url origin)
    echo "   当前远程地址: ${CURRENT_URL}"
    echo ""
    read -p "是否要更新远程地址? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→${NC} 更新远程仓库地址..."
        git remote set-url origin ${REPO_URL}
        echo -e "${GREEN}✓${NC} 远程地址已更新"
    fi
else
    echo -e "${BLUE}→${NC} 添加远程仓库..."
    git remote add origin ${REPO_URL}
    echo -e "${GREEN}✓${NC} 远程仓库已添加"
fi

echo ""

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠${NC}  检测到未提交的更改"
    echo ""
    git status -s
    echo ""
    read -p "是否要提交这些更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→${NC} 添加所有更改..."
        git add -A
        
        echo -e "${BLUE}→${NC} 提交更改..."
        read -p "请输入提交信息 (默认: Update): " COMMIT_MSG
        COMMIT_MSG=${COMMIT_MSG:-"Update"}
        git commit -m "${COMMIT_MSG}"
        echo -e "${GREEN}✓${NC} 更改已提交"
    else
        echo -e "${YELLOW}⚠${NC}  跳过提交，将推送现有提交"
    fi
fi

echo ""

# 推送到 GitHub
echo -e "${BLUE}→${NC} 推送到 GitHub..."
echo ""

# 获取当前分支名
CURRENT_BRANCH=$(git branch --show-current)
echo "当前分支: ${CURRENT_BRANCH}"

# 推送
if git push -u origin ${CURRENT_BRANCH}; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✓ 部署成功！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "仓库地址: ${REPO_URL}"
    echo "访问: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "1. 访问 GitHub 仓库查看代码"
    echo "2. 配置 GitHub Pages (可选)"
    echo "3. 部署到 Vercel/Railway (推荐)"
    echo ""
    echo "详细部署指南: 查看 DEPLOYMENT.md"
else
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  ⚠ 推送失败${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "可能的原因:"
    echo "1. 仓库不存在 - 请先在 GitHub 创建仓库"
    echo "2. 没有权限 - 请检查 GitHub 认证"
    echo "3. 网络问题 - 请检查网络连接"
    echo ""
    echo "解决方法:"
    echo "1. 访问 https://github.com/new 创建仓库"
    echo "2. 运行: gh auth login (使用 GitHub CLI)"
    echo "3. 或手动配置 SSH 密钥"
    echo ""
    exit 1
fi
