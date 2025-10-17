#!/usr/bin/env python3
"""
测试并发获取性能
"""

import sys
import os
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def main():
    print("\n" + "=" * 70)
    print("🚀 并发获取性能测试")
    print("=" * 70)
    
    from app.services.concurrent_data_fetcher import concurrent_fetcher
    
    # 测试50只股票
    test_stocks = ['000001', '000002', '600000', '600519', '000858'] * 10
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试配置:")
    print(f"   股票数量: {len(test_stocks)}")
    print(f"   并发数: 10")
    print(f"   测试日期: {test_date}")
    print()
    
    def progress(current, total, code):
        if current % 10 == 0 or current == total:
            print(f"   进度: {current}/{total} ({current/total*100:.0f}%)")
    
    start = time.time()
    results = concurrent_fetcher.fetch_batch_concurrent(test_stocks, test_date, progress)
    elapsed = time.time() - start
    
    success = len([r for r in results if not r.empty])
    
    print(f"\n✅ 测试完成")
    print(f"   成功: {success}/{len(test_stocks)}")
    print(f"   耗时: {elapsed:.2f}秒")
    print(f"   速度: {len(test_stocks)/elapsed:.1f} 股/秒")
    print(f"\n📊 预估全量同步 (5158只):")
    print(f"   预估耗时: {5158/len(test_stocks)*elapsed:.0f}秒 ({5158/len(test_stocks)*elapsed/60:.1f}分钟)")
    print()

if __name__ == '__main__':
    sys.exit(main())
