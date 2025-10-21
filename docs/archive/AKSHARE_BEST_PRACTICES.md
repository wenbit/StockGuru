# 🎯 借鉴 AKShare 的最佳实践

## 📋 AKShare 核心设计分析

通过深入分析 AKShare 源码（10k+ stars），发现了 **6个优秀的设计模式**：

---

## 🏗️ 核心设计模式

### 1. 分层异常处理体系 ⭐⭐⭐⭐⭐

#### 设计思想
```python
# exceptions.py
class AkshareException(Exception):
    """基础异常类"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class APIError(AkshareException):
    """API 请求失败"""
    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(f"API Error: {message} (Status code: {status_code})")

class DataParsingError(AkshareException):
    """数据解析失败"""
    pass

class NetworkError(AkshareException):
    """网络相关问题"""
    pass

class RateLimitError(AkshareException):
    """API 频率限制"""
    pass

class InvalidParameterError(AkshareException):
    """无效参数"""
    pass
```

#### 核心优势
- ✅ **分类清晰**: 不同类型的错误有专门的异常类
- ✅ **易于处理**: 可以针对性捕获和处理
- ✅ **信息丰富**: 包含状态码等详细信息
- ✅ **继承体系**: 统一的基类便于统一处理

---

### 2. 指数退避重试机制 ⭐⭐⭐⭐⭐

#### 设计思想
```python
def make_request_with_retry_json(
    url, params=None, headers=None, proxies=None, 
    max_retries=3, retry_delay=1
):
    """
    发送 HTTP GET 请求，支持重试机制和代理设置
    """
    if proxies is None:
        proxies = config.proxies  # 全局代理配置
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, params=params, headers=headers, proxies=proxies
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data:
                        raise DataParsingError("Empty response data")
                    return data
                except ValueError:
                    raise DataParsingError("Failed to parse JSON response")
            
            elif response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded")
            
            else:
                raise APIError(f"API request failed. Status code: {response.status_code}")
        
        except (RequestException, RateLimitError, APIError, DataParsingError) as e:
            if attempt == max_retries - 1:
                # 最后一次尝试，抛出异常
                if isinstance(e, RateLimitError):
                    raise
                elif isinstance(e, (APIError, DataParsingError)):
                    raise
                else:
                    raise NetworkError(
                        f"Failed to connect after {max_retries} attempts: {str(e)}"
                    )
            
            # 指数退避：每次重试等待时间翻倍
            time.sleep(retry_delay)
            retry_delay *= 2  # 1s -> 2s -> 4s
    
    raise NetworkError(f"Failed to connect after {max_retries} attempts")
```

#### 核心优势
- ✅ **指数退避**: 避免频繁重试导致封IP
- ✅ **智能重试**: 区分可重试和不可重试的错误
- ✅ **代理集成**: 自动使用全局代理配置
- ✅ **数据验证**: 检查返回数据是否为空

---

### 3. 上下文管理器代理 ⭐⭐⭐⭐⭐

#### 设计思想
```python
# context.py
class AkshareConfig:
    """全局配置单例"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.proxies = None
        return cls._instance
    
    @classmethod
    def set_proxies(cls, proxies):
        cls().proxies = proxies
    
    @classmethod
    def get_proxies(cls):
        return cls().proxies


class ProxyContext:
    """代理上下文管理器"""
    def __init__(self, proxies):
        self.proxies = proxies
        self.old_proxies = None
    
    def __enter__(self):
        self.old_proxies = config.get_proxies()
        config.set_proxies(self.proxies)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        config.set_proxies(self.old_proxies)
        return False  # 不处理异常


# 使用示例
with ProxyContext({'http': 'http://proxy:8080'}):
    # 在这个代码块中使用代理
    data = fetch_data()
# 代码块结束后自动恢复原代理配置
```

#### 核心优势
- ✅ **临时代理**: 支持临时切换代理
- ✅ **自动恢复**: 退出时自动恢复原配置
- ✅ **优雅设计**: 使用 with 语句，代码清晰
- ✅ **线程安全**: 单例模式保证全局唯一

---

