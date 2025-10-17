#!/usr/bin/env python3
"""测试查询数据"""

import os
import psycopg2
from dotenv import load_dotenv

# 加载环境变量
env_file = os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend', '.env')
load_dotenv(env_file)

database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')

print("🔍 测试查询\n")

try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # 查询2025-10-16的数据
    print("📅 查询 2025-10-16 的数据（前20条）:\n")
    cursor.execute("""
        SELECT stock_code, stock_name, trade_date, 
               open_price, close_price, high_price, low_price,
               volume, amount, change_pct
        FROM daily_stock_data
        WHERE trade_date = '2025-10-16'
        AND stock_code ~ '^[0-9]{6}$'  -- 只要6位数字的股票代码
        ORDER BY stock_code
        LIMIT 20
    """)
    
    print(f"{'代码':<8} {'名称':<12} {'日期':<12} {'开盘':<8} {'收盘':<8} {'涨跌幅':<8} {'成交量':<12}")
    print("-" * 85)
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            stock_code = row[0] or 'N/A'
            stock_name = row[1] or 'N/A'
            trade_date = row[2] or 'N/A'
            open_price = f"{row[3]:.2f}" if row[3] else 'N/A'
            close_price = f"{row[4]:.2f}" if row[4] else 'N/A'
            change_pct = f"{row[9]:.2f}%" if row[9] else 'N/A'
            volume = f"{row[7]:,}" if row[7] else 'N/A'
            
            print(f"{stock_code:<8} {stock_name:<12} {trade_date:<12} {open_price:<8} {close_price:<8} {change_pct:<8} {volume:<12}")
    else:
        print("❌ 没有找到数据！")
    
    print(f"\n找到 {len(rows)} 条记录")
    
    # 测试特定股票
    print("\n\n🎯 查询特定股票 (000001):\n")
    cursor.execute("""
        SELECT stock_code, stock_name, trade_date, close_price, volume
        FROM daily_stock_data
        WHERE stock_code = '000001'
        ORDER BY trade_date DESC
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'代码':<8} {'名称':<12} {'日期':<12} {'收盘':<8} {'成交量':<12}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<8} {row[1] or 'N/A':<12} {row[2]:<12} {row[3]:.2f} {row[4]:,}")
    else:
        print("❌ 没有找到000001的数据！")
    
    cursor.close()
    conn.close()
    
    print("\n✅ 查询测试完成")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
