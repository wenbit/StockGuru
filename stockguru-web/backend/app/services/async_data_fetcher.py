"""
异步数据获取服务
使用 asyncio 和 aiohttp 实现并发请求，提升性能
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import date

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.warning("aiohttp 未安装，异步功能将被禁用")

logger = logging.getLogger(__name__)


class AsyncDataFetcher:
    """异步数据获取器"""
    
    def __init__(self, max_concurrent: int = 10):
        """
        初始化
        
        Args:
            max_concurrent: 最大并发数
        """
        self.logger = logging.getLogger(__name__)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.enabled = AIOHTTP_AVAILABLE
        
        if not self.enabled:
            self.logger.warning("异步功能已禁用")
    
    async def fetch_stock_data(self, session: aiohttp.ClientSession, 
                               stock_code: str, date_str: str) -> Optional[Dict]:
        """
        异步获取单只股票数据
        
        Args:
            session: aiohttp 会话
            stock_code: 股票代码
            date_str: 日期字符串
            
        Returns:
            股票数据字典
        """
        async with self.semaphore:  # 限制并发数
            try:
                # 这里需要替换为实际的 API 端点
                url = f"https://api.example.com/stock/{stock_code}?date={date_str}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_stock_data(stock_code, data)
                    else:
                        self.logger.warning(f"获取失败 {stock_code}: HTTP {response.status}")
                        return None
                        
            except asyncio.TimeoutError:
                self.logger.error(f"超时 {stock_code}")
                return None
            except Exception as e:
                self.logger.error(f"获取失败 {stock_code}: {e}")
                return None
    
    async def fetch_multiple_stocks(self, stock_codes: List[str], 
                                    date_str: str) -> List[Dict]:
        """
        异步获取多只股票数据
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            
        Returns:
            股票数据列表
        """
        if not self.enabled:
            self.logger.error("异步功能未启用")
            return []
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.fetch_stock_data(session, code, date_str)
                for code in stock_codes
            ]
            
            # 并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤掉失败的结果
            valid_results = [
                r for r in results 
                if r is not None and not isinstance(r, Exception)
            ]
            
            self.logger.info(f"成功获取: {len(valid_results)}/{len(stock_codes)}")
            return valid_results
    
    def _process_stock_data(self, stock_code: str, raw_data: Dict) -> Dict:
        """
        处理原始数据
        
        Args:
            stock_code: 股票代码
            raw_data: 原始数据
            
        Returns:
            处理后的数据
        """
        # 根据实际 API 返回格式处理
        return {
            'stock_code': stock_code,
            'stock_name': raw_data.get('name', ''),
            'trade_date': raw_data.get('date', ''),
            'open_price': float(raw_data.get('open', 0)),
            'close_price': float(raw_data.get('close', 0)),
            'high_price': float(raw_data.get('high', 0)),
            'low_price': float(raw_data.get('low', 0)),
            'volume': int(raw_data.get('volume', 0)),
            'amount': float(raw_data.get('amount', 0)),
            'change_pct': float(raw_data.get('change_pct', 0)),
            'turnover_rate': float(raw_data.get('turnover_rate', 0))
        }
    
    async def fetch_with_retry(self, session: aiohttp.ClientSession,
                               stock_code: str, date_str: str,
                               max_retries: int = 3) -> Optional[Dict]:
        """
        带重试的异步获取
        
        Args:
            session: aiohttp 会话
            stock_code: 股票代码
            date_str: 日期字符串
            max_retries: 最大重试次数
            
        Returns:
            股票数据字典
        """
        for attempt in range(max_retries):
            result = await self.fetch_stock_data(session, stock_code, date_str)
            if result is not None:
                return result
            
            if attempt < max_retries - 1:
                # 指数退避
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        return None
    
    async def fetch_batch(self, stock_codes: List[str], date_str: str,
                         batch_size: int = 100) -> List[Dict]:
        """
        分批异步获取（避免一次性请求过多）
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            batch_size: 每批数量
            
        Returns:
            股票数据列表
        """
        all_results = []
        
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i+batch_size]
            self.logger.info(f"处理批次 {i//batch_size + 1}: {len(batch)} 只股票")
            
            results = await self.fetch_multiple_stocks(batch, date_str)
            all_results.extend(results)
            
            # 批次间短暂延迟，避免过载
            if i + batch_size < len(stock_codes):
                await asyncio.sleep(0.5)
        
        return all_results


class AsyncBatchProcessor:
    """异步批处理器"""
    
    def __init__(self, max_workers: int = 4):
        """
        初始化
        
        Args:
            max_workers: 最大工作线程数
        """
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
    
    async def process_items(self, items: List[any], 
                           process_func, *args, **kwargs) -> List[any]:
        """
        异步处理多个项目
        
        Args:
            items: 待处理项目列表
            process_func: 处理函数（可以是同步或异步）
            
        Returns:
            处理结果列表
        """
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_with_semaphore(item):
            async with semaphore:
                if asyncio.iscoroutinefunction(process_func):
                    return await process_func(item, *args, **kwargs)
                else:
                    # 同步函数在线程池中执行
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, process_func, item, *args, **kwargs
                    )
        
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常
        valid_results = [
            r for r in results 
            if not isinstance(r, Exception)
        ]
        
        return valid_results


def run_async(coro):
    """
    运行异步函数（兼容同步调用）
    
    Args:
        coro: 协程对象
        
    Returns:
        执行结果
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


# 使用示例
async def example_usage():
    """使用示例"""
    from datetime import date, timedelta
    
    fetcher = AsyncDataFetcher(max_concurrent=10)
    
    stock_codes = ['000001', '000002', '600000', '600001']
    date_str = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')  # 昨天
    
    # 异步获取数据
    results = await fetcher.fetch_multiple_stocks(stock_codes, date_str)
    
    print(f"获取到 {len(results)} 条数据")
    return results


if __name__ == '__main__':
    # 测试
    results = run_async(example_usage())
    print(results)
