#!/usr/bin/env python3
"""
调试脚本：查看 pywencai 返回的实际字段名
"""
import sys
import os
from pathlib import Path

# 设置环境变量
env_file = Path('stockguru-web/backend/.env')
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

sys.path.insert(0, 'stockguru-web/backend')

from app.services.modules.data_fetcher import DataFetcher
from app.services.modules.stock_filter import StockFilter
from app.core.config import settings

print("=" * 60)
print("调试：查看实际数据字段")
print("=" * 60)

# 初始化
fetcher = DataFetcher()
stock_filter = StockFilter(config=settings)

# 获取数据
date = "2025-10-14"
print(f"\n1. 获取成交额数据 (Top 5)...")
volume_df = fetcher.get_volume_top_stocks(date, top_n=5)
print(f"   获取到 {len(volume_df)} 条数据")
print(f"   字段名: {list(volume_df.columns)}")
if not volume_df.empty:
    print(f"\n   第一条数据:")
    for col in volume_df.columns:
        print(f"   - {col}: {volume_df.iloc[0][col]}")

print(f"\n2. 获取热度数据 (Top 5)...")
hot_df = fetcher.get_hot_top_stocks(date, top_n=5)
print(f"   获取到 {len(hot_df)} 条数据")
print(f"   字段名: {list(hot_df.columns)}")

print(f"\n3. 计算综合评分...")
filtered_df = stock_filter.calculate_comprehensive_score(volume_df, hot_df)
print(f"   筛选出 {len(filtered_df)} 条数据")
print(f"   字段名: {list(filtered_df.columns)}")

if not filtered_df.empty:
    print(f"\n   第一条筛选结果:")
    first_row = filtered_df.iloc[0]
    for col in filtered_df.columns:
        print(f"   - {col}: {first_row[col]}")
    
    print(f"\n4. 转换为字典:")
    stock_dict = filtered_df.iloc[0].to_dict()
    print(f"   字典键: {list(stock_dict.keys())}")
    
    # 测试字段映射
    print(f"\n5. 测试字段映射:")
    close_price = (
        stock_dict.get("最新价", None) or 
        stock_dict.get("close", None) or 
        stock_dict.get("收盘价", None)
    )
    change_pct = (
        stock_dict.get("最新涨跌幅", None) or 
        stock_dict.get("change_pct", None) or 
        stock_dict.get("涨跌幅", None)
    )
    print(f"   收盘价: {close_price}")
    print(f"   涨跌幅: {change_pct}")

print("\n" + "=" * 60)
