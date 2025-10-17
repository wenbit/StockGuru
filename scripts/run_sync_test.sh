#!/bin/bash
# 运行同步测试脚本（自动加载 .env 配置）

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/stockguru-web/backend/.env"

# 检查 .env 文件
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 错误: 找不到 .env 文件: $ENV_FILE"
    exit 1
fi

echo "📁 加载环境变量: $ENV_FILE"

# 加载 .env 文件
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# 检查必要的环境变量
if [ -z "$DATABASE_URL" ] && [ -z "$NEON_DATABASE_URL" ]; then
    echo "❌ 错误: 未找到 DATABASE_URL 或 NEON_DATABASE_URL"
    exit 1
fi

echo "✅ 环境变量已加载"
echo ""

# 运行测试
cd "$PROJECT_ROOT"

# 获取昨天的日期（默认值）
YESTERDAY=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d 2>/dev/null || echo "2025-10-16")

# 解析参数
if [ "$1" = "--all" ] || [ "$1" = "all" ]; then
    # 全量测试
    DATE=${2:-$YESTERDAY}
    echo "🚀 开始全量同步测试"
    echo "   股票数量: 全部A股"
    echo "   测试日期: $DATE"
    echo ""
    python scripts/test_copy_sync.py --all --date "$DATE"
else
    # 指定数量测试
    STOCKS=${1:-15}
    DATE=${2:-$YESTERDAY}
    echo "🚀 开始同步测试"
    echo "   股票数量: $STOCKS"
    echo "   测试日期: $DATE"
    echo ""
    python scripts/test_copy_sync.py --stocks "$STOCKS" --date "$DATE"
fi
