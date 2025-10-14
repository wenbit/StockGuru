#!/usr/bin/env python3
"""
测试真实动量计算
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_file = Path('stockguru-web/backend/.env')
if env_file.exists():
    load_dotenv(env_file)

sys.path.insert(0, 'stockguru-web/backend')

from app.services.modules.data_fetcher import DataFetcher
from app.services.modules.momentum_calculator import MomentumCalculator
from app.core.config import settings
import pandas as pd

print("=" * 60)
print("测试真实动量计算")
print("=" * 60)

# 初始化
fetcher = DataFetcher()
momentum_calc = MomentumCalculator(config=settings)

# 测试股票
test_code = "600111"  # 北方稀土
print(f"\n测试股票: {test_code}")

# 1. 获取K线数据
print(f"\n1. 获取25天K线数据...")
kline_df = fetcher.get_stock_daily_data(test_code, days=25)
print(f"   获取到 {len(kline_df)} 天数据")
if not kline_df.empty:
    print(f"   日期范围: {kline_df['date'].iloc[0]} ~ {kline_df['date'].iloc[-1]}")
    print(f"   收盘价范围: {kline_df['close'].min():.2f} ~ {kline_df['close'].max():.2f}")

# 2. 计算动量
print(f"\n2. 计算动量分数...")
if not kline_df.empty:
    momentum_score = momentum_calc.calculate_momentum(kline_df['close'])
    print(f"   动量分数: {momentum_score:.2f}")
    
    # 3. 批量计算测试
    print(f"\n3. 测试批量计算...")
    test_stocks = pd.DataFrame([
        {'code': test_code, 'name': '北方稀土', 'comprehensive_score': 1.0}
    ])
    stock_data_dict = {test_code: kline_df}
    
    result_df = momentum_calc.batch_calculate(test_stocks, stock_data_dict)
    print(f"   结果:")
    print(result_df[['code', 'name', 'comprehensive_score', 'momentum_score']])
else:
    print("   ❌ 未获取到K线数据")

print("\n" + "=" * 60)
