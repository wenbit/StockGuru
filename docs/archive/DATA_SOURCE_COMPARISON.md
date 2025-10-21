# 📊 数据源对比分析报告

## 🎯 目标
分析 AKShare 和 AData 是否可以替代/补充当前的 baostock，提升同步入库性能

---

## 📋 当前使用：baostock

### 优势
- ✅ **免费无限制**
- ✅ **稳定性高**
- ✅ **数据质量好**
- ✅ **无需API Key**

### 劣势
- ❌ **不支持多线程**（主要瓶颈）
- ❌ **串行调用慢**（占81%时间）
- ❌ **单日同步需 12-15 分钟**

### 当前性能
```
单日同步 (5158只股票):
- baostock API 调用: ~12分钟 (81%)
- 数据处理: ~1.5分钟 (10%)
- 数据库插入: ~1.3分钟 (9%)
总计: ~15分钟
```

---

## 🆚 数据源对比

### 1. AKShare ⭐⭐⭐⭐

#### 基本信息
- **项目**: https://github.com/akfamily/akshare
- **Star**: 10k+
- **维护**: 活跃
- **数据源**: 东方财富、新浪财经等多个公开接口

#### 核心特点
```python
import akshare as ak

# 获取单只股票历史数据
df = ak.stock_zh_a_hist(
    symbol="000001", 
    period="daily",
    start_date="20170301", 
    end_date='20231022',
    adjust=""
)
```

#### 优势
- ✅ **接口丰富**：覆盖股票、基金、期货等
- ✅ **数据源多样**：东方财富、新浪、腾讯等
- ✅ **更新及时**：数据更新快
- ✅ **文档完善**：有详细文档和示例
- ✅ **支持多种数据**：实时行情、财务数据、概念板块等

#### 劣势
- ⚠️ **依赖公开接口**：可能被限流
- ⚠️ **稳定性一般**：接口可能失效
- ⚠️ **无官方支持**：爬虫性质
- ⚠️ **并发限制**：过快请求可能被封IP

#### 性能评估
- **单股查询**: 100-300ms
- **批量查询**: 不支持真正的批量
- **并发能力**: 有限（需要控制频率）
- **预估提升**: **2-3倍**（通过异步并发）

---

### 2. AData ⭐⭐⭐⭐⭐ 推荐

#### 基本信息
- **项目**: https://github.com/1nchaos/adata
- **Star**: 1k+
- **维护**: 活跃
- **数据源**: 多数据源融合（东方财富、同花顺、百度股市通等）

#### 核心特点
```python
import adata

# 获取所有股票代码
codes_df = adata.stock.info.all_code()

# 获取单只股票行情
market_df = adata.stock.market.get_market(
    stock_code='000001',
    k_type=1,  # 日K
    start_date='2021-01-01'
)
```

#### 优势
- ✅ **多数据源融合**：自动切换数据源
- ✅ **高可用性**：动态设置代理
- ✅ **专注A股**：针对A股优化
- ✅ **接口简洁**：易于使用
- ✅ **支持代理**：内置代理池支持
- ✅ **数据完整**：包含概念、板块、财务等

#### 劣势
- ⚠️ **Star较少**：相对小众
- ⚠️ **依赖公开接口**：可能被限流
- ⚠️ **需要代理**：高频请求需要代理池

#### 性能评估
- **单股查询**: 100-200ms
- **批量查询**: 不支持真正的批量
- **并发能力**: 中等（支持代理池）
- **预估提升**: **3-5倍**（通过异步+代理池）

---

## 🎯 优化方案

### 方案 1: 混合使用（推荐）⭐⭐⭐⭐⭐

**策略**: baostock 为主，AData/AKShare 为辅

#### 实施方案
```python
class HybridDataFetcher:
    """混合数据获取器"""
    
    def __init__(self):
        self.baostock = BaostockFetcher()
        self.adata = ADataFetcher()
        self.akshare = AKShareFetcher()
    
    async def fetch_daily_data(self, date_str):
        # 1. 优先使用 AData（异步并发）
        try:
            results = await self.adata.fetch_concurrent(
                stock_codes, 
                date_str,
                max_concurrent=20
            )
            if len(results) > 0.8 * len(stock_codes):
                return results
        except Exception as e:
            logger.warning(f"AData 失败: {e}")
        
        # 2. 回退到 baostock（稳定但慢）
        return self.baostock.fetch_serial(stock_codes, date_str)
```

#### 优势
- ✅ **性能提升**: 3-5倍（正常情况）
- ✅ **稳定性高**: 自动回退
- ✅ **数据完整**: 多源保障

#### 预期性能
```
单日同步 (5158只股票):
- 正常情况: 3-5分钟 (AData并发)
- 回退情况: 12-15分钟 (baostock)
平均: ~5分钟 (提升 3倍)
```

---

### 方案 2: 完全替换为 AData ⭐⭐⭐⭐

**策略**: 使用 AData + 代理池

#### 实施方案
```python
import adata
import asyncio

class ADataAsyncFetcher:
    """AData 异步获取器"""
    
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool
        adata.proxy(is_proxy=True, proxy_url=proxy_pool.get_url())
    
    async def fetch_batch(self, stock_codes, date_str):
        semaphore = asyncio.Semaphore(20)  # 限制并发
        
        async def fetch_one(code):
            async with semaphore:
                return await self._fetch_single(code, date_str)
        
        tasks = [fetch_one(code) for code in stock_codes]
        return await asyncio.gather(*tasks)
```

