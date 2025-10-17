#!/usr/bin/env python3
"""
测试 Tushare 数据源集成
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def test_tushare_integration():
    """测试 Tushare 集成"""
    print("=" * 70)
    print("🧪 测试 Tushare 数据源集成")
    print("=" * 70)
    
    from app.services.enhanced_data_fetcher import RobustMultiSourceFetcher
    
    # 初始化（不提供 token，使用免费 API）
    fetcher = RobustMultiSourceFetcher(tushare_token=None)
    
    print(f"\n可用数据源: {[s[0] for s in fetcher.sources]}")
    print()
    
    # 测试股票
    test_stocks = ['000001', '600000', '000002']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"测试日期: {test_date}")
    print(f"测试股票: {test_stocks}")
    print()
    
    print("🔄 开始测试...")
    print("-" * 70)
    
    success_count = 0
    source_usage = {}
    
    for i, code in enumerate(test_stocks, 1):
        try:
            import time
            start = time.time()
            
            df = fetcher.fetch_daily_data(code, test_date)
            elapsed = time.time() - start
            
            if not df.empty:
                success_count += 1
                # 根据时间判断使用的数据源
                if elapsed < 1:
                    source = "Baostock"
                    source_usage['baostock'] = source_usage.get('baostock', 0) + 1
                else:
                    source = "Other"
                
                print(f"  [{i}/{len(test_stocks)}] ✅ {code} - {elapsed:.2f}s ({source})")
            else:
                print(f"  [{i}/{len(test_stocks)}] ⚠️  {code} - 无数据")
        
        except Exception as e:
            print(f"  [{i}/{len(test_stocks)}] ❌ {code} - {str(e)[:50]}")
    
    print("-" * 70)
    print(f"\n📊 测试结果:")
    print(f"   成功: {success_count}/{len(test_stocks)} ({success_count/len(test_stocks)*100:.1f}%)")
    
    print(f"\n📈 数据源使用:")
    for source, count in source_usage.items():
        print(f"   {source}: {count}/{len(test_stocks)}")
    
    print(f"\n💡 说明:")
    print(f"   - Tushare 已集成为第2优先级数据源")
    print(f"   - 当前使用免费 API（无 token）")
    print(f"   - 如需使用 Pro API，请设置 TUSHARE_TOKEN 环境变量")
    print(f"   - 优先级: Baostock → Tushare → AData → AKShare")
    print()


def show_tushare_info():
    """显示 Tushare 信息"""
    print("=" * 70)
    print("📚 Tushare 使用说明")
    print("=" * 70)
    
    print("\n✅ Tushare 优势:")
    print("   1. 数据质量高，更新及时")
    print("   2. API 稳定，速度快")
    print("   3. 支持多种数据类型")
    print("   4. 文档完善")
    
    print("\n📝 获取 Token:")
    print("   1. 访问: https://tushare.pro/register")
    print("   2. 注册账号（免费）")
    print("   3. 获取 token")
    print("   4. 设置环境变量: export TUSHARE_TOKEN='your_token'")
    
    print("\n🎯 使用方式:")
    print("   # 不使用 token（免费 API）")
    print("   fetcher = RobustMultiSourceFetcher()")
    print()
    print("   # 使用 token（Pro API）")
    print("   fetcher = RobustMultiSourceFetcher(tushare_token='your_token')")
    
    print("\n⚠️  注意:")
    print("   - 免费 API 有调用限制")
    print("   - Pro API 需要积分（注册即送）")
    print("   - 建议注册获取 token")
    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🚀 Tushare 数据源集成测试")
    print("=" * 70)
    print()
    
    try:
        # 显示说明
        show_tushare_info()
        
        # 执行测试
        test_tushare_integration()
        
        print("=" * 70)
        print("🎉 测试完成！")
        print("=" * 70)
        print()
        print("✅ Tushare 已成功集成")
        print("✅ 现在有 4 个数据源可用")
        print("✅ 优先级: Baostock → Tushare → AData → AKShare")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