### 4. 智能分页获取 ⭐⭐⭐⭐⭐

#### 设计思想
```python
def fetch_paginated_data(url: str, base_params: Dict, timeout: int = 15):
    """
    东方财富-分页获取数据并合并结果
    """
    # 1. 复制参数以避免修改原始参数
    params = base_params.copy()
    
    # 2. 获取第一页数据，用于确定分页信息
    r = requests.get(url, params=params, timeout=timeout)
    data_json = r.json()
    
    # 3. 计算分页信息
    per_page_num = len(data_json["data"]["diff"])
    total_page = math.ceil(data_json["data"]["total"] / per_page_num)
    
    # 4. 存储所有页面数据
    temp_list = []
    temp_list.append(pd.DataFrame(data_json["data"]["diff"]))
    
    # 5. 获取进度条（自动适配环境）
    tqdm = get_tqdm()
    
    # 6. 获取剩余页面数据
    for page in tqdm(range(2, total_page + 1), leave=False):
        params.update({"pn": page})
        r = requests.get(url, params=params, timeout=timeout)
        data_json = r.json()
        inner_temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_list.append(inner_temp_df)
    
    # 7. 合并所有数据
    temp_df = pd.concat(temp_list, ignore_index=True)
    temp_df["f3"] = pd.to_numeric(temp_df["f3"], errors="coerce")
    temp_df.sort_values(by=["f3"], ascending=False, inplace=True, ignore_index=True)
    temp_df.reset_index(inplace=True)
    temp_df["index"] = temp_df["index"].astype(int) + 1
    
    return temp_df
```

#### 核心优势
- ✅ **自动分页**: 自动计算总页数
- ✅ **进度显示**: 显示获取进度
- ✅ **数据合并**: 自动合并所有页数据
- ✅ **参数隔离**: 不修改原始参数

---

### 5. 环境自适应进度条 ⭐⭐⭐⭐

#### 设计思想
```python
def get_tqdm(enable: bool = True):
    """
    返回适用于当前环境的 tqdm 对象
    """
    if not enable:
        # 如果进度条被禁用，返回一个不显示进度条的对象
        return lambda iterable, *args, **kwargs: iterable
    
    try:
        # 尝试检查是否在 jupyter notebook 环境中
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            from tqdm.notebook import tqdm  # Jupyter 专用
        else:
            from tqdm import tqdm  # 标准版本
    except (NameError, ImportError):
        # 如果不在 Jupyter 环境中，就使用标准 tqdm
        from tqdm import tqdm
    
    return tqdm
```

#### 核心优势
- ✅ **环境检测**: 自动检测 Jupyter 环境
- ✅ **自适应**: 使用合适的进度条版本
- ✅ **可禁用**: 支持禁用进度条
- ✅ **优雅降级**: 检测失败时使用标准版本

---

### 6. 统一数据清洗 ⭐⭐⭐⭐

#### 设计思想
```python
def stock_zh_a_spot_em() -> pd.DataFrame:
    """东方财富网-沪深京 A 股-实时行情"""
    # 1. 获取数据
    temp_df = fetch_paginated_data(url, params)
    
    # 2. 设置列名（中文列名，易于理解）
    temp_df.columns = [
        "序号", "代码", "名称", "最新价", "涨跌幅", "涨跌额",
        "成交量", "成交额", "振幅", "最高", "最低", "今开", "昨收",
        "量比", "换手率", "市盈率-动态", "市净率", "总市值", 
        "流通市值", "涨速", "5分钟涨跌", "60日涨跌幅", "年初至今涨跌幅"
    ]
    
    # 3. 统一数据类型转换（使用 errors="coerce" 处理异常值）
    numeric_cols = [
        "最新价", "涨跌幅", "涨跌额", "成交量", "成交额", "振幅",
        "最高", "最低", "今开", "昨收", "量比", "换手率",
        "市盈率-动态", "市净率", "总市值", "流通市值", "涨速",
        "5分钟涨跌", "60日涨跌幅", "年初至今涨跌幅"
    ]
    for col in numeric_cols:
        temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce")
    
    # 4. 选择需要的列（明确的列顺序）
    temp_df = temp_df[[
        "序号", "代码", "名称", "最新价", "涨跌幅", "涨跌额",
        "成交量", "成交额", "振幅", "最高", "最低", "今开", "昨收",
        "量比", "换手率", "市盈率-动态", "市净率", "总市值",
        "流通市值", "涨速", "5分钟涨跌", "60日涨跌幅", "年初至今涨跌幅"
    ]]
    
    return temp_df
```

