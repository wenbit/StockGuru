#!/usr/bin/env python3
"""
更新 2025-10-15 的同步日志记录
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
    'sync_type': 'daily',
    'status': 'success',
    'total_stocks': 5377,
    'success_count': 5274,
    'failed_count': 0,
    'started_at': '2025-10-17 14:34:41',  # 从日志中获取
    'completed_at': '2025-10-17 14:56:37',  # 从日志中获取
    'error_message': None
}

try:
    print("="*80)
    print("更新 2025-10-15 同步日志")
    print("="*80)
    print()
    
    # 连接数据库
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    print("✅ 数据库连接成功")
    print()
    
    # 插入或更新同步日志
    sql = """
    INSERT INTO sync_logs (
        sync_date, sync_type, status, total_stocks, success_count, failed_count,
        error_message, started_at, completed_at, created_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
    )
    ON CONFLICT (sync_date, sync_type) 
    DO UPDATE SET
        status = EXCLUDED.status,
        total_stocks = EXCLUDED.total_stocks,
        success_count = EXCLUDED.success_count,
        failed_count = EXCLUDED.failed_count,
        error_message = EXCLUDED.error_message,
        started_at = EXCLUDED.started_at,
        completed_at = EXCLUDED.completed_at
    """
    
    cursor.execute(sql, (
        sync_data['sync_date'],
        sync_data['sync_type'],
        sync_data['status'],
        sync_data['total_stocks'],
        sync_data['success_count'],
        sync_data['failed_count'],
        sync_data['error_message'],
        sync_data['started_at'],
        sync_data['completed_at']
    ))
    
    conn.commit()
    
    print("📝 同步日志记录:")
    print(f"   日期: {sync_data['sync_date']}")
    print(f"   类型: {sync_data['sync_type']}")
    print(f"   状态: {sync_data['status']}")
    print(f"   总股票数: {sync_data['total_stocks']:,}")
    print(f"   成功数量: {sync_data['success_count']:,}")
    print(f"   失败数量: {sync_data['failed_count']}")
    print(f"   开始时间: {sync_data['started_at']}")
    print(f"   完成时间: {sync_data['completed_at']}")
    print()
    
    # 验证插入
    cursor.execute("""
        SELECT sync_date, status, total_stocks, success_count, 
               started_at, completed_at
        FROM sync_logs 
        WHERE sync_date = %s AND sync_type = %s
    """, (sync_data['sync_date'], sync_data['sync_type']))
    
    result = cursor.fetchone()
    
    if result:
        print("✅ 同步日志已成功更新到数据库")
        print()
        print("验证查询结果:")
        print(f"   日期: {result[0]}")
        print(f"   状态: {result[1]}")
        print(f"   总数: {result[2]:,}")
        print(f"   成功: {result[3]:,}")
        print(f"   开始: {result[4]}")
        print(f"   完成: {result[5]}")
    else:
        print("⚠️  警告: 未找到插入的记录")
    
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
