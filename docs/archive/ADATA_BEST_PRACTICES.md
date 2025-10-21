# 🎯 借鉴 AData 的最佳实践

## 📋 AData 核心设计分析

通过深入分析 AData 源码，发现以下优秀设计模式：

---

## 🏗️ 核心设计模式

### 1. 多数据源融合架构 ⭐⭐⭐⭐⭐

#### 设计思想
```python
class StockMarket:
    def __init__(self):
        # 初始化多个数据源
        self.sina_market = StockMarketSina()
        self.qq_market = StockMarketQQ()
        self.baidu_market = StockMarketBaiDu()
        self.east_market = StockMarketEast()
    
    def get_market(self, stock_code):
        # 主数据源：东方财富
        df = self.east_market.get_market(stock_code)
        return df
    
    def get_market_min(self, stock_code):
        # 主数据源
        df = self.east_market.get_market_min(stock_code)
        # 失败时自动切换
        if df.empty:
            return self.baidu_market.get_market_min(stock_code)
        return df
```

#### 核心优势
- ✅ **高可用性**: 一个数据源失败自动切换
- ✅ **灵活性**: 易于添加新数据源
- ✅ **可维护性**: 每个数据源独立实现

---

### 2. 模板方法模式 ⭐⭐⭐⭐⭐

#### 设计思想
```python
class StockMarketTemplate:
    """统一的接口定义"""
    _MARKET_COLUMNS = ['trade_time', 'open', 'close', ...]
    
    def get_market(self, stock_code, start_date, end_date):
        """子类必须实现"""
        pass
    
    def get_market_min(self, stock_code):
        """子类必须实现"""
        pass
```

#### 核心优势
- ✅ **统一接口**: 所有数据源返回相同格式
- ✅ **易于扩展**: 新增数据源只需继承模板
- ✅ **类型安全**: 明确的列定义

---

### 3. 全局代理管理 ⭐⭐⭐⭐⭐

#### 设计思想
```python
class SunProxy:
    """单例模式的全局代理管理器"""
    _data = {}
    _instance_lock = threading.Lock()
    
    @classmethod
    def set(cls, key, value):
        cls._data[key] = value
    
    @classmethod
    def get(cls, key):
        return cls._data.get(key)

# 使用
adata.proxy(is_proxy=True, ip='192.168.1.1:8080')
```

#### 核心优势
- ✅ **全局配置**: 一次设置全局生效
- ✅ **线程安全**: 使用锁保护
- ✅ **易于使用**: 简单的 API

---

### 4. 智能请求封装 ⭐⭐⭐⭐⭐

#### 设计思想
```python
class SunRequests:
    def request(self, method='get', url=None, 
                times=3,              # 重试次数
                retry_wait_time=1588, # 重试等待
                wait_time=None,       # 请求间隔
                proxies=None, **kwargs):
        
        # 1. 获取全局代理配置
        proxies = self.__get_proxies(proxies)
        
        # 2. 重试机制
        for i in range(times):
            if wait_time:
                time.sleep(wait_time / 1000)
            
            res = requests.request(
                method=method, url=url, 
                proxies=proxies, **kwargs
            )
            
            if res.status_code in (200, 404):
                return res
            
            time.sleep(retry_wait_time / 1000)
        
        return res
```

#### 核心优势
- ✅ **自动重试**: 失败自动重试
- ✅ **频率控制**: 防止请求过快
- ✅ **代理集成**: 自动使用全局代理

---

### 5. 装饰器异常处理 ⭐⭐⭐⭐

#### 设计思想
```python
def handler_null(func):
    """统一的异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return pd.DataFrame()  # 返回空 DataFrame
    return wrapper

@handler_null
def get_market(self, stock_code):
    # 业务逻辑
    pass
```

#### 核心优势
- ✅ **统一处理**: 所有方法统一异常处理
- ✅ **优雅降级**: 失败返回空数据而不是崩溃
- ✅ **代码简洁**: 减少重复的 try-catch

---

## 🚀 应用到 StockGuru

### 方案 1: 多数据源融合架构

