#!/usr/bin/env python3
"""
测试优化获取器
预期提速 2倍
"""

import sys
import os
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def main():
    print("\n" + "=" * 70)
    print("🚀 优化获取器测试")
    print("=" * 70)
    
    from app.services.optimized_fetcher import optimized_fetcher
    
    # 测试50只股票
    test_stocks = [
        '000001', '000002', '600000', '600519', '000858',
        '601318', '600036', '601166', '600276', '600030'
    ] * 5
    
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试配置:")
    print(f"   股票数量: {len(test_stocks)}")
    print(f"   优化方式: 预取 + 并行处理")
    print(f"   测试日期: {test_date}")
    print()
    
    def progress(current, total, code):
        if current % 10 == 0 or current == total:
            print(f"   进度: {current}/{total} ({current/total*100:.0f}%)")
    
    print("🔄 阶段1: 获取数据（带预取）...")
    start = time.time()
    
    raw_data = optimized_fetcher.fetch_all_optimized(
        test_stocks,
        test_date,
        progress_callback=progress
    )
    
    fetch_time = time.time() - start
    
    print(f"\n✅ 获取完成")
    print(f"   成功: {len(raw_data)}/{len(test_stocks)}")
    print(f"   耗时: {fetch_time:.2f}秒")
    print(f"   速度: {len(test_stocks)/fetch_time:.1f} 股/秒")
    
    # 阶段2: 并行处理
    print(f"\n🔄 阶段2: 并行处理数据...")
    process_start = time.time()
    
    processed_data = optimized_fetcher.process_data_parallel(raw_data, max_workers=4)
    
    process_time = time.time() - process_start
    
    print(f"\n✅ 处理完成")
    print(f"   记录数: {len(processed_data)}")
    print(f"   耗时: {process_time:.2f}秒")
    
    # 总结
    total_time = time.time() - start
    
    print(f"\n" + "=" * 70)
    print(f"📊 测试总结")
    print(f"=" * 70)
    print(f"总耗时: {total_time:.2f}秒")
    print(f"├─ 获取: {fetch_time:.2f}秒 ({fetch_time/total_time*100:.0f}%)")
    print(f"└─ 处理: {process_time:.2f}秒 ({process_time/total_time*100:.0f}%)")
    print()
    print(f"平均速度: {len(test_stocks)/total_time:.1f} 股/秒")
    print()
    
    # 预估全量
    print(f"📈 预估全量同步 (5158只):")
    estimated = 5158 / len(test_stocks) * total_time
    print(f"   预估耗时: {estimated:.0f}秒 ({estimated/60:.1f}分钟)")
    
    # 对比
    baseline = 14  # 分钟
    speedup = baseline / (estimated/60)
    print(f"\n🎯 vs 基准(14分钟):")
    print(f"   提升: {speedup:.1f}x")
    
    if speedup >= 1.5:
        print(f"   评价: ✅ 优化有效！")
    else:
        print(f"   评价: ⚠️  提升有限")
    
    print()
    return 0

if __name__ == '__main__':
    sys.exit(main())
