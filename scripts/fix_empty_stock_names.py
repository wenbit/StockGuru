#!/usr/bin/env python3
"""修复空的股票名称"""

import os
import psycopg2
import baostock as bs
from dotenv import load_dotenv

env_file = os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend', '.env')
load_dotenv(env_file)

database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')

print("🔧 修复空的股票名称\n")

try:
    # 连接数据库
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # 查找stock_name为空的记录
    cursor.execute("""
        SELECT DISTINCT stock_code
        FROM daily_stock_data
        WHERE stock_name = '' OR stock_name IS NULL
    """)
    
    empty_codes = [row[0] for row in cursor.fetchall()]
    print(f"找到 {len(empty_codes)} 个股票代码的名称为空\n")
    
    if not empty_codes:
        print("✅ 没有需要修复的数据")
        exit(0)
    
    # 登录baostock
    bs.login()
    print("✅ baostock 登录成功\n")
    
    # 获取股票名称映射
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    rs = bs.query_all_stock(day=today)
    
    stock_names = {}
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        code = row[0]
        name = row[2]
        if code and '.' in code:
            stock_code = code.split('.')[1]
            if name:
                stock_names[stock_code] = name
    
    print(f"获取到 {len(stock_names)} 个股票名称\n")
    
    # 更新数据库
    updated = 0
    not_found = 0
    
    print("开始更新...")
    for stock_code in empty_codes:
        if stock_code in stock_names:
            stock_name = stock_names[stock_code]
            cursor.execute("""
                UPDATE daily_stock_data
                SET stock_name = %s
                WHERE stock_code = %s AND (stock_name = '' OR stock_name IS NULL)
            """, (stock_name, stock_code))
            updated += cursor.rowcount
            if updated % 100 == 0:
                print(f"  已更新 {updated} 条记录...")
        else:
            not_found += 1
    
    conn.commit()
    
    print(f"\n✅ 修复完成!")
    print(f"  更新: {updated} 条")
    print(f"  未找到: {not_found} 个")
    
    bs.logout()
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