#### 优势
- ✅ **性能最优**: 5-10倍提升
- ✅ **数据更新快**: 实时性好
- ✅ **功能丰富**: 支持更多数据

#### 劣势
- ⚠️ **需要代理池**: 额外成本
- ⚠️ **稳定性风险**: 接口可能失效
- ⚠️ **维护成本**: 需要监控

#### 预期性能
```
单日同步 (5158只股票):
- 理想情况: 2-3分钟
- 一般情况: 3-5分钟
平均: ~3分钟 (提升 5倍)
```

---

### 方案 3: 分时段使用 ⭐⭐⭐

**策略**: 历史数据用 baostock，实时数据用 AData

#### 实施方案
```python
def sync_strategy(sync_date):
    today = date.today()
    
    if sync_date < today - timedelta(days=7):
        # 历史数据：使用 baostock（稳定）
        return baostock_fetcher.fetch(sync_date)
    else:
        # 近期数据：使用 AData（快速）
        return adata_fetcher.fetch(sync_date)
```

#### 优势
- ✅ **平衡性能和稳定性**
- ✅ **降低风险**
- ✅ **灵活切换**

---

## 📊 性能对比总结

| 方案 | 单日同步 | 提升倍数 | 稳定性 | 成本 | 推荐度 |
|------|---------|---------|--------|------|--------|
| **当前 (baostock)** | 12-15分钟 | 1x | ⭐⭐⭐⭐⭐ | $0 | ⭐⭐⭐ |
| **方案1 (混合)** | 3-5分钟 | 3-5x | ⭐⭐⭐⭐ | $0 | ⭐⭐⭐⭐⭐ |
| **方案2 (AData)** | 2-3分钟 | 5-10x | ⭐⭐⭐ | 代理成本 | ⭐⭐⭐⭐ |
| **方案3 (分时段)** | 5-8分钟 | 2-3x | ⭐⭐⭐⭐ | $0 | ⭐⭐⭐⭐ |

---

## 🚀 推荐实施方案

### 立即实施：方案1（混合使用）⭐⭐⭐⭐⭐

#### 理由
1. **性能提升明显**: 3-5倍
2. **风险可控**: 自动回退
3. **零成本**: 无需代理
4. **易于实施**: 代码改动小

#### 实施步骤

**步骤 1**: 安装依赖
```bash
pip install adata akshare
```

**步骤 2**: 创建混合获取器
```python
# app/services/hybrid_data_fetcher.py
class HybridDataFetcher:
    def __init__(self):
        self.sources = {
            'adata': ADataFetcher(),
            'akshare': AKShareFetcher(),
            'baostock': BaostockFetcher()
        }
    
    async def fetch_with_fallback(self, stock_codes, date_str):
        # 尝试顺序: adata -> akshare -> baostock
        for source_name, fetcher in self.sources.items():
            try:
                results = await fetcher.fetch(stock_codes, date_str)
                if self._validate_results(results):
                    logger.info(f"使用 {source_name} 获取成功")
                    return results
            except Exception as e:
                logger.warning(f"{source_name} 失败: {e}")
        
        raise Exception("所有数据源均失败")
```

**步骤 3**: 集成到现有服务
```python
# 修改 daily_data_sync_service_neon.py
from app.services.hybrid_data_fetcher import HybridDataFetcher

class DailyDataSyncServiceNeon:
    def __init__(self):
        self.fetcher = HybridDataFetcher()
    
    async def sync_daily_data(self, sync_date):
        # 使用混合获取器
        results = await self.fetcher.fetch_with_fallback(
            stock_codes, 
            date_str
        )
```

---

## 📈 预期收益

### 性能提升
```
当前: 12-15分钟/日
优化后: 3-5分钟/日
提升: 3-5倍

1年数据同步:
当前: 49小时
优化后: 10-16小时
节省: 33-39小时
```

### 累计优化效果
```
Supabase: 57分钟/日
    ↓ 57x
当前优化: 1分钟/日
    ↓ 3-5x (数据获取优化)
最终: 12-20秒/日 ⚡⚡⚡
```

---

## ⚠️ 风险评估

### 方案1（混合）风险
- **低风险**: 有 baostock 兜底
- **中收益**: 3-5倍提升
- **易维护**: 代码简单

### 方案2（AData）风险
- **中风险**: 依赖公开接口
- **高收益**: 5-10倍提升
- **需维护**: 监控接口状态

---

## 🎯 结论

### 推荐方案
**方案1（混合使用）** - 最佳性价比

### 实施优先级
1. ✅ **立即**: 实施方案1（混合使用）
2. ⏳ **观察**: 监控稳定性和性能
3. ⏳ **优化**: 根据实际情况调整策略

### 预期效果
- **性能**: 提升 3-5倍
- **稳定性**: 保持高水平
- **成本**: $0
- **维护**: 低

---

**分析完成时间**: 2025-10-17 08:25  
**推荐方案**: 混合使用（方案1）  
**预期提升**: 3-5倍  
**风险等级**: 低
