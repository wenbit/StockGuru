#!/usr/bin/env python3
"""测试API使用的数据库连接"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('stockguru-web/backend/.env')

sys.path.insert(0, 'stockguru-web/backend')

from app.core.database import DatabaseConnection

print("测试API数据库连接\n")

with DatabaseConnection() as cursor:
    # 总记录数
    cursor.execute("SELECT COUNT(*) as total FROM daily_stock_data")
    total = cursor.fetchone()['total']
    print(f"总记录数: {total}")
    
    # 按日期统计
    cursor.execute("""
        SELECT trade_date, COUNT(*) as count
        FROM daily_stock_data
        GROUP BY trade_date
        ORDER BY trade_date DESC
        LIMIT 10
    """)
    
    print("\n按日期统计:")
    for row in cursor.fetchall():
        print(f"  {row['trade_date']}: {row['count']} 条")
    
    # 检查2025-10-16
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM daily_stock_data
        WHERE trade_date = '2025-10-16'
    """)
    count_1016 = cursor.fetchone()['count']
    print(f"\n2025-10-16的数据: {count_1016} 条")

print("\n✅ 测试完成")
