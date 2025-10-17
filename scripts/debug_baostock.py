#!/usr/bin/env python3
"""调试 baostock API"""

import baostock as bs

# 登录
bs.login()
print("✅ baostock 登录成功")

# 测试获取股票列表
from datetime import date
today = date.today().strftime('%Y-%m-%d')
print(f"\n测试获取股票列表（日期: {today}）...")
rs = bs.query_all_stock(day=today)
print(f"error_code: {rs.error_code}")
print(f"error_msg: {rs.error_msg}")
print(f"fields: {rs.fields}")

count = 0
stocks = []
while (rs.error_code == '0') & rs.next():
    row = rs.get_row_data()
    print(f"Row {count}: {row}")
    if row[1] and (row[1].startswith('sh.') or row[1].startswith('sz.')):
        stocks.append(row)
    count += 1
    if count >= 10:  # 只显示前10条
        break

print(f"\n总共获取: {count} 条")
print(f"A股数量: {len(stocks)}")

if stocks:
    print("\n前5只A股:")
    for stock in stocks[:5]:
        print(f"  {stock}")

# 登出
bs.logout()
print("\n✅ baostock 登出成功")
