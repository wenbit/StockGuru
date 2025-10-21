#!/usr/bin/env python3
"""
测试Baostock是否能获取指定日期的数据
"""

import baostock as bs

print('测试Baostock数据获取')
print('='*60)

bs.login()

# 测试不同日期
test_dates = [
    '20251009',  # 2025-10-09
    '20251010',  # 2025-10-10
    '20251013',  # 2025-10-13
    '20251014',  # 2025-10-14
    '20251015',  # 2025-10-15
    '20251016',  # 2025-10-16
]

for date_bs in test_dates:
    date_str = f'{date_bs[:4]}-{date_bs[4:6]}-{date_bs[6:8]}'
    
    # 测试获取浦发银行的数据
    rs = bs.query_history_k_data_plus(
        'sh.600000',
        'date,code,close,volume',
        start_date=date_bs,
        end_date=date_bs,
        frequency='d',
        adjustflag='3'
    )
    
    print(f'{date_str}:', end=' ')
    
    if rs is None:
        print('❌ 返回None')
        continue
    
    if rs.error_code != '0':
        print(f'❌ 错误: {rs.error_msg}')
        continue
    
    data_list = []
    while rs.next():
        data_list.append(rs.get_row_data())
    
    if data_list:
        row = data_list[0]
        print(f'✅ 有数据 - 收盘: {row[2]}, 成交量: {row[3]}')
    else:
        print('❌ 无数据（可能非交易日或数据未更新）')

bs.logout()
print()
print('='*60)
print('结论: 检查哪些日期有数据可用')
