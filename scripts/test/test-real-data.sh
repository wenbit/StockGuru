#!/bin/bash

# 测试真实数据获取

echo "🧪 测试 StockGuru 真实数据获取..."
echo ""

cd stockguru-web/backend
source venv/bin/activate

echo "📊 测试 1: 测试 pywencai 连接"
python << 'PYTHON'
import pywencai
print("✅ pywencai 已安装")
print(f"版本: {pywencai.__version__}")
PYTHON

echo ""
echo "📊 测试 2: 测试 DataFetcher"
python << 'PYTHON'
from app.services.modules.data_fetcher import DataFetcher
from datetime import datetime, timedelta

fetcher = DataFetcher()

# 使用最近的交易日
date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f"测试日期: {date}")

try:
    print("\n获取成交额数据...")
    volume_df = fetcher.get_volume_top_stocks(date, top_n=10)
    print(f"✅ 成功获取 {len(volume_df)} 只股票")
    if not volume_df.empty:
        print(f"示例数据:")
        print(volume_df.head(3))
except Exception as e:
    print(f"❌ 失败: {e}")

try:
    print("\n获取热度数据...")
    hot_df = fetcher.get_hot_top_stocks(date, top_n=10)
    print(f"✅ 成功获取 {len(hot_df)} 只股票")
    if not hot_df.empty:
        print(f"示例数据:")
        print(hot_df.head(3))
except Exception as e:
    print(f"❌ 失败: {e}")

PYTHON

echo ""
echo "📊 测试 3: 测试完整筛选流程"
echo "请访问 http://localhost:3000 并点击'一键筛选'按钮"
echo "或者运行以下命令测试 API:"
echo ""
echo "curl -X POST http://localhost:8000/api/v1/screening \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"date\":\"2025-10-14\"}'"
echo ""
