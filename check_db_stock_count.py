#!/usr/bin/env python3
"""
检查数据库中最近几天的股票数量
验证同步数量是否准确
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def main():
    print("\n" + "=" * 70)
    print("📊 数据库股票数量检查")
    print("=" * 70)
    print()
    
    try:
        import psycopg2
        
        # 从环境变量获取数据库连接
        database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        
        if not database_url:
            print("❌ 未找到数据库连接配置")
            print("   请设置环境变量: DATABASE_URL 或 NEON_DATABASE_URL")
            return 1
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 检查最近7天的数据
        print("查询最近7天的股票数量...")
        print()
        
        for i in range(7):
            check_date = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 查询该日期的股票数量
            cursor.execute("""
                SELECT COUNT(DISTINCT stock_code) as stock_count
                FROM daily_stock_data
                WHERE trade_date = %s
            """, (check_date,))
            
            result = cursor.fetchone()
            count = result[0] if result else 0
            
            # 判断是否是交易日
            if count > 0:
                print(f"  {check_date}: {count:4d} 只 ✅ (交易日)")
            else:
                print(f"  {check_date}: {count:4d} 只 ⚠️  (非交易日/无数据)")
        
        print()
        
        # 查询最近一个交易日的详细信息
        cursor.execute("""
            SELECT trade_date, COUNT(DISTINCT stock_code) as stock_count
            FROM daily_stock_data
            WHERE trade_date >= %s
            GROUP BY trade_date
            ORDER BY trade_date DESC
            LIMIT 1
        """, ((date.today() - timedelta(days=7)).strftime('%Y-%m-%d'),))
        
        result = cursor.fetchone()
        
        if result:
            last_date, last_count = result
            print("=" * 70)
            print("📈 最近交易日详情")
            print("=" * 70)
            print()
            print(f"  日期: {last_date}")
            print(f"  股票数: {last_count} 只")
            print()
            
            # 分析股票代码分布
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN stock_code LIKE '6%' THEN '上海主板'
                        WHEN stock_code LIKE '00%' THEN '深圳主板'
                        WHEN stock_code LIKE '30%' THEN '创业板'
                        WHEN stock_code LIKE '688%' THEN '科创板'
                        WHEN stock_code LIKE '8%' THEN '北交所'
                        ELSE '其他'
                    END as market,
                    COUNT(*) as count
                FROM daily_stock_data
                WHERE trade_date = %s
                GROUP BY market
                ORDER BY count DESC
            """, (last_date,))
            
            print("  市场分布:")
            total = 0
            for market, count in cursor.fetchall():
                print(f"    {market}: {count:4d} 只")
                total += count
            print(f"    总计: {total:4d} 只")
            print()
            
            # 对比预估
            print("=" * 70)
            print("🎯 对比分析")
            print("=" * 70)
            print()
            
            estimated = 5897  # 我们的预估
            print(f"  预估股票数: {estimated} 只")
            print(f"  实际股票数: {last_count} 只")
            print(f"  差异: {abs(estimated - last_count)} 只 ({abs(estimated - last_count)/last_count*100:.1f}%)")
            print()
            
            if abs(estimated - last_count) / last_count < 0.1:
                print("  ✅ 预估准确（误差 <10%）")
            elif abs(estimated - last_count) / last_count < 0.2:
                print("  ⚠️  预估基本准确（误差 10-20%）")
            else:
                print("  ❌ 预估偏差较大（误差 >20%）")
            
            print()
            
            # 重新计算预估时间
            print("=" * 70)
            print("⏱️  重新预估同步时间")
            print("=" * 70)
            print()
            
            speed = 6.7  # 股/秒
            estimated_time = last_count / speed
            
            print(f"  实际股票数: {last_count} 只")
            print(f"  平均速度: {speed} 股/秒")
            print(f"  预估耗时: {estimated_time:.0f}秒 ({estimated_time/60:.1f}分钟)")
            print()
            
        else:
            print("⚠️  数据库中没有最近7天的数据")
            print("   可能原因:")
            print("   1. 数据库为空")
            print("   2. 还未进行数据同步")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print()
        print("可能原因:")
        print("  1. 数据库连接失败")
        print("  2. 表不存在")
        print("  3. 配置错误")
        print()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