#### 实现代码
```python
# app/services/multi_source_data_fetcher.py

from abc import ABC, abstractmethod
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataSourceTemplate(ABC):
    """数据源模板基类"""
    
    COLUMNS = ['stock_code', 'stock_name', 'trade_date',
               'open_price', 'close_price', 'high_price', 'low_price',
               'volume', 'amount', 'change_pct', 'turnover_rate']
    
    @abstractmethod
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """获取单只股票日线数据"""
        pass
    
    @abstractmethod
    def fetch_batch_data(self, stock_codes: list, date_str: str) -> pd.DataFrame:
        """批量获取股票数据"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """数据源名称"""
        pass


class BaostockSource(DataSourceTemplate):
    """Baostock 数据源"""
    
    def __init__(self):
        import baostock as bs
        self.bs = bs
        self.logged_in = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        if not self.logged_in:
            self.bs.login()
            self.logged_in = True
        
        # 实现 baostock 获取逻辑
        rs = self.bs.query_history_k_data_plus(
            f"sh.{stock_code}" if stock_code.startswith('6') else f"sz.{stock_code}",
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=date_str,
            end_date=date_str
        )
        
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data, columns=rs.fields)
        # 数据转换...
        return df
    
    def fetch_batch_data(self, stock_codes: list, date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            df = self.fetch_daily_data(code, date_str)
            if not df.empty:
                results.append(df)
        return pd.concat(results) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "baostock"


class ADataSource(DataSourceTemplate):
    """AData 数据源"""
    
    def __init__(self):
        import adata
        self.adata = adata
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        try:
            df = self.adata.stock.market.get_market(
                stock_code=stock_code,
                k_type=1,
                start_date=date_str,
                end_date=date_str
            )
            # 数据转换...
            return df
        except Exception as e:
            logger.error(f"AData 获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_batch_data(self, stock_codes: list, date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            df = self.fetch_daily_data(code, date_str)
            if not df.empty:
                results.append(df)
        return pd.concat(results) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "adata"


class AKShareSource(DataSourceTemplate):
    """AKShare 数据源"""
    
    def __init__(self):
        import akshare as ak
        self.ak = ak
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        try:
            df = self.ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=date_str.replace('-', ''),
                end_date=date_str.replace('-', ''),
                adjust=""
            )
            # 数据转换...
            return df
        except Exception as e:
            logger.error(f"AKShare 获取失败: {e}")
            return pd.DataFrame()
    
    def fetch_batch_data(self, stock_codes: list, date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            df = self.fetch_daily_data(code, date_str)
            if not df.empty:
                results.append(df)
        return pd.concat(results) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "akshare"


class MultiSourceDataFetcher:
    """多数据源融合获取器"""
    
    def __init__(self):
        self.sources = [
            ADataSource(),      # 优先级1: AData（快速）
            AKShareSource(),    # 优先级2: AKShare（备选）
            BaostockSource()    # 优先级3: Baostock（兜底）
        ]
        self.logger = logging.getLogger(__name__)
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """
        多数据源获取单只股票数据
        自动切换数据源直到成功
        """
        for source in self.sources:
            try:
                self.logger.debug(f"尝试使用 {source.get_source_name()} 获取 {stock_code}")
                df = source.fetch_daily_data(stock_code, date_str)
                
                if not df.empty:
                    self.logger.info(f"✅ {source.get_source_name()} 获取成功: {stock_code}")
                    return df
                
            except Exception as e:
                self.logger.warning(f"❌ {source.get_source_name()} 失败: {e}")
                continue
        
        self.logger.error(f"所有数据源均失败: {stock_code}")
        return pd.DataFrame()
    
    def fetch_batch_data(self, stock_codes: list, date_str: str) -> pd.DataFrame:
        """
        批量获取股票数据
        优先使用第一个数据源，失败则逐个切换
        """
        for source in self.sources:
            try:
                self.logger.info(f"使用 {source.get_source_name()} 批量获取 {len(stock_codes)} 只股票")
                df = source.fetch_batch_data(stock_codes, date_str)
                
                # 验证数据完整性（至少获取到 80%）
                if len(df) >= len(stock_codes) * 0.8:
                    self.logger.info(f"✅ {source.get_source_name()} 批量获取成功: {len(df)}/{len(stock_codes)}")
                    return df
                
            except Exception as e:
                self.logger.warning(f"❌ {source.get_source_name()} 批量获取失败: {e}")
                continue
        
        self.logger.error("所有数据源批量获取均失败")
        return pd.DataFrame()
```

---

### 方案 2: 全局代理管理

