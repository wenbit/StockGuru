#!/usr/bin/env python3
"""
测试 Baostock 并发可行性
"""

import sys
import os
import time
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

def test_baostock_single_thread():
    """测试单线程 Baostock"""
    print("=" * 70)
    print("🧪 测试 1: 单线程 Baostock")
    print("=" * 70)
    
    import baostock as bs
    
    test_stocks = ['000001', '000002', '600000', '600519', '000858']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票: {test_stocks}")
    print(f"测试日期: {test_date}")
    print()
    
    # 登录
    bs.login()
    
    start = time.time()
    success = 0
    
    for code in test_stocks:
        prefix = "sh." if code.startswith('6') else "sz."
        rs = bs.query_history_k_data_plus(
            f"{prefix}{code}",
            "date,code,open,high,low,close,volume,amount",
            start_date=test_date,
            end_date=test_date
        )
        
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        if data:
            success += 1
            print(f"  ✅ {code}")
        else:
            print(f"  ⚠️  {code} - 无数据")
    
    elapsed = time.time() - start
    
    bs.logout()
    
    print(f"\n结果:")
    print(f"  成功: {success}/{len(test_stocks)}")
    print(f"  耗时: {elapsed:.2f}秒")
    print(f"  平均: {elapsed/len(test_stocks):.2f}秒/只")
    print()
    
    return elapsed


def fetch_single_stock(code, test_date):
    """单个股票获取（供线程池调用）"""
    import baostock as bs
    
    # 每个线程需要独立登录
    bs.login()
    
    try:
        prefix = "sh." if code.startswith('6') else "sz."
        rs = bs.query_history_k_data_plus(
            f"{prefix}{code}",
            "date,code,open,high,low,close,volume,amount",
            start_date=test_date,
            end_date=test_date
        )
        
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        return {'code': code, 'success': len(data) > 0, 'data': data}
    
    except Exception as e:
        return {'code': code, 'success': False, 'error': str(e)}
    
    finally:
        bs.logout()


def test_baostock_concurrent():
    """测试并发 Baostock"""
    print("=" * 70)
    print("🧪 测试 2: 并发 Baostock (5 workers)")
    print("=" * 70)
    
    test_stocks = ['000001', '000002', '600000', '600519', '000858']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票: {test_stocks}")
    print(f"测试日期: {test_date}")
    print(f"并发数: 5")
    print()
    
    start = time.time()
    success = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_single_stock, code, test_date) for code in test_stocks]
        
        for future in futures:
            result = future.result()
            if result['success']:
                success += 1
                print(f"  ✅ {result['code']}")
            else:
                print(f"  ❌ {result['code']} - {result.get('error', '无数据')}")
    
    elapsed = time.time() - start
    
    print(f"\n结果:")
    print(f"  成功: {success}/{len(test_stocks)}")
    print(f"  耗时: {elapsed:.2f}秒")
    print(f"  平均: {elapsed/len(test_stocks):.2f}秒/只")
    print()
    
    return elapsed


def test_baostock_high_concurrency():
    """测试高并发 Baostock"""
    print("=" * 70)
    print("🧪 测试 3: 高并发 Baostock (10 workers, 20只)")
    print("=" * 70)
    
    test_stocks = ['000001', '000002', '600000', '600519', '000858'] * 4
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票数: {len(test_stocks)}")
    print(f"测试日期: {test_date}")
    print(f"并发数: 10")
    print()
    
    start = time.time()
    success = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_single_stock, code, test_date) for code in test_stocks]
        
        for i, future in enumerate(futures, 1):
            result = future.result()
            if result['success']:
                success += 1
            else:
                errors.append(result)
            
            if i % 5 == 0:
                print(f"  进度: {i}/{len(test_stocks)}")
    
    elapsed = time.time() - start
    
    print(f"\n结果:")
    print(f"  成功: {success}/{len(test_stocks)} ({success/len(test_stocks)*100:.1f}%)")
    print(f"  失败: {len(errors)}")
    print(f"  耗时: {elapsed:.2f}秒")
    print(f"  平均: {elapsed/len(test_stocks):.2f}秒/只")
    print(f"  速度: {len(test_stocks)/elapsed:.1f} 股/秒")
    
    if errors:
        print(f"\n  错误示例:")
        for err in errors[:3]:
            print(f"    {err['code']}: {err.get('error', '未知')}")
    
    print()
    
    return elapsed, success, len(errors)


def main():
    print("\n" + "=" * 70)
    print("🔍 Baostock 并发可行性测试")
    print("=" * 70)
    print()
    
    try:
        # 测试1: 单线程
        single_time = test_baostock_single_thread()
        
        # 测试2: 低并发
        concurrent_time = test_baostock_concurrent()
        
        # 测试3: 高并发
        high_time, high_success, high_errors = test_baostock_high_concurrency()
        
        # 总结
        print("=" * 70)
        print("📊 测试总结")
        print("=" * 70)
        print()
        
        print("性能对比:")
        print(f"  单线程 (5只): {single_time:.2f}秒")
        print(f"  并发5 (5只): {concurrent_time:.2f}秒")
        print(f"  并发10 (20只): {high_time:.2f}秒")
        print()
        
        if concurrent_time < single_time:
            speedup = single_time / concurrent_time
            print(f"✅ 并发有效！")
            print(f"   提速: {speedup:.1f}x")
        else:
            print(f"⚠️  并发效果不明显")
        
        print()
        print("💡 结论:")
        
        if high_errors == 0:
            print("  ✅ Baostock 支持并发")
            print("  ✅ 无错误，稳定性好")
            print("  ✅ 建议使用 10 个并发线程")
            print()
            print("  预估全量同步 (5158只):")
            print(f"    耗时: {5158 * (high_time/20):.0f}秒 ({5158 * (high_time/20)/60:.1f}分钟)")
        else:
            print("  ⚠️  Baostock 并发有问题")
            print(f"  ⚠️  错误率: {high_errors/20*100:.1f}%")
            print("  💡 建议:")
            print("    - 降低并发数 (5个)")
            print("    - 或使用串行获取")
        
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
