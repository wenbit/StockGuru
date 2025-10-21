#!/usr/bin/env python3
"""
清理错误数据并重新同步
"""

import os
import sys
import psycopg2
from datetime import datetime

def cleanup_and_resync():
    """清理并重新同步"""
    
    db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误：未设置数据库连接URL")
        return False
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("=" * 100)
    print("步骤 1/3: 清理错误数据")
    print("=" * 100)
    
    # 删除 09-09 和 09-10 的数据
    print("\n正在删除 2025-09-09 和 2025-09-10 的数据...")
    cur.execute("DELETE FROM daily_stock_data WHERE trade_date IN ('2025-09-09', '2025-09-10')")
    deleted_count = cur.rowcount
    print(f"✓ 已删除 {deleted_count} 条记录")
    
    # 重置同步状态
    print("\n正在重置同步状态...")
    cur.execute("""
        UPDATE daily_sync_status 
        SET status = 'pending',
            total_records = 0,
            success_count = 0,
            failed_count = 0,
            start_time = NULL,
            end_time = NULL,
            duration_seconds = NULL,
            remarks = '待重新同步（已修复计数逻辑）',
            updated_at = NOW()
        WHERE sync_date IN ('2025-09-09', '2025-09-10')
    """)
    conn.commit()
    print("✓ 同步状态已重置")
    
    # 显示清理结果
    print("\n" + "=" * 100)
    print("清理后的数据量:")
    print("-" * 100)
    cur.execute("""
        SELECT trade_date, COUNT(*) as count
        FROM daily_stock_data 
        WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-11'
        GROUP BY trade_date
        ORDER BY trade_date
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,} 条")
    
    print("\n" + "=" * 100)
    print("同步状态:")
    print("-" * 100)
    cur.execute("""
        SELECT sync_date, status, total_records, success_count, failed_count
        FROM daily_sync_status
        WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-11'
        ORDER BY sync_date
    """)
    
    for row in cur.fetchall():
        sync_date, status, total, success, failed = row
        print(f"  {sync_date}: {status:10s} | 总数={total:5d} | 成功={success:5d} | 失败={failed:5d}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 100)
    print("✅ 数据清理完成！")
    print("=" * 100)
    
    return True

if __name__ == '__main__':
    success = cleanup_and_resync()
    sys.exit(0 if success else 1)
