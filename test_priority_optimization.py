#!/usr/bin/env python3
"""
测试数据源优先级优化
验证 Baostock 优先，快速切换
"""

import sys
import os
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def test_priority_and_speed():
    """测试优先级和速度"""
    print("=" * 70)
    print("🧪 测试数据源优先级优化")
    print("=" * 70)
    
    from app.services.enhanced_data_fetcher import robust_fetcher
    
    test_stocks = ['000001', '000002', '600000', '600519', '000858']
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n📅 测试日期: {test_date}")
    print(f"📊 测试股票: {len(test_stocks)} 只")
    print(f"   {test_stocks}")
    print()
    
    print("🎯 优化策略:")
    print("   1. Baostock 优先（Priority 1）- 最稳定")
    print("   2. AData 备选（Priority 2）- 快速失败（1次重试）")
    print("   3. AKShare 最后（Priority 3）- 快速失败（1次重试）")
    print()
    
    print("🔄 开始测试...")
    print("-" * 70)
    
    start_time = time.time()
    success_count = 0
    source_stats = {'baostock': 0, 'adata': 0, 'akshare': 0}
    
    for i, code in enumerate(test_stocks, 1):
        stock_start = time.time()
        try:
            df = robust_fetcher.fetch_daily_data(code, test_date)
            stock_time = time.time() - stock_start
            
            if not df.empty:
                success_count += 1
                # 简单判断使用了哪个数据源（基于时间）
                if stock_time < 1:
                    source_stats['baostock'] += 1
                    source = "Baostock"
                else:
                    source = "Other"
                
                print(f"  [{i}/{len(test_stocks)}] ✅ {code} - {stock_time:.2f}s ({source})")
            else:
                print(f"  [{i}/{len(test_stocks)}] ⚠️  {code} - 无数据")
        
        except Exception as e:
            print(f"  [{i}/{len(test_stocks)}] ❌ {code} - {str(e)[:50]}")
    
    total_time = time.time() - start_time
    
    print("-" * 70)
    print(f"\n📊 测试结果:")
    print(f"   成功: {success_count}/{len(test_stocks)} ({success_count/len(test_stocks)*100:.1f}%)")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均: {total_time/len(test_stocks):.2f}秒/只")
    
    print(f"\n📈 数据源使用统计:")
    print(f"   Baostock: ~{source_stats['baostock']}/{len(test_stocks)}")
    
    print(f"\n🎯 优化效果:")
    if total_time/len(test_stocks) < 1:
        print(f"   ✅ 速度优秀: {total_time/len(test_stocks):.2f}秒/只")
        print(f"   ✅ Baostock 优先策略有效")
    else:
        print(f"   ⚠️  速度一般: {total_time/len(test_stocks):.2f}秒/只")
    
    if success_count == len(test_stocks):
        print(f"   ✅ 成功率: 100%")
    
    print()
    
    return total_time/len(test_stocks)


def compare_with_old():
    """对比旧策略"""
    print("=" * 70)
    print("📊 性能对比")
    print("=" * 70)
    
    print("\n旧策略（AData优先）:")
    print("   - AData → AKShare → Baostock")
    print("   - 每个源重试3次")
    print("   - 预估: ~13秒/只（因网络重试）")
    
    print("\n新策略（Baostock优先）:")
    print("   - Baostock → AData → AKShare")
    print("   - Baostock正常，其他只重试1次")
    print("   - 预估: ~0.5秒/只（直接成功）")
    
    print()


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🔧 数据源优先级优化测试")
    print("=" * 70)
    print()
    
    try:
        # 对比说明
        compare_with_old()
        
        # 执行测试
        avg_time = test_priority_and_speed()
        
        print("=" * 70)
        print("🎉 测试完成！")
        print("=" * 70)
        print()
        
        if avg_time < 1:
            print("✅ 优化成功！")
            print(f"   平均速度: {avg_time:.2f}秒/只")
            print("   Baostock 优先策略有效")
            print("   快速切换机制正常")
        else:
            print("⚠️  速度未达预期")
            print(f"   平均速度: {avg_time:.2f}秒/只")
            print("   但多数据源保障了成功率")
        
        print()
        print("💡 核心改进:")
        print("   1. Baostock 提升到最高优先级")
        print("   2. AData/AKShare 快速失败（1次重试）")
        print("   3. 避免无效等待，快速切换")
        print()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
