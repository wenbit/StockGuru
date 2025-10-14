#!/usr/bin/env python3
"""测试 K线 API"""
import sys
import os

# 设置路径
backend_path = '/Users/van/dev/source/claudecode_src/StockGuru/stockguru-web/backend'
os.chdir(backend_path)
sys.path.insert(0, backend_path)

# 设置环境变量
os.environ['SUPABASE_URL'] = 'https://mislyhozlviaedinpnfa.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1pc2x5aG96bHZpYWVkaW5wbmZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MzAwNzEsImV4cCI6MjA3NjAwNjA3MX0.okEn31fdzMRV_k0SExYS-5TPdp7DngntKuvnPamV1Us'

try:
    import pandas as pd
    from app.services.modules.data_fetcher import DataFetcher
    from app.services.modules.momentum_calculator import MomentumCalculator
    from app.core.config import settings
    
    print("✓ 配置加载成功")
    
    # 测试数据获取
    fetcher = DataFetcher()
    kline_df = fetcher.get_stock_daily_data('000001', days=60)
    print(f"✓ 数据获取成功: {kline_df.shape}")
    print(f"  列名: {kline_df.columns.tolist()}")
    
    # 测试均线计算
    momentum_calc = MomentumCalculator(config=settings)
    ma5 = momentum_calc.calculate_ma(kline_df['close'], period=5)
    ma10 = momentum_calc.calculate_ma(kline_df['close'], period=10)
    ma20 = momentum_calc.calculate_ma(kline_df['close'], period=20)
    
    print(f"✓ 均线计算成功: MA5={len(ma5)}, MA10={len(ma10)}, MA20={len(ma20)}")
    
    # 测试转换为字典
    kline_data = kline_df.to_dict('records')
    print(f"✓ 转换为字典成功: {len(kline_data)} 条记录")
    
    # 测试添加均线
    for i, record in enumerate(kline_data):
        record['ma5'] = float(ma5.iloc[i]) if i < len(ma5) and not pd.isna(ma5.iloc[i]) else None
        record['ma10'] = float(ma10.iloc[i]) if i < len(ma10) and not pd.isna(ma10.iloc[i]) else None
        record['ma20'] = float(ma20.iloc[i]) if i < len(ma20) and not pd.isna(ma20.iloc[i]) else None
    
    print(f"✓ 添加均线成功")
    print(f"  第一条记录: date={kline_data[0].get('date')}, close={kline_data[0].get('close')}, ma5={kline_data[0].get('ma5')}")
    print(f"  最后一条记录: date={kline_data[-1].get('date')}, close={kline_data[-1].get('close')}, ma5={kline_data[-1].get('ma5')}")
    
    print("\n✅ 所有测试通过!")
    
except Exception as e:
    import traceback
    print(f"\n❌ 错误: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)
