#!/usr/bin/env python3
"""
更新 2025-10-15 的 daily_sync_status 记录
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
project_root = Path(__file__).parent.parent
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

# 获取数据库连接
database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')

if not database_url:
    print("❌ 错误: 未找到数据库连接 URL")
    sys.exit(1)

# 同步数据（来自刚才的同步结果）
sync_data = {
    'sync_date': '2025-10-15',
    'status': 'success',
    'total_records': 5274,
    'success_count': 5274,
    'failed_count': 0,
    'start_time': '2025-10-17 14:34:41',
    'end_time': '2025-10-17 14:56:37',
    'duration_seconds': 1316,  # 21.9分钟 = 1316秒
    'error_message': None,
    'remarks': '手动同步完成，共获取5377只股票，成功入库5274条'
}

try:
    print("="*80)
    print("更新 2025-10-15 daily_sync_status 记录")
    print("="*80)
    print()
    
    # 连接数据库
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    print("✅ 数据库连接成功")
    print()
    
    # 更新 daily_sync_status
    sql = """
    UPDATE daily_sync_status
    SET 
        status = %s,
        total_records = %s,
        success_count = %s,
        failed_count = %s,
        start_time = %s,
        end_time = %s,
        duration_seconds = %s,
        error_message = %s,
        remarks = %s,
        updated_at = NOW()
    WHERE sync_date = %s
    """
    
    cursor.execute(sql, (
        sync_data['status'],
        sync_data['total_records'],
        sync_data['success_count'],
        sync_data['failed_count'],
        sync_data['start_time'],
        sync_data['end_time'],
        sync_data['duration_seconds'],
        sync_data['error_message'],
        sync_data['remarks'],
        sync_data['sync_date']
    ))
    
    rows_updated = cursor.rowcount
    conn.commit()
    
    if rows_updated > 0:
        print(f"✅ 成功更新 {rows_updated} 条记录")
        print()
        print("📝 更新内容:")
        print(f"   日期: {sync_data['sync_date']}")
        print(f"   状态: {sync_data['status']}")
        print(f"   总记录数: {sync_data['total_records']:,}")
        print(f"   成功数量: {sync_data['success_count']:,}")
        print(f"   失败数量: {sync_data['failed_count']}")
        print(f"   开始时间: {sync_data['start_time']}")
        print(f"   完成时间: {sync_data['end_time']}")
        print(f"   耗时: {sync_data['duration_seconds']}秒 ({sync_data['duration_seconds']//60}分{sync_data['duration_seconds']%60}秒)")
        print(f"   备注: {sync_data['remarks']}")
    else:
        print("⚠️  警告: 没有找到需要更新的记录")
        print("   尝试插入新记录...")
        
        # 如果没有记录，则插入
        insert_sql = """
        INSERT INTO daily_sync_status (
            sync_date, status, total_records, success_count, failed_count,
            start_time, end_time, duration_seconds, error_message, remarks,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """
        
        cursor.execute(insert_sql, (
            sync_data['sync_date'],
            sync_data['status'],
            sync_data['total_records'],
            sync_data['success_count'],
            sync_data['failed_count'],
            sync_data['start_time'],
            sync_data['end_time'],
            sync_data['duration_seconds'],
            sync_data['error_message'],
            sync_data['remarks']
        ))
        
        conn.commit()
        print("✅ 新记录已插入")
    
    print()
    
    # 验证更新
    cursor.execute("""
        SELECT sync_date, status, total_records, success_count, 
               start_time, end_time, duration_seconds, remarks
        FROM daily_sync_status 
        WHERE sync_date = %s
    """, (sync_data['sync_date'],))
    
    result = cursor.fetchone()
    
    if result:
        print("验证查询结果:")
        print(f"   日期: {result[0]}")
        print(f"   状态: {result[1]}")
        print(f"   总数: {result[2]:,}")
        print(f"   成功: {result[3]:,}")
        print(f"   开始: {result[4]}")
        print(f"   完成: {result[5]}")
        print(f"   耗时: {result[6]}秒")
        print(f"   备注: {result[7]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*80)
    print("✅ 完成")
    print("="*80)
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
