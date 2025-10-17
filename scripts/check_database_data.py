#!/usr/bin/env python3
"""检查数据库中的数据"""

import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
env_file = os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend', '.env')
load_dotenv(env_file)

print("🔍 检查数据库数据\n")

# 获取数据库连接
database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')

if not database_url:
    print("❌ 错误: 未找到 DATABASE_URL")
    exit(1)

print(f"✅ 数据库连接: {database_url.split('@')[1] if '@' in database_url else 'unknown'}\n")

try:
    # 连接数据库
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # 1. 检查表是否存在
    print("📊 检查表结构...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'daily_stock_data'
    """)
    
    if cursor.fetchone():
        print("✅ 表 daily_stock_data 存在\n")
    else:
        print("❌ 表 daily_stock_data 不存在！\n")
        exit(1)
    
    # 2. 检查总记录数
    print("📈 统计数据...")
    cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
    total_count = cursor.fetchone()[0]
    print(f"总记录数: {total_count} 条\n")
    
    if total_count == 0:
        print("⚠️ 数据库为空！\n")
        exit(0)
    
    # 3. 按日期统计
    print("📅 按日期统计:")
    cursor.execute("""
        SELECT trade_date, COUNT(*) as count
        FROM daily_stock_data
        GROUP BY trade_date
        ORDER BY trade_date DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} 条")
    
    print()
    
    # 4. 查看最新的几条记录
    print("🔍 最新10条记录:")
    cursor.execute("""
        SELECT stock_code, stock_name, trade_date, close_price, volume
        FROM daily_stock_data
        ORDER BY trade_date DESC, stock_code
        LIMIT 10
    """)
    
    print(f"{'股票代码':<10} {'股票名称':<15} {'交易日期':<12} {'收盘价':<10} {'成交量':<15}")
    print("-" * 75)
    
    for row in cursor.fetchall():
        print(f"{row[0]:<10} {row[1]:<15} {row[2]:<12} {row[3]:<10.2f} {row[4]:<15}")
    
    print()
    
    # 5. 检查特定日期的数据
    print("🎯 检查2025-10-16的数据:")
    cursor.execute("""
        SELECT COUNT(*) 
        FROM daily_stock_data 
        WHERE trade_date = '2025-10-16'
    """)
    count_1016 = cursor.fetchone()[0]
    print(f"2025-10-16: {count_1016} 条\n")
    
    # 6. 检查索引
    print("🔑 检查索引:")
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'daily_stock_data'
    """)
    
    indexes = cursor.fetchall()
    if indexes:
        for idx in indexes:
            print(f"  - {idx[0]}")
    else:
        print("  ⚠️ 没有索引！")
    
    print()
    
    # 7. 测试查询性能
    print("⚡ 测试查询性能:")
    import time
    
    # 测试1: 按日期查询
    start = time.time()
    cursor.execute("""
        SELECT * FROM daily_stock_data 
        WHERE trade_date = '2025-10-16'
        LIMIT 100
    """)
    cursor.fetchall()
    elapsed = time.time() - start
    print(f"  按日期查询100条: {elapsed*1000:.2f}ms")
    
    # 测试2: 按股票代码查询
    start = time.time()
    cursor.execute("""
        SELECT * FROM daily_stock_data 
        WHERE stock_code = '000001'
        LIMIT 100
    """)
    cursor.fetchall()
    elapsed = time.time() - start
    print(f"  按股票代码查询: {elapsed*1000:.2f}ms")
    
    print()
    print("✅ 检查完成！")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
