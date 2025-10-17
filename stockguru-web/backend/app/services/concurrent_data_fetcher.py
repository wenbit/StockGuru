"""
并发数据获取器
使用线程池实现并发获取，预期提速 5-7倍
"""

import logging
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import pandas as pd

from app.services.enhanced_data_fetcher import robust_fetcher

logger = logging.getLogger(__name__)


class ConcurrentDataFetcher:
    """
    并发数据获取器
    使用线程池并发获取多只股票数据
    """
    
    def __init__(self, max_workers: int = 10):
        """
        初始化并发获取器
        
        Args:
            max_workers: 最大并发线程数（默认10）
        """
        self.max_workers = max_workers
        self.fetcher = robust_fetcher
        logger.info(f"✅ Concurrent fetcher initialized with {max_workers} workers")
    
    def fetch_single(self, stock_code: str, date_str: str) -> Dict:
        """
        获取单只股票数据（供线程池调用）
        
        Args:
            stock_code: 股票代码
            date_str: 日期字符串
        
        Returns:
            包含股票代码和数据的字典
        """
        try:
            df = self.fetcher.fetch_daily_data(stock_code, date_str)
            return {
                'code': stock_code,
                'success': not df.empty,
                'data': df
            }
        except Exception as e:
            logger.error(f"Failed to fetch {stock_code}: {e}")
            return {
                'code': stock_code,
                'success': False,
                'data': pd.DataFrame(),
                'error': str(e)
            }
    
    def fetch_batch_concurrent(
        self,
        stock_codes: List[str],
        date_str: str,
        progress_callback: Optional[callable] = None
    ) -> List[pd.DataFrame]:
        """
        并发批量获取股票数据
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            progress_callback: 进度回调函数 callback(current, total, code)
        
        Returns:
            DataFrame 列表
        """
        results = []
        success_count = 0
        failed_count = 0
        
        logger.info(f"🚀 Starting concurrent fetch for {len(stock_codes)} stocks with {self.max_workers} workers")
        
        start_time = time.time()
        
        # 使用线程池并发获取
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_code = {
                executor.submit(self.fetch_single, code, date_str): code
                for code in stock_codes
            }
            
            # 处理完成的任务
            for i, future in enumerate(as_completed(future_to_code), 1):
                result = future.result()
                
                if result['success']:
                    results.append(result['data'])
                    success_count += 1
                else:
                    failed_count += 1
                
                # 进度回调
                if progress_callback:
                    progress_callback(i, len(stock_codes), result['code'])
                
                # 每100只输出一次进度
                if i % 100 == 0 or i == len(stock_codes):
                    elapsed = time.time() - start_time
                    speed = i / elapsed if elapsed > 0 else 0
                    eta = (len(stock_codes) - i) / speed if speed > 0 else 0
                    logger.info(
                        f"Progress: {i}/{len(stock_codes)} "
                        f"({i/len(stock_codes)*100:.1f}%) "
                        f"Speed: {speed:.1f} stocks/s "
                        f"ETA: {eta:.0f}s"
                    )
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"✅ Concurrent fetch completed: "
            f"{success_count} success, {failed_count} failed "
            f"in {elapsed:.2f}s ({len(stock_codes)/elapsed:.1f} stocks/s)"
        )
        
        return results
    
    def fetch_and_prepare_for_db(
        self,
        stock_codes: List[str],
        date_str: str,
        progress_callback: Optional[callable] = None
    ) -> List[tuple]:
        """
        并发获取数据并准备数据库插入格式
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            progress_callback: 进度回调函数
        
        Returns:
            准备好的数据库插入元组列表
        """
        logger.info(f"🔄 Fetching and preparing data for {len(stock_codes)} stocks")
        
        # 并发获取数据
        dataframes = self.fetch_batch_concurrent(stock_codes, date_str, progress_callback)
        
        # 准备数据库插入数据
        data_to_insert = []
        
        for df in dataframes:
            if df.empty:
                continue
            
            for _, row in df.iterrows():
                try:
                    # 提取股票代码
                    code = row.get('code', '')
                    if '.' in code:
                        code = code.split('.')[1]
                    
                    data_to_insert.append((
                        code,  # stock_code
                        '',  # stock_name (暂时为空)
                        row.get('date', date_str),  # trade_date
                        float(row.get('open', 0)),  # open_price
                        float(row.get('close', 0)),  # close_price
                        float(row.get('high', 0)),  # high_price
                        float(row.get('low', 0)),  # low_price
                        int(float(row.get('volume', 0))),  # volume
                        float(row.get('amount', 0)),  # amount
                        float(row.get('pctChg', 0)),  # change_pct
                        float(row.get('turn', 0))  # turnover_rate
                    ))
                except Exception as e:
                    logger.warning(f"Failed to prepare data for {code}: {e}")
        
        logger.info(f"✅ Prepared {len(data_to_insert)} records for database insertion")
        
        return data_to_insert


# 全局实例
concurrent_fetcher = ConcurrentDataFetcher(max_workers=10)


# 便捷函数
def fetch_concurrent(stock_codes: List[str], date_str: str, max_workers: int = 10) -> List[pd.DataFrame]:
    """
    便捷函数：并发获取股票数据
    
    Args:
        stock_codes: 股票代码列表
        date_str: 日期字符串
        max_workers: 最大并发数
    
    Returns:
        DataFrame 列表
    """
    fetcher = ConcurrentDataFetcher(max_workers=max_workers)
    return fetcher.fetch_batch_concurrent(stock_codes, date_str)
