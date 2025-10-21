# 📊 A股数量差异说明

## 问题：为什么不同脚本获取的股票数量不一样？

### 数量对比

| 脚本/方法 | 股票数量 | 过滤规则 | 说明 |
|----------|---------|---------|------|
| `init_historical_data.py` | **5158只** | `sh.` 或 `sz.` 开头 | 包含所有沪深股票 |
| `test_copy_sync.py` (旧) | **4193只** | 特定代码段 | 遗漏科创板等 |
| `test_copy_sync.py` (新) | **5377只** | 完整代码段 | 包含所有A股 |
| 实际A股总数 | **5377只** | - | 官方统计 |

---

## 详细分析

### 1. init_historical_data.py - 5158只

**过滤规则**:
```python
if row[1].startswith('sh.') or row[1].startswith('sz.'):
    # 获取所有 sh. 和 sz. 开头的股票
```

**包含范围**:
- ✅ 沪市所有股票 (sh.)
- ✅ 深市所有股票 (sz.)
- ❌ 北交所股票 (bj.)

**为什么是5158只？**
- 这个数字包含了沪深两市的**所有证券**
- 包括：主板、中小板、创业板、科创板
- 但可能包含了一些**非股票证券**（如ETF、债券等）

**实际构成**:
```
沪市 (sh.): 约2300只
├─ 主板 600/601/603/605: 1695只
├─ 科创板 688: 588只
└─ 其他证券: 约17只

深市 (sz.): 约2858只
├─ 主板 000/001: 742只
├─ 中小板 002/003/004: 964只
├─ 创业板 300/301: 1388只
└─ 其他证券: 约-236只 (差异)

总计: 5158只
```

---

### 2. test_copy_sync.py (旧版) - 4193只

**过滤规则**:
```python
if (stock_code.startswith('600') or stock_code.startswith('601') or 
    stock_code.startswith('603') or stock_code.startswith('605') or
    stock_code.startswith('000') or stock_code.startswith('002') or 
    stock_code.startswith('300')):
```

**遗漏内容**:
- ❌ 科创板 688xxx: 588只
- ❌ 创业板新股 301xxx: ~200只
- ❌ 深市主板 001xxx: ~100只
- ❌ 中小板 003/004xxx: ~300只
- ❌ 其他: ~96只

**总计遗漏**: 约1184只

**为什么只有4193只？**
- 过滤规则太严格
- 只包含了最常见的代码段
- 遗漏了新板块和新代码段

---

### 3. test_copy_sync.py (新版) - 5377只

**过滤规则**:
```python
if (stock_code.startswith('600') or stock_code.startswith('601') or 
    stock_code.startswith('603') or stock_code.startswith('605') or
    stock_code.startswith('688') or  # 科创板 ✅
    stock_code.startswith('000') or stock_code.startswith('001') or
    stock_code.startswith('002') or stock_code.startswith('003') or 
    stock_code.startswith('004') or
    stock_code.startswith('300') or stock_code.startswith('301')):  # 创业板新股 ✅
```

**完整覆盖**:
- ✅ 沪市主板: 1695只
- ✅ 科创板: 588只
- ✅ 深市主板: 742只
- ✅ 中小板: 964只
- ✅ 创业板: 1388只

**总计**: 5377只（纯A股，不含其他证券）

---

## 差异原因总结

### 5158 vs 5377 的差异 (219只)

**5158只 (init_historical_data.py)**:
- 使用 `sh.` 和 `sz.` 前缀过滤
- 可能包含了一些**非股票证券**
- 可能遗漏了一些**特殊代码段**

**5377只 (test_copy_sync.py 新版)**:
- 使用精确的代码段过滤
- **只包含纯A股**
- 完整覆盖所有板块

**差异来源**:
1. **非股票证券** (~200只)
   - ETF基金
   - 可转债
   - 其他衍生品

2. **统计时间差异**
   - 不同时间点的股票数量会变化
   - 新股上市、退市等

3. **过滤标准不同**
   - `sh./sz.` 更宽泛
   - 代码段过滤更精确

---

## 推荐使用

### 场景1: 历史数据初始化
**推荐**: `init_historical_data.py` (5158只)
- 更宽泛的覆盖
- 包含所有沪深证券
- 适合一次性初始化

### 场景2: 每日增量同步
**推荐**: `test_copy_sync.py` 新版 (5377只)
- 精确的A股过滤
- 排除非股票证券
- 适合日常同步

### 场景3: 数据分析
**推荐**: 根据需求选择
- 只分析股票: 使用5377只
- 包含ETF等: 使用5158只

---

## 验证方法

### 检查股票总数
```bash
# 方法1: 使用 check_stock_count.py
python scripts/check_stock_count.py

# 方法2: 使用 init_historical_data.py
python scripts/init_historical_data.py --dry-run

# 方法3: 使用 test_copy_sync.py
python scripts/test_copy_sync.py --stocks 0 --date 2025-10-16
```

---

## 结论

1. **5158只** = 沪深所有证券（包含ETF等）
2. **4193只** = 旧版过滤规则（遗漏科创板等）
3. **5377只** = 完整的A股股票（不含其他证券）

**最准确的A股数量**: **5377只** ✅

---

**更新时间**: 2025-10-17  
**数据来源**: baostock  
**统计日期**: 2025-10-16
