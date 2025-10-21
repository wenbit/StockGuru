#!/usr/bin/env python3
"""
实时监控同步进度
"""

import os
import sys
import time
import psycopg2
from datetime import datetime

def monitor_progress(sync_date):
    """监控同步进度"""
    
    db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误：未设置数据库连接URL")
        return
    
    print(f"🔍 监控 {sync_date} 的同步进度...")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            # 获取当前数据量
            cur.execute("""
                SELECT COUNT(*) 
                FROM daily_stock_data 
                WHERE trade_date = %s
            """, (sync_date,))
            current_count = cur.fetchone()[0]
            
            # 获取同步状态
            cur.execute("""
                SELECT status, total_records, success_count, failed_count, remarks
                FROM daily_sync_status
                WHERE sync_date = %s
            """, (sync_date,))
            
            status_row = cur.fetchone()
            if status_row:
                status, total, success, failed, remarks = status_row
                progress = (current_count / 5200 * 100) if current_count > 0 else 0
                
                print(f"\r⏱️  {datetime.now().strftime('%H:%M:%S')} | "
                      f"状态: {status:10s} | "
                      f"数据库: {current_count:5d} 条 | "
                      f"进度: {progress:5.1f}% | "
                      f"成功: {success:5d} | "
                      f"失败: {failed:5d}", end='', flush=True)
            else:
                print(f"\r⏱️  {datetime.now().strftime('%H:%M:%S')} | "
                      f"数据库: {current_count:5d} 条", end='', flush=True)
            
            cur.close()
            conn.close()
            
            # 检查是否完成
            if status_row and status in ['success', 'failed'] and current_count > 4000:
                print(f"\n\n✅ 同步完成！")
                print(f"   最终状态: {status}")
                print(f"   数据量: {current_count} 条")
                print(f"   成功: {success}")
                print(f"   失败: {failed}")
                break
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  监控已停止")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")

if __name__ == '__main__':
    sync_date = sys.argv[1] if len(sys.argv) > 1 else '2025-09-09'
    monitor_progress(sync_date)
