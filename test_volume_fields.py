"""
测试成交量字段 - 检查数据源返回的实际字段
"""
import sys
sys.path.insert(0, 'stockguru-web/backend')

from app.services.modules.data_fetcher import DataFetcher
import pandas as pd

def test_volume_fields():
    """测试成交量字段"""
    fetcher = DataFetcher()
    
    # 测试几个日期
    test_dates = ['2025-10-11', '2025-10-12', '2025-10-13']
    
    for date in test_dates:
        print(f"\n{'='*60}")
        print(f"测试日期: {date}")
        print(f"{'='*60}")
        
        try:
            # 获取成交额数据
            print("\n1. 成交额数据:")
            volume_df = fetcher.get_volume_top_stocks(date, top_n=5)
            if not volume_df.empty:
                print(f"   字段列表: {list(volume_df.columns)}")
                print(f"   数据行数: {len(volume_df)}")
                
                # 打印第一条数据
                if len(volume_df) > 0:
                    first_row = volume_df.iloc[0]
                    print(f"\n   第一条数据:")
                    for col in volume_df.columns:
                        value = first_row[col]
                        if '成交' in str(col) or 'vol' in str(col).lower():
                            print(f"   - {col}: {value}")
            else:
                print("   未获取到数据")
            
            # 获取热度数据
            print("\n2. 热度数据:")
            hot_df = fetcher.get_hot_top_stocks(date, top_n=5)
            if not hot_df.empty:
                print(f"   字段列表: {list(hot_df.columns)}")
                print(f"   数据行数: {len(hot_df)}")
                
                # 打印第一条数据
                if len(hot_df) > 0:
                    first_row = hot_df.iloc[0]
                    print(f"\n   第一条数据:")
                    for col in hot_df.columns:
                        value = first_row[col]
                        if '成交' in str(col) or 'vol' in str(col).lower() or '热度' in str(col):
                            print(f"   - {col}: {value}")
            else:
                print("   未获取到数据")
                
        except Exception as e:
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_volume_fields()