#### 核心优势
- ✅ **中文列名**: 易于理解和使用
- ✅ **类型安全**: 统一转换数据类型
- ✅ **异常处理**: errors="coerce" 处理异常值
- ✅ **列顺序**: 明确的列顺序

---

## 🚀 应用到 StockGuru

### 实现方案

#### 1. 分层异常处理

```python
# app/exceptions.py

class StockGuruException(Exception):
    """基础异常类"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DataSourceError(StockGuruException):
    """数据源错误"""
    def __init__(self, message, source_name=None):
        self.source_name = source_name
        super().__init__(f"[{source_name}] {message}" if source_name else message)


class DataValidationError(StockGuruException):
    """数据验证错误"""
    pass


class RateLimitError(StockGuruException):
    """频率限制错误"""
    def __init__(self, message, retry_after=None):
        self.retry_after = retry_after
        super().__init__(message)


class DatabaseError(StockGuruException):
    """数据库错误"""
    pass
```

---

#### 2. 指数退避请求封装

```python
# app/services/smart_request.py

import time
import requests
from typing import Optional, Dict, Any
import logging

from app.exceptions import (
    DataSourceError, RateLimitError, DataValidationError
)

logger = logging.getLogger(__name__)


class SmartRequest:
    """智能请求封装（借鉴 AKShare）"""
    
    @staticmethod
    def get_json(
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        proxies: Optional[Dict] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 15
    ) -> Any:
        """
        发送 GET 请求并返回 JSON
        
        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            proxies: 代理配置
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            timeout: 超时时间
        
        Returns:
            JSON 数据
        
        Raises:
            DataSourceError: 数据源错误
            RateLimitError: 频率限制
            DataValidationError: 数据验证失败
        """
        current_delay = retry_delay
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout
                )
                
                # 成功
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if not data:
                            raise DataValidationError("Empty response data")
                        return data
                    except ValueError as e:
                        raise DataValidationError(f"Failed to parse JSON: {e}")
                
                # 频率限制
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', 60)
                    raise RateLimitError(
                        f"Rate limit exceeded",
                        retry_after=int(retry_after)
                    )
                
                # 其他错误
                else:
                    raise DataSourceError(
                        f"Request failed with status {response.status_code}"
                    )
            
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            
            except (RateLimitError, DataValidationError, DataSourceError) as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Error (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 最后一次尝试
            if attempt == max_retries - 1:
                raise DataSourceError(
                    f"Failed after {max_retries} attempts"
                )
            
            # 指数退避
            logger.info(f"Retrying in {current_delay}s...")
            time.sleep(current_delay)
            current_delay *= 2  # 指数增长
        
        raise DataSourceError(f"Failed after {max_retries} attempts")
```

---

#### 3. 代理上下文管理器

```python
# app/services/proxy_context.py

from contextlib import contextmanager
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class GlobalConfig:
    """全局配置（单例）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.proxies = None
        return cls._instance
    
    @classmethod
    def set_proxies(cls, proxies: Optional[Dict]):
        cls().proxies = proxies
        logger.info(f"Global proxies set: {proxies}")
    
    @classmethod
    def get_proxies(cls) -> Optional[Dict]:
        return cls().proxies


@contextmanager
def use_proxy(proxies: Dict):
    """
    临时使用代理的上下文管理器
    
    Usage:
        with use_proxy({'http': 'http://proxy:8080'}):
            data = fetch_data()  # 使用代理
        # 自动恢复原配置
    """
    config = GlobalConfig()
    old_proxies = config.get_proxies()
    
    try:
        config.set_proxies(proxies)
        yield
    finally:
        config.set_proxies(old_proxies)
```

