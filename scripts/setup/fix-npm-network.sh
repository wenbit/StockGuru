#!/bin/bash

# 修复 npm 网络问题

echo "🔧 修复 npm 网络问题..."
echo ""

# 1. 设置国内镜像
echo "📦 步骤 1/4: 设置 npm 镜像..."
npm config set registry https://registry.npmmirror.com
npm config set disturl https://npmmirror.com/dist
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/
npm config set phantomjs_cdnurl https://npmmirror.com/mirrors/phantomjs/
npm config set chromedriver_cdnurl https://npmmirror.com/mirrors/chromedriver/
npm config set operadriver_cdnurl https://npmmirror.com/mirrors/operadriver/
npm config set fse_binary_host_mirror https://npmmirror.com/mirrors/fsevents
echo "✅ npm 镜像配置完成"
echo ""

# 2. 清理 npm 缓存
echo "📦 步骤 2/4: 清理 npm 缓存..."
npm cache clean --force
echo "✅ 缓存已清理"
echo ""

# 3. 验证配置
echo "📦 步骤 3/4: 验证配置..."
echo "Registry: $(npm config get registry)"
echo ""

# 4. 测试连接
echo "📦 步骤 4/4: 测试连接..."
if npm ping; then
    echo "✅ npm 连接正常"
else
    echo "⚠️  npm 连接仍有问题"
    echo ""
    echo "备选方案："
    echo "1. 使用 yarn: brew install yarn"
    echo "2. 使用 pnpm: brew install pnpm"
    echo "3. 检查网络代理设置"
fi

echo ""
echo "🎉 配置完成！"
echo ""
echo "现在可以重试创建前端项目："
echo "  ./setup-frontend.sh"
echo ""
