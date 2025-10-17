#!/usr/bin/env python3
"""检查表结构"""

import os
import psycopg2
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend', '.env')
load_dotenv(env_file)

database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')

try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    print("📋 表结构:\n")
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'daily_stock_data'
        ORDER BY ordinal_position
    """)
    
    print(f"{'字段名':<25} {'数据类型':<20} {'长度':<10} {'可空':<10}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        col_name = row[0]
        data_type = row[1]
        max_length = row[2] if row[2] else 'N/A'
        nullable = row[3]
        print(f"{col_name:<25} {data_type:<20} {max_length:<10} {nullable:<10}")
    
    print("\n\n🔍 查看原始数据（不格式化）:\n")
    cursor.execute("""
        SELECT stock_code, stock_name, trade_date::text, close_price
        FROM daily_stock_data
        WHERE stock_code = '000001'
        ORDER BY trade_date DESC
        LIMIT 3
    """)
    
    for row in cursor.fetchall():
        print(f"代码: {repr(row[0])}")
        print(f"名称: {repr(row[1])}")
        print(f"日期: {repr(row[2])}")
        print(f"收盘: {repr(row[3])}")
        print("-" * 50)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
