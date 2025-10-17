#!/usr/bin/env python3
"""检查A股总数"""

import baostock as bs
from datetime import date

# 登录
bs.login()
print("✅ baostock 登录成功\n")

# 获取所有股票（使用今天的日期）
today = date.today().strftime('%Y-%m-%d')
print(f"📅 查询日期: {today}\n")
rs = bs.query_all_stock(day=today)

# 统计各类股票
stats = {
    '沪市主板(600/601/603/605)': 0,
    '科创板(688)': 0,
    '深市主板(000/001)': 0,
    '中小板(002/003/004)': 0,
    '创业板(300/301)': 0,
    '北交所(8/43)': 0,
    '其他': 0,
    '指数': 0
}

all_stocks = []
while (rs.error_code == '0') & rs.next():
    row = rs.get_row_data()
    code = row[0]
    name = row[2]
    
    if code and '.' in code:
        stock_code = code.split('.')[1]
        
        # 分类统计
        if stock_code.startswith(('600', '601', '603', '605')):
            stats['沪市主板(600/601/603/605)'] += 1
            all_stocks.append((code, name))
        elif stock_code.startswith('688'):
            stats['科创板(688)'] += 1
            all_stocks.append((code, name))
        elif stock_code.startswith(('000', '001')):
            stats['深市主板(000/001)'] += 1
            all_stocks.append((code, name))
        elif stock_code.startswith(('002', '003', '004')):
            stats['中小板(002/003/004)'] += 1
            all_stocks.append((code, name))
        elif stock_code.startswith(('300', '301')):
            stats['创业板(300/301)'] += 1
            all_stocks.append((code, name))
        elif stock_code.startswith(('8', '43')):
            stats['北交所(8/43)'] += 1
            all_stocks.append((code, name))
        elif len(stock_code) <= 6 and stock_code.isdigit():
            # 可能是指数
            stats['指数'] += 1
        else:
            stats['其他'] += 1
            print(f"  其他类型: {code} - {name}")

# 输出统计
print("📊 A股市场统计")
print("=" * 60)
for category, count in stats.items():
    if count > 0:
        print(f"{category:30s}: {count:5d} 只")

print("=" * 60)
print(f"{'A股总数':30s}: {len(all_stocks):5d} 只")
print(f"{'指数数量':30s}: {stats['指数']:5d} 个")
print(f"{'其他':30s}: {stats['其他']:5d} 个")

# 登出
bs.logout()
print("\n✅ 统计完成")
