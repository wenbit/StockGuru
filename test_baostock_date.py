#!/usr/bin/env python3
"""测试 baostock 在指定日期是否有数据"""

import baostock as bs

# 登录
lg = bs.login()
print(f"登录结果: {lg.error_code} - {lg.error_msg}")

# 测试获取一只股票的数据
test_code = "sh.600000"  # 浦发银行
test_date = "2025-10-14"

rs = bs.query_history_k_data_plus(
    test_code,
    "date,code,open,high,low,close,volume",
    start_date=test_date,
    end_date=test_date,
    frequency="d",
    adjustflag="2"
)

print(f"\n查询结果: {rs.error_code} - {rs.error_msg}")
print(f"字段: {rs.fields}")

data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

print(f"\n获取到 {len(data_list)} 条数据")
if data_list:
    print(f"数据示例: {data_list[0]}")
else:
    print("没有数据！可能不是交易日或数据未更新")

# 登出
bs.logout()
