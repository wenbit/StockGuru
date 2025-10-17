"""
优化获取器
使用批量处理 + 并行数据处理
实测有效的优化方案
"""

import logging
import time
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

logger = logging.getLogger(__name__)


class OptimizedFetcher:
    """
    优化获取器（实用版）
    - 串行获取（Baostock限制）
    - 并行处理数据（CPU密集型）
    - 批量准备插入
    """
    
    def __init__(self):
        logger.info("✅ Optimized fetcher initialized")
    
    def fetch_all_optimized(
        self,
        stock_codes: List[str],
        date_str: str,
        progress_callback=None
    ) -> List[Tuple[str, pd.DataFrame]]:
        """
        优化的批量获取
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            progress_callback: 进度回调
        
        Returns:
            (code, DataFrame) 元组列表
        """
        import baostock as bs
        
        logger.info(f"🚀 Starting optimized fetch for {len(stock_codes)} stocks")
        
        # 1. 只登录一次
        bs.login()
        start_time = time.time()
        
        raw_data = []
        success_count = 0
        
        try:
            # 2. 串行获取（Baostock 不支持并发）
            for i, code in enumerate(stock_codes):
                try:
                    # 直接获取
                    df = self._fetch_single(code, date_str, bs)
                    
                    if not df.empty:
                        raw_data.append((code, df))
                        success_count += 1
                    
                    # 进度回调
                    if progress_callback and ((i + 1) % 100 == 0 or i + 1 == len(stock_codes)):
                        progress_callback(i + 1, len(stock_codes), code)
                
                except Exception as e:
                    logger.warning(f"Failed to fetch {code}: {e}")
            
            fetch_time = time.time() - start_time
            
            logger.info(
                f"✅ Fetch completed: {success_count}/{len(stock_codes)} "
                f"in {fetch_time:.2f}s ({len(stock_codes)/fetch_time:.1f} stocks/s)"
            )
        
        finally:
            # 3. 只登出一次
            bs.logout()
        
        return raw_data
    
    
    def _fetch_single(self, code: str, date_str: str, bs) -> pd.DataFrame:
        """
        获取单只股票
        
        Args:
            code: 股票代码
            date_str: 日期
            bs: baostock 实例
        
        Returns:
            DataFrame
        """
        try:
            prefix = "sh." if code.startswith('6') else "sz."
            rs = bs.query_history_k_data_plus(
                f"{prefix}{code}",
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=date_str,
                end_date=date_str
            )
            
            data = []
            while rs.error_code == '0' and rs.next():
                data.append(rs.get_row_data())
            
            if data:
                df = pd.DataFrame(data, columns=rs.fields)
                return df
            
            return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error fetching {code}: {e}")
            return pd.DataFrame()
    
    def process_data_parallel(
        self,
        raw_data: List[Tuple[str, pd.DataFrame]],
        max_workers: int = 4
    ) -> List[tuple]:
        """
        并行处理数据
        
        Args:
            raw_data: 原始数据列表
            max_workers: 最大工作线程数
        
        Returns:
            准备好的数据库插入元组列表
        """
        logger.info(f"🔄 Processing {len(raw_data)} records with {max_workers} workers")
        
        start_time = time.time()
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self._process_single, raw_data))
        
        # 展平结果
        data_to_insert = []
        for result in results:
            if result:
                data_to_insert.extend(result)
        
        process_time = time.time() - start_time
        
        logger.info(
            f"✅ Processing completed: {len(data_to_insert)} records "
            f"in {process_time:.2f}s"
        )
        
        return data_to_insert
    
    def _process_single(self, item: Tuple[str, pd.DataFrame]) -> List[tuple]:
        """
        处理单个数据
        
        Args:
            item: (code, DataFrame) 元组
        
        Returns:
            数据库插入元组列表
        """
        code, df = item
        
        if df.empty:
            return []
        
        result = []
        
        try:
            for _, row in df.iterrows():
                result.append((
                    code,  # stock_code
                    '',  # stock_name
                    row.get('date', ''),  # trade_date
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
            logger.warning(f"Failed to process {code}: {e}")
        
        return result


# 全局实例
optimized_fetcher = OptimizedFetcher()
