#!/usr/bin/env python3
"""
测试进程池方案
"""

import sys
import os
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def main():
    print("\n" + "=" * 70)
    print("🧪 进程池方案测试")
    print("=" * 70)
    
    from app.services.concurrent_data_fetcher import concurrent_fetcher
    
    # 测试10只股票
    test_stocks = ['000001', '000002', '600000', '600519', '000858',
                   '601318', '600036', '601166', '600276', '600030']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试配置:")
    print(f"   股票数量: {len(test_stocks)}")
    print(f"   并发方式: 进程池")
    print(f"   进程数: 5")
    print(f"   测试日期: {test_date}")
    print()
    
    def progress(current, total, code):
        if current % 5 == 0 or current == total:
            print(f"   进度: {current}/{total} ({current/total*100:.0f}%)")
    
    print("🔄 开始测试...")
    start = time.time()
    
    try:
        results = concurrent_fetcher.fetch_batch_concurrent(
            test_stocks,
            test_date,
            progress_callback=progress
        )
        
        elapsed = time.time() - start
        success = len([r for r in results if not r.empty])
        
        print(f"\n✅ 测试完成")
        print(f"   成功: {success}/{len(test_stocks)} ({success/len(test_stocks)*100:.1f}%)")
        print(f"   耗时: {elapsed:.2f}秒")
        print(f"   速度: {len(test_stocks)/elapsed:.1f} 股/秒")
        
        if success == len(test_stocks):
            print(f"\n🎉 进程池方案工作正常！")
            print(f"\n📊 预估全量同步 (5158只):")
            estimated = 5158 / len(test_stocks) * elapsed
            print(f"   预估耗时: {estimated:.0f}秒 ({estimated/60:.1f}分钟)")
            print(f"   vs 串行(14分钟): 提升 {14/(estimated/60):.1f}x")
        else:
            print(f"\n⚠️  成功率: {success/len(test_stocks)*100:.1f}%")
            print(f"   可能需要调整进程数或使用串行方案")
        
        print()
        return 0
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