#### 实现代码
```python
# app/services/proxy_manager.py

import threading
import requests
import logging

logger = logging.getLogger(__name__)


class ProxyManager:
    """全局代理管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    _config = {
        'enabled': False,
        'proxy_ip': None,
        'proxy_url': None,
        'proxies': {}
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def enable(cls, proxy_ip: str = None, proxy_url: str = None):
        """
        启用代理
        
        Args:
            proxy_ip: 代理IP，格式: '192.168.1.1:8080'
            proxy_url: 代理池URL，动态获取IP
        """
        cls._config['enabled'] = True
        cls._config['proxy_ip'] = proxy_ip
        cls._config['proxy_url'] = proxy_url
        
        if proxy_ip:
            cls._config['proxies'] = {
                'http': f'http://{proxy_ip}',
                'https': f'http://{proxy_ip}'
            }
        
        logger.info(f"代理已启用: {proxy_ip or '动态获取'}")
    
    @classmethod
    def disable(cls):
        """禁用代理"""
        cls._config['enabled'] = False
        cls._config['proxies'] = {}
        logger.info("代理已禁用")
    
    @classmethod
    def get_proxies(cls) -> dict:
        """获取当前代理配置"""
        if not cls._config['enabled']:
            return {}
        
        # 如果有固定IP，直接返回
        if cls._config['proxy_ip']:
            return cls._config['proxies']
        
        # 如果配置了代理池URL，动态获取
        if cls._config['proxy_url']:
            try:
                ip = requests.get(cls._config['proxy_url'], timeout=5).text.strip()
                return {
                    'http': f'http://{ip}',
                    'https': f'http://{ip}'
                }
            except Exception as e:
                logger.error(f"获取代理IP失败: {e}")
                return {}
        
        return {}
    
    @classmethod
    def test_proxy(cls) -> bool:
        """测试代理是否可用"""
        proxies = cls.get_proxies()
        if not proxies:
            return True  # 无代理时返回True
        
        try:
            response = requests.get(
                'http://www.baidu.com',
                proxies=proxies,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"代理测试失败: {e}")
            return False


# 全局实例
proxy_manager = ProxyManager()
```

---

### 方案 3: 智能请求封装

#### 实现代码
```python
# app/services/smart_requests.py

import time
import requests
from typing import Optional
import logging

from app.services.proxy_manager import proxy_manager

logger = logging.getLogger(__name__)


class SmartRequests:
    """智能请求封装"""
    
    @staticmethod
    def request(
        method: str = 'GET',
        url: str = None,
        max_retries: int = 3,
        retry_delay: float = 1.5,
        wait_before: float = 0,
        timeout: int = 10,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        智能HTTP请求
        
        Args:
            method: 请求方法
            url: 请求URL
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            wait_before: 请求前等待时间（秒）
            timeout: 超时时间
            **kwargs: requests 其他参数
        
        Returns:
            Response 对象或 None
        """
        # 请求前等待（防止频率过快）
        if wait_before > 0:
            time.sleep(wait_before)
        
        # 获取全局代理配置
        if 'proxies' not in kwargs:
            kwargs['proxies'] = proxy_manager.get_proxies()
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = timeout
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, **kwargs)
                
                # 成功状态码
                if response.status_code in (200, 404):
                    return response
                
                # 其他状态码，记录并重试
                logger.warning(
                    f"请求失败 (尝试 {attempt + 1}/{max_retries}): "
                    f"状态码 {response.status_code}"
                )
                
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{max_retries})")
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            except Exception as e:
                logger.error(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            
            # 最后一次尝试失败
            if attempt == max_retries - 1:
                logger.error(f"请求最终失败: {url}")
                return None
            
            # 等待后重试
            time.sleep(retry_delay)
        
        return None


# 全局实例
smart_requests = SmartRequests()
```

---

## 📊 预期效果

### 性能提升

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| 单日同步 | 12-15分钟 | **3-5分钟** | **3-5x** |
| 数据可用性 | 95% | **99%+** | **4%+** |
| 失败重试 | 手动 | **自动** | ✅ |
| 代理支持 | 无 | **有** | ✅ |

### 稳定性提升

- ✅ **多数据源**: 一个失败自动切换
- ✅ **自动重试**: 网络波动自动恢复
- ✅ **代理支持**: 突破频率限制
- ✅ **优雅降级**: 失败不崩溃

---

## 🎯 实施建议

### 立即实施
1. ✅ 多数据源融合架构
2. ✅ 智能请求封装
3. ✅ 全局代理管理

### 中期实施
4. ⏳ 异步并发优化
5. ⏳ 数据源健康监控

---

**分析完成时间**: 2025-10-17 08:30  
**核心借鉴**: 5个设计模式  
**预期提升**: 3-5倍性能 + 高可用性
