#!/usr/bin/env python3
"""
修复同步状态数据
- 修正失败数大于总数的异常数据
- 将有失败记录的任务状态改为 'failed'
"""

import os
import sys
import psycopg2
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def fix_sync_status():
    """修复同步状态"""
    
    # 获取数据库连接
    db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误：未设置 NEON_DATABASE_URL 或 DATABASE_URL 环境变量")
        return
    
    print("🔧 开始修复同步状态数据...")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. 查找异常数据（失败数 > 0 但状态为 success）
        print("\n1️⃣  查找异常数据...")
        cur.execute("""
            SELECT sync_date, status, total_records, success_count, failed_count, remarks
            FROM daily_sync_status
            WHERE failed_count > 0 AND status = 'success'
            ORDER BY sync_date
        """)
        
        abnormal_records = cur.fetchall()
        
        if not abnormal_records:
            print("✅ 没有发现异常数据")
        else:
            print(f"⚠️  发现 {len(abnormal_records)} 条异常数据：")
            for record in abnormal_records:
                sync_date, status, total, success, failed, remarks = record
                print(f"   {sync_date}: 总数={total}, 成功={success}, 失败={failed}, 状态={status}")
        
        # 2. 修复：将有失败记录的任务状态改为 failed
        if abnormal_records:
            print(f"\n2️⃣  修复异常数据...")
            for record in abnormal_records:
                sync_date = record[0]
                success = record[3]
                failed = record[4]
                
                # 更新状态为 failed
                cur.execute("""
                    UPDATE daily_sync_status
                    SET status = 'failed',
                        remarks = %s,
                        updated_at = NOW()
                    WHERE sync_date = %s
                """, (f'同步失败: 成功{success}, 失败{failed}', sync_date))
                
                print(f"   ✅ 已修复 {sync_date}: 状态改为 'failed'")
            
            conn.commit()
            print(f"\n✅ 已修复 {len(abnormal_records)} 条记录")
        
        # 3. 查找失败数异常大的数据（失败数 > 总数）
        print(f"\n3️⃣  查找失败数异常的数据...")
        cur.execute("""
            SELECT sync_date, status, total_records, success_count, failed_count, remarks
            FROM daily_sync_status
            WHERE failed_count > total_records
            ORDER BY sync_date
        """)
        
        invalid_records = cur.fetchall()
        
        if not invalid_records:
            print("✅ 没有发现失败数异常的数据")
        else:
            print(f"⚠️  发现 {len(invalid_records)} 条失败数异常的数据：")
            for record in invalid_records:
                sync_date, status, total, success, failed, remarks = record
                print(f"   {sync_date}: 总数={total}, 成功={success}, 失败={failed} ❌")
            
            # 询问是否修复
            print(f"\n这些数据的失败数明显错误，建议重新同步这些日期。")
            print(f"是否将这些记录状态改为 'pending' 以便重新同步？(y/n): ", end='')
            choice = input().strip().lower()
            
            if choice == 'y':
                for record in invalid_records:
                    sync_date = record[0]
                    
                    # 重置为 pending 状态
                    cur.execute("""
                        UPDATE daily_sync_status
                        SET status = 'pending',
                            total_records = 0,
                            success_count = 0,
                            failed_count = 0,
                            remarks = '待重新同步（数据异常已重置）',
                            updated_at = NOW()
                        WHERE sync_date = %s
                    """, (sync_date,))
                    
                    print(f"   ✅ 已重置 {sync_date}: 状态改为 'pending'")
                
                conn.commit()
                print(f"\n✅ 已重置 {len(invalid_records)} 条记录，可以重新同步")
        
        # 4. 显示修复后的统计
        print(f"\n4️⃣  修复后的统计...")
        cur.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(CASE WHEN failed_count > 0 THEN 1 ELSE 0 END) as has_failed
            FROM daily_sync_status
            GROUP BY status
            ORDER BY status
        """)
        
        stats = cur.fetchall()
        print("\n状态统计：")
        for status, count, has_failed in stats:
            print(f"   {status}: {count} 条 (其中有失败记录: {has_failed})")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ 修复完成！")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_sync_status()
