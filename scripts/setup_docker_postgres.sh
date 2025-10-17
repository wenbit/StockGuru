#!/bin/bash
# 使用 Docker 快速设置 PostgreSQL 测试环境

set -e

echo "🐳 Docker PostgreSQL 快速安装"
echo "================================"
echo ""

# 检查 Docker
echo "📦 步骤 1/6: 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "请先安装 Docker: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ Docker 已安装: $(docker --version)"
echo ""

# 停止并删除旧容器
echo "🧹 步骤 2/6: 清理旧容器..."
docker stop postgres-test 2>/dev/null || true
docker rm postgres-test 2>/dev/null || true
echo "✅ 清理完成"
echo ""

# 启动 PostgreSQL 容器
echo "🚀 步骤 3/6: 启动 PostgreSQL 容器..."
docker run -d \
  --name postgres-test \
  -e POSTGRES_PASSWORD=test123 \
  -e POSTGRES_DB=stockguru_test \
  -p 5432:5432 \
  postgres:15

echo "✅ 容器已启动"
echo ""

# 等待 PostgreSQL 启动
echo "⏳ 步骤 4/6: 等待 PostgreSQL 启动..."
sleep 5

# 验证连接
for i in {1..10}; do
    if docker exec postgres-test pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ PostgreSQL 已就绪"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ PostgreSQL 启动超时"
        exit 1
    fi
    echo "等待中... ($i/10)"
    sleep 2
done
echo ""

# 导入表结构
echo "📝 步骤 5/6: 导入表结构..."
docker exec -i postgres-test psql -U postgres stockguru_test < stockguru-web/database/daily_stock_data_schema.sql
echo "✅ 表结构导入成功"
echo ""

# 验证表
echo "🔍 步骤 6/6: 验证表结构..."
docker exec postgres-test psql -U postgres stockguru_test -c "\dt" | grep daily_stock_data
echo "✅ 表结构验证成功"
echo ""

echo "================================"
echo "✅ Docker PostgreSQL 环境已就绪！"
echo ""
echo "📊 容器信息:"
echo "  容器名: postgres-test"
echo "  数据库: stockguru_test"
echo "  用户名: postgres"
echo "  密码: test123"
echo "  端口: 5432"
echo ""
echo "🔧 环境变量配置:"
echo "  export DATABASE_URL='postgresql://postgres:test123@localhost:5432/stockguru_test'"
echo ""
echo "🔄 重启后端服务:"
echo "  cd stockguru-web/backend"
echo "  pkill -f uvicorn"
echo "  uvicorn app.main:app --reload --port 8000 &"
echo "  cd ../.."
echo ""
echo "🧪 运行测试:"
echo "  curl -X POST 'http://localhost:8000/api/v1/daily/sync' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"sync_date\": \"2025-10-10\"}'"
echo ""
echo "💡 查看数据:"
echo "  docker exec postgres-test psql -U postgres stockguru_test -c 'SELECT COUNT(*) FROM daily_stock_data;'"
echo ""
echo "🗑️  清理容器:"
echo "  docker stop postgres-test && docker rm postgres-test"
echo ""
echo "🎉 安装完成！总耗时: 约2分钟"
