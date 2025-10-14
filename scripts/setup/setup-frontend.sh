#!/bin/bash

# 前端项目设置脚本

set -e

echo "🚀 设置 StockGuru 前端项目..."
echo ""

# 1. 配置 npm 镜像
echo "📦 步骤 1/5: 配置 npm 镜像..."
npm config set registry https://registry.npmmirror.com
echo "✅ 镜像已设置为: $(npm config get registry)"
echo ""

# 2. 清理旧项目
if [ -d "frontend" ]; then
    echo "📦 步骤 2/5: 清理旧项目..."
    rm -rf frontend
    echo "✅ 旧项目已删除"
else
    echo "📦 步骤 2/5: 无需清理"
fi
echo ""

# 3. 创建 Next.js 项目
echo "📦 步骤 3/5: 创建 Next.js 项目..."
echo "   这可能需要 2-3 分钟..."
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --eslint=false \
  --src-dir=false \
  --import-alias="@/*" \
  --no-turbopack

echo "✅ Next.js 项目创建完成"
echo ""

# 4. 安装额外依赖
echo "📦 步骤 4/5: 安装额外依赖..."
cd frontend
npm install @supabase/supabase-js
echo "✅ 依赖安装完成"
echo ""

# 5. 创建环境变量文件
echo "📦 步骤 5/5: 创建环境变量文件..."
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://mislyhozlviaedinpnfa.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1pc2x5aG96bHZpYWVkaW5wbmZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MzAwNzEsImV4cCI6MjA3NjAwNjA3MX0.okEn31fdzMRV_k0SExYS-5TPdp7DngntKuvnPamV1Us
EOF
echo "✅ 环境变量文件已创建"
echo ""

echo "🎉 前端项目设置完成！"
echo ""
echo "下一步："
echo "1. cd frontend"
echo "2. npm run dev"
echo "3. 访问 http://localhost:3000"
echo ""
