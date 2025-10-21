#!/usr/bin/env python3
"""
清理除2025-10-16外的其他日期数据
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.core.database import DatabaseConnection


def clean_data():
    """清理数据"""
    
    print("="*80)
    print("清理除2025-10-16外的其他日期数据")
    print("="*80)
    
    with DatabaseConnection() as cursor:
        # 1. 查看当前数据
        print("\n1. 当前数据统计:")
        cursor.execute("""
            SELECT trade_date, COUNT(*) as count 
            FROM daily_stock_data 
            GROUP BY trade_date 
            ORDER BY trade_date DESC
        """)
        
        total_before = 0
        for row in cursor.fetchall():
            count = row['count']
            total_before += count
            print(f"   {row['trade_date']}: {count:,} 条")
        
        print(f"\n   总计: {total_before:,} 条")
        
        # 2. 删除非2025-10-16的数据
        print("\n2. 删除其他日期的数据...")
        cursor.execute("""
            DELETE FROM daily_stock_data 
            WHERE trade_date <> '2025-10-16'
        """)
        deleted = cursor.rowcount
        print(f"   ✅ 已删除 {deleted:,} 条记录")
        
        # 3. 确认结果
        print("\n3. 剩余数据:")
        cursor.execute("""
            SELECT trade_date, COUNT(*) as count 
            FROM daily_stock_data 
            GROUP BY trade_date 
            ORDER BY trade_date DESC
        """)
        
        total_after = 0
        for row in cursor.fetchall():
            count = row['count']
            total_after += count
            print(f"   {row['trade_date']}: {count:,} 条")
        
        print(f"\n   总计: {total_after:,} 条")
        
        # 4. 清理同步状态表
        print("\n4. 清理同步状态表...")
        cursor.execute("""
            DELETE FROM daily_sync_status 
            WHERE sync_date NOT IN ('2025-10-16', '2025-10-17')
        """)
        deleted_status = cursor.rowcount
        print(f"   ✅ 已删除 {deleted_status} 条状态记录")
        
        # 5. 查看状态表
        print("\n5. 同步状态表:")
        cursor.execute("""
            SELECT sync_date, status, total_records 
            FROM daily_sync_status 
            ORDER BY sync_date DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   {row['sync_date']}: {row['status']} ({row['total_records']:,} 条)")
        
        print("\n" + "="*80)
        print("✅ 清理完成！")
        print("="*80)
        print(f"\n统计:")
        print(f"  删除前: {total_before:,} 条")
        print(f"  删除后: {total_after:,} 条")
        print(f"  已删除: {deleted:,} 条")
        print(f"\n保留数据:")
        print(f"  2025-10-16: {total_after:,} 条")


if __name__ == '__main__':
    try:
        clean_data()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
