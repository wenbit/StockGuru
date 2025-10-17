#!/usr/bin/env python3
"""
详细测试 Tushare 是否真正可用
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def test_tushare_direct():
    """直接测试 Tushare API"""
    print("=" * 70)
    print("🧪 测试 1: 直接测试 Tushare API")
    print("=" * 70)
    
    try:
        import tushare as ts
        print("✅ Tushare 已安装")
        print(f"   版本: {ts.__version__}")
    except ImportError:
        print("❌ Tushare 未安装")
        return False
    
    # 测试免费 API
    print("\n测试免费 API (get_k_data)...")
    try:
        test_code = '000001'
        test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"   股票代码: {test_code}")
        print(f"   日期: {test_date}")
        
        df = ts.get_k_data(test_code, start=test_date, end=test_date)
        
        if not df.empty:
            print(f"✅ 免费 API 可用")
            print(f"   获取数据: {len(df)} 条")
            print(f"\n   数据示例:")
            print(df.head())
            return True
        else:
            print("⚠️  免费 API 返回空数据（可能非交易日）")
            
            # 尝试获取最近的数据
            print("\n尝试获取最近5天的数据...")
            start_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
            df = ts.get_k_data(test_code, start=start_date)
            
            if not df.empty:
                print(f"✅ 免费 API 可用")
                print(f"   获取数据: {len(df)} 条")
                print(f"\n   最新数据:")
                print(df.tail(3))
                return True
            else:
                print("❌ 免费 API 无法获取数据")
                return False
    
    except Exception as e:
        print(f"❌ 免费 API 测试失败: {e}")
        return False


def test_tushare_fetcher():
    """测试 Tushare 获取器"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: 测试 Tushare 获取器")
    print("=" * 70)
    
    from app.services.enhanced_data_fetcher import EnhancedTushareFetcher
    
    fetcher = EnhancedTushareFetcher(token=None)
    
    if not fetcher.is_available():
        print("❌ Tushare 获取器不可用")
        return False
    
    print("✅ Tushare 获取器已初始化")
    
    # 测试获取数据
    test_stocks = ['000001', '600000']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票: {test_stocks}")
    print(f"测试日期: {test_date}")
    print()
    
    success_count = 0
    for code in test_stocks:
        print(f"获取 {code}...")
        try:
            df = fetcher.fetch_daily_data(code, test_date, max_retries=2)
            
            if not df.empty:
                print(f"  ✅ 成功获取 {len(df)} 条数据")
                success_count += 1
            else:
                print(f"  ⚠️  返回空数据")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    print(f"\n成功率: {success_count}/{len(test_stocks)}")
    return success_count > 0


def test_multi_source_with_tushare():
    """测试多数据源（包含 Tushare）"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: 测试多数据源切换（包含 Tushare）")
    print("=" * 70)
    
    from app.services.enhanced_data_fetcher import RobustMultiSourceFetcher
    import time
    
    fetcher = RobustMultiSourceFetcher(tushare_token=None)
    
    print(f"\n可用数据源: {[s[0] for s in fetcher.sources]}")
    
    if 'tushare' not in [s[0] for s in fetcher.sources]:
        print("⚠️  Tushare 未加载到数据源列表")
        return False
    
    print("✅ Tushare 已加载到数据源列表")
    
    # 测试获取
    test_stocks = ['000001', '600000', '000002']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票: {test_stocks}")
    print(f"测试日期: {test_date}")
    print()
    
    success_count = 0
    total_time = 0
    
    for code in test_stocks:
        start = time.time()
        try:
            df = fetcher.fetch_daily_data(code, test_date)
            elapsed = time.time() - start
            total_time += elapsed
            
            if not df.empty:
                success_count += 1
                print(f"✅ {code} - {elapsed:.2f}s")
            else:
                print(f"⚠️  {code} - 无数据")
        except Exception as e:
            print(f"❌ {code} - {str(e)[:50]}")
    
    print(f"\n成功率: {success_count}/{len(test_stocks)}")
    print(f"平均速度: {total_time/len(test_stocks):.2f}秒/只")
    
    return success_count == len(test_stocks)


def test_tushare_vs_baostock():
    """对比 Tushare 和 Baostock"""
    print("\n" + "=" * 70)
    print("🧪 测试 4: Tushare vs Baostock 对比")
    print("=" * 70)
    
    import time
    
    test_code = '000001'
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n测试股票: {test_code}")
    print(f"测试日期: {test_date}")
    print()
    
    # 测试 Baostock
    print("1. Baostock:")
    try:
        import baostock as bs
        bs.login()
        
        start = time.time()
        rs = bs.query_history_k_data_plus(
            f"sz.{test_code}",
            "date,code,open,high,low,close,volume,amount",
            start_date=test_date,
            end_date=test_date
        )
        
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        bs.logout()
        elapsed = time.time() - start
        
        if data:
            print(f"   ✅ 成功获取 {len(data)} 条")
            print(f"   耗时: {elapsed:.2f}秒")
        else:
            print(f"   ⚠️  无数据")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 测试 Tushare
    print("\n2. Tushare:")
    try:
        import tushare as ts
        
        start = time.time()
        df = ts.get_k_data(test_code, start=test_date, end=test_date)
        elapsed = time.time() - start
        
        if not df.empty:
            print(f"   ✅ 成功获取 {len(df)} 条")
            print(f"   耗时: {elapsed:.2f}秒")
        else:
            print(f"   ⚠️  无数据")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🔍 Tushare 详细可用性测试")
    print("=" * 70)
    print()
    
    results = {}
    
    try:
        # 测试1: 直接测试 API
        results['direct_api'] = test_tushare_direct()
        
        # 测试2: 测试获取器
        results['fetcher'] = test_tushare_fetcher()
        
        # 测试3: 测试多数据源
        results['multi_source'] = test_multi_source_with_tushare()
        
        # 测试4: 对比测试
        test_tushare_vs_baostock()
        
        # 总结
        print("=" * 70)
        print("📊 测试总结")
        print("=" * 70)
        print()
        
        all_passed = all(results.values())
        
        print("测试结果:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print()
        
        if all_passed:
            print("🎉 所有测试通过！")
            print()
            print("✅ Tushare 完全可用")
            print("✅ 已成功集成到多数据源系统")
            print("✅ 现在有 4 个数据源可用")
            print()
            print("📊 数据源优先级:")
            print("   1. Baostock (最稳定)")
            print("   2. Tushare (数据质量高)")
            print("   3. AData (备选)")
            print("   4. AKShare (最后)")
            print()
            return 0
        else:
            print("⚠️  部分测试未通过")
            print()
            print("💡 可能原因:")
            print("   1. 测试日期非交易日")
            print("   2. 网络连接问题")
            print("   3. API 限制")
            print()
            print("建议:")
            print("   - 尝试不同的日期")
            print("   - 检查网络连接")
            print("   - 考虑注册 Tushare Pro 获取 token")
            print()
            return 1
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
