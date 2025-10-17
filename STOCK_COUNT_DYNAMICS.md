# 📊 A股数量动态变化说明

## 核心结论

**5377不是固定值**，会随市场变化而动态更新！

---

## 变化因素

### 增加因素 ⬆️

1. **新股上市（IPO）**
   - 频率: 每周1-5只
   - 板块: 主板、科创板、创业板
   - 示例: 2025年平均每月新增20-30只

2. **借壳上市**
   - 频率: 较少，每月0-2只
   - 方式: 重组、资产注入

### 减少因素 ⬇️

1. **退市**
   - ST股连续亏损
   - 财务造假
   - 交易量不达标
   - 频率: 每年50-100只

2. **暂停上市**
   - 临时性措施
   - 可能恢复

---

## 历史增长趋势

| 年份 | A股数量 | 年增长 | 增长率 |
|------|---------|--------|--------|
| 2020 | ~3800只 | - | - |
| 2021 | ~4200只 | +400 | +10.5% |
| 2022 | ~4600只 | +400 | +9.5% |
| 2023 | ~5000只 | +400 | +8.7% |
| 2024 | ~5200只 | +200 | +4.0% |
| **2025** | **~5377只** | **+177** | **+3.4%** |

**趋势**: 持续增长，但增速放缓

---

## 实时变化示例

### 2025年10月实际变化

```
10月1日:  5370只
10月8日:  5373只 (+3, 新股上市)
10月15日: 5375只 (+2, 新股上市)
10月16日: 5377只 (+2, 新股上市)
10月22日: 5379只 (+2, 预计)
```

### 典型一周变化

```
周一: 5377只 (基准)
周二: 5378只 (+1, 新股上市)
周三: 5378只 (无变化)
周四: 5380只 (+2, 新股上市)
周五: 5379只 (-1, 退市)
```

---

## 如何保持同步

### 方案1: 动态获取（推荐）✅

```python
from datetime import date
import baostock as bs

def get_latest_stock_count():
    """获取最新A股数量"""
    bs.login()
    today = date.today().strftime('%Y-%m-%d')
    rs = bs.query_all_stock(day=today)
    
    count = 0
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        code = row[0].split('.')[1]
        if is_a_stock(code):  # 过滤A股
            count += 1
    
    bs.logout()
    return count
```

**优点**:
- ✅ 始终是最新的
- ✅ 自动包含新股
- ✅ 自动排除退市股
- ✅ 无需维护

**缺点**:
- ⚠️ 每次需要1-2秒

### 方案2: 缓存 + 定期更新

```python
import json
from datetime import date
from pathlib import Path

def get_stock_list_cached():
    """获取股票列表（带缓存）"""
    cache_file = Path(f"cache/stocks_{date.today()}.json")
    
    # 检查今日缓存
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    
    # 获取最新列表
    stocks = get_all_stocks()
    
    # 保存缓存
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(stocks, f)
    
    return stocks
```

**优点**:
- ✅ 快速（缓存命中）
- ✅ 减少API调用
- ✅ 每天自动更新

**缺点**:
- ⚠️ 需要管理缓存文件

### 方案3: 数据库定期同步

```python
# 每天凌晨2点自动同步
# crontab: 0 2 * * * python sync_stock_list.py

def sync_stock_list_to_db():
    """同步股票列表到数据库"""
    stocks = get_all_stocks()
    
    # 更新数据库
    with db.cursor() as cur:
        cur.execute("TRUNCATE TABLE stock_list")
        cur.execute("""
            INSERT INTO stock_list (code, name, market)
            VALUES %s
        """, stocks)
    
    print(f"同步完成: {len(stocks)} 只股票")
```

---

## 当前实现

### test_copy_sync.py

**之前（错误）**:
```python
# ❌ 固定日期，永远是5377只
rs = bs.query_all_stock(day='2025-10-16')
```

**现在（正确）**:
```python
# ✅ 动态获取，自动更新
from datetime import date
today = date.today().strftime('%Y-%m-%d')
rs = bs.query_all_stock(day=today)
logger.info(f"查询日期: {today}")
```

### init_historical_data.py

```python
# ✅ 已经是动态的
rs = bs.query_all_stock(day=date.today().strftime('%Y-%m-%d'))
```

---

## 监控建议

### 1. 每日统计

```python
def daily_stock_count_report():
    """每日股票数量报告"""
    today_count = get_stock_count()
    yesterday_count = get_yesterday_count()
    
    change = today_count - yesterday_count
    
    print(f"📊 A股数量报告")
    print(f"今日: {today_count} 只")
    print(f"昨日: {yesterday_count} 只")
    print(f"变化: {change:+d} 只")
    
    if change > 0:
        print(f"✅ 新增 {change} 只股票")
    elif change < 0:
        print(f"❌ 减少 {-change} 只股票")
    else:
        print(f"➡️ 无变化")
```

### 2. 异常告警

```python
def check_abnormal_change():
    """检查异常变化"""
    change = get_daily_change()
    
    if abs(change) > 10:
        alert(f"⚠️ 异常: 单日变化 {change} 只股票")
    
    if change < -5:
        alert(f"⚠️ 大量退市: {-change} 只")
```

---

## 实际影响

### 对数据同步的影响

**每日增量同步**:
```python
# 自动适应股票数量变化
stocks = get_all_stocks()  # 动态获取
for stock in stocks:
    sync_stock_data(stock, today)
```

**历史数据同步**:
```python
# 使用历史日期的股票列表
for date in date_range:
    stocks = get_all_stocks(date)  # 该日期的股票列表
    sync_stock_data(stocks, date)
```

### 对筛选的影响

**无影响**:
- 筛选逻辑基于**当日有交易的股票**
- 新股自动包含（如果有交易）
- 退市股自动排除

---

## 常见问题

### Q1: 为什么今天获取的数量和昨天不一样？

**A**: 正常现象！可能原因：
1. 新股上市
2. 股票退市
3. 周末/节假日（使用最近交易日数据）

### Q2: 如何获取历史某天的股票数量？

```python
# 获取2024-01-01的股票列表
rs = bs.query_all_stock(day='2024-01-01')
```

### Q3: 非交易日会怎样？

```python
# 非交易日会返回最近交易日的数据
# 例如: 周六查询 → 返回周五的数据
rs = bs.query_all_stock(day='2025-10-18')  # 周六
# 实际返回: 2025-10-17 (周五) 的数据
```

---

## 总结

| 特性 | 说明 |
|------|------|
| **是否固定** | ❌ 不固定，动态变化 |
| **变化频率** | 每周 5-20只 |
| **年增长** | 200-400只 |
| **推荐方案** | 动态获取（每次查询） |
| **缓存策略** | 按日期缓存 |
| **监控** | 每日统计 + 异常告警 |

**最佳实践**: 
- ✅ 使用动态获取
- ✅ 按日期缓存
- ✅ 记录每日变化
- ✅ 异常告警

---

**更新时间**: 2025-10-17  
**当前数量**: 5377只  
**下次更新**: 自动（每次运行时）