---

#### 4. 智能分页获取

```python
# app/services/paginated_fetcher.py

import math
from typing import Dict, List, Callable, Optional
import pandas as pd
from tqdm import tqdm
import logging

from app.services.smart_request import SmartRequest

logger = logging.getLogger(__name__)


class PaginatedFetcher:
    """智能分页数据获取器"""
    
    @staticmethod
    def fetch_all_pages(
        url: str,
        base_params: Dict,
        page_param: str = 'page',
        page_size_param: str = 'page_size',
        data_extractor: Optional[Callable] = None,
        show_progress: bool = True
    ) -> pd.DataFrame:
        """
        自动分页获取所有数据
        
        Args:
            url: 请求URL
            base_params: 基础参数
            page_param: 页码参数名
            page_size_param: 每页大小参数名
            data_extractor: 数据提取函数
            show_progress: 是否显示进度条
        
        Returns:
            合并后的 DataFrame
        """
        # 1. 复制参数
        params = base_params.copy()
        
        # 2. 获取第一页
        first_page = SmartRequest.get_json(url, params=params)
        
        # 3. 提取数据
        if data_extractor:
            total = data_extractor(first_page, 'total')
            data_list = data_extractor(first_page, 'data')
        else:
            total = first_page.get('total', 0)
            data_list = first_page.get('data', [])
        
        # 4. 计算分页
        page_size = params.get(page_size_param, len(data_list))
        total_pages = math.ceil(total / page_size) if page_size > 0 else 1
        
        logger.info(f"Total records: {total}, Pages: {total_pages}")
        
        # 5. 存储数据
        all_data = [pd.DataFrame(data_list)]
        
        # 6. 获取剩余页
        page_range = range(2, total_pages + 1)
        if show_progress:
            page_range = tqdm(page_range, desc="Fetching pages")
        
        for page in page_range:
            params[page_param] = page
            page_data = SmartRequest.get_json(url, params=params)
            
            if data_extractor:
                data_list = data_extractor(page_data, 'data')
            else:
                data_list = page_data.get('data', [])
            
            if data_list:
                all_data.append(pd.DataFrame(data_list))
        
        # 7. 合并数据
        if all_data:
            result_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Fetched {len(result_df)} records")
            return result_df
        
        return pd.DataFrame()
```

---

## 📊 预期效果

### 性能提升

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| 错误处理 | 基础 | **分层** | ✅ |
| 重试机制 | 固定延迟 | **指数退避** | ✅ |
| 代理管理 | 无 | **上下文管理** | ✅ |
| 分页获取 | 手动 | **自动** | ✅ |
| 进度显示 | 无 | **自适应** | ✅ |

### 代码质量提升

- ✅ **异常处理**: 更精确的错误分类
- ✅ **重试策略**: 智能的指数退避
- ✅ **代理支持**: 灵活的代理切换
- ✅ **用户体验**: 进度条显示
- ✅ **代码复用**: 通用的工具函数

---

## 🎯 实施建议

### 立即实施
1. ✅ 分层异常处理体系
2. ✅ 指数退避重试机制
3. ✅ 代理上下文管理器

### 中期实施
4. ⏳ 智能分页获取
5. ⏳ 环境自适应进度条

---

## 💡 核心价值

### AKShare vs AData 对比

| 特性 | AKShare | AData |
|------|---------|-------|
| 异常处理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 重试机制 | ⭐⭐⭐⭐⭐ (指数退避) | ⭐⭐⭐⭐ |
| 代理管理 | ⭐⭐⭐⭐⭐ (上下文) | ⭐⭐⭐⭐ (全局) |
| 分页获取 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 进度显示 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 数据清洗 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 综合借鉴

**最佳方案**: 结合两者优势
- **AData**: 多数据源融合、模板方法模式
- **AKShare**: 异常处理、重试机制、分页获取

---

**分析完成时间**: 2025-10-17 08:35  
**核心借鉴**: 6个设计模式  
**推荐实施**: 分层异常 + 指数退避 + 代理上下文
