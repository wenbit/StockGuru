#!/usr/bin/env python3
"""
实测 Baostock 同步一天数据
真实性能测试
"""

import sys
import os
import time
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def get_all_stock_codes():
    """获取所有A股代码（使用预定义列表）"""
    # 使用常见的A股代码作为测试样本
    # 实际项目中应该从数据库或API获取
    stock_codes = []
    
    # 生成常见的股票代码
    # 深圳主板 000001-002999
    for i in range(1, 3000):
        stock_codes.append(f"{i:06d}")
    
    # 上海主板 600000-603999
    for i in range(600000, 604000):
        stock_codes.append(str(i))
    
    # 创业板 300001-301999
    for i in range(300001, 302000):
        stock_codes.append(str(i))
    
    return stock_codes


def main():
    print("\n" + "=" * 70)
    print("🔍 Baostock 真实同步测试")
    print("=" * 70)
    
    import baostock as bs
    
    # 获取所有股票代码
    print("\n📋 获取股票列表...")
    stock_codes = get_all_stock_codes()
    print(f"   总股票数: {len(stock_codes)}")
    
    # 测试日期（最近的交易日）
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"   测试日期: {test_date}")
    print()
    
    # 选择测试规模
    print("选择测试规模:")
    print("   1. 小规模测试 (100只)")
    print("   2. 中规模测试 (500只)")
    print("   3. 大规模测试 (1000只)")
    print("   4. 全量测试 ({}只)".format(len(stock_codes)))
    print()
    
    choice = input("请选择 (1-4，默认1): ").strip() or "1"
    
    if choice == "1":
        test_codes = stock_codes[:100]
        test_name = "小规模"
    elif choice == "2":
        test_codes = stock_codes[:500]
        test_name = "中规模"
    elif choice == "3":
        test_codes = stock_codes[:1000]
        test_name = "大规模"
    else:
        test_codes = stock_codes
        test_name = "全量"
    
    print(f"\n开始 {test_name} 测试 ({len(test_codes)}只)...")
    print("=" * 70)
    print()
    
    # 开始测试
    bs.login()
    
    start_time = time.time()
    success_count = 0
    failed_count = 0
    empty_count = 0
    
    for i, code in enumerate(test_codes, 1):
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
            
            if data:
                success_count += 1
            else:
                empty_count += 1
            
            # 每100只输出进度
            if i % 100 == 0 or i == len(test_codes):
                elapsed = time.time() - start_time
                speed = i / elapsed if elapsed > 0 else 0
                eta = (len(test_codes) - i) / speed if speed > 0 else 0
                
                print(f"进度: {i}/{len(test_codes)} ({i/len(test_codes)*100:.1f}%) | "
                      f"成功: {success_count} | "
                      f"速度: {speed:.1f} 股/秒 | "
                      f"预计剩余: {eta:.0f}秒")
        
        except Exception as e:
            failed_count += 1
            if failed_count <= 3:
                print(f"   ⚠️  {code}: {e}")
    
    bs.logout()
    
    total_time = time.time() - start_time
    
    # 结果统计
    print()
    print("=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    print()
    
    print(f"测试规模: {test_name} ({len(test_codes)}只)")
    print(f"测试日期: {test_date}")
    print()
    
    print(f"结果统计:")
    if len(test_codes) > 0:
        print(f"   成功: {success_count} ({success_count/len(test_codes)*100:.1f}%)")
        print(f"   无数据: {empty_count} ({empty_count/len(test_codes)*100:.1f}%)")
        print(f"   失败: {failed_count} ({failed_count/len(test_codes)*100:.1f}%)")
    else:
        print(f"   ❌ 没有测试数据")
        return 1
    print()
    
    print(f"性能指标:")
    print(f"   总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
    print(f"   平均速度: {len(test_codes)/total_time:.2f} 股/秒")
    print(f"   平均耗时: {total_time/len(test_codes):.3f} 秒/股")
    print()
    
    # 预估全量
    if len(test_codes) < len(stock_codes):
        estimated_time = len(stock_codes) * (total_time / len(test_codes))
        print(f"预估全量同步 ({len(stock_codes)}只):")
        print(f"   预估耗时: {estimated_time:.0f}秒 ({estimated_time/60:.1f}分钟)")
        print()
    
    # 性能评价
    speed = len(test_codes) / total_time
    
    print("性能评价:")
    if speed > 10:
        print("   ✅ 优秀 (>10 股/秒)")
    elif speed > 5:
        print("   ✅ 良好 (5-10 股/秒)")
    elif speed > 3:
        print("   ⚠️  一般 (3-5 股/秒)")
    else:
        print("   ❌ 较慢 (<3 股/秒)")
    
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
