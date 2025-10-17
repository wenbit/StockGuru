"""
增强的数据获取器 - 解决网络问题
针对 AData 和 AKShare 的网络连接问题进行优化
"""

import time
import logging
from typing import List, Dict, Optional
import pandas as pd
from datetime import date

logger = logging.getLogger(__name__)


class EnhancedADataFetcher:
    """增强的 AData 获取器 - 解决网络问题"""
    
    def __init__(self):
        try:
            import adata
            self.adata = adata
            self.available = True
            
            # 设置更长的超时和重试
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # 创建会话
            self.session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=5,  # 总重试次数
                backoff_factor=2,  # 退避因子
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20
            )
            
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive'
            })
            
            logger.info("Enhanced AData fetcher initialized")
            
        except ImportError:
            logger.warning("AData not installed")
            self.adata = None
            self.available = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str, max_retries: int = 3) -> pd.DataFrame:
        """
        获取单只股票数据（增强版）
        
        Args:
            stock_code: 股票代码
            date_str: 日期字符串
            max_retries: 最大重试次数
        
        Returns:
            DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        for attempt in range(max_retries):
            try:
                # 添加请求间隔，避免过快
                if attempt > 0:
                    time.sleep(1 * (2 ** attempt))  # 指数退避
                
                logger.debug(f"AData attempt {attempt + 1}/{max_retries} for {stock_code}")
                
                # 使用 adata 获取数据
                df = self.adata.stock.market.get_market(
                    stock_code=stock_code,
                    k_type=1,
                    start_date=date_str,
                    end_date=date_str
                )
                
                if not df.empty:
                    logger.info(f"✅ AData success: {stock_code}")
                    return df
                
            except Exception as e:
                logger.warning(f"AData attempt {attempt + 1} failed for {stock_code}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"AData fetch failed after {max_retries} attempts: {stock_code}")
        
        return pd.DataFrame()
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.available


class EnhancedAKShareFetcher:
    """增强的 AKShare 获取器 - 解决网络问题"""
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
            
            # 配置 requests 会话
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            self.session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=5,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20
            )
            
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate'
            })
            
            logger.info("Enhanced AKShare fetcher initialized")
            
        except ImportError:
            logger.warning("AKShare not installed")
            self.ak = None
            self.available = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str, max_retries: int = 3) -> pd.DataFrame:
        """
        获取单只股票数据（增强版）
        
        Args:
            stock_code: 股票代码
            date_str: 日期字符串
            max_retries: 最大重试次数
        
        Returns:
            DataFrame
        """
        if not self.available:
            return pd.DataFrame()
        
        for attempt in range(max_retries):
            try:
                # 添加请求间隔
                if attempt > 0:
                    time.sleep(1 * (2 ** attempt))  # 指数退避
                
                logger.debug(f"AKShare attempt {attempt + 1}/{max_retries} for {stock_code}")
                
                # 使用 akshare 获取数据
                df = self.ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=date_str.replace('-', ''),
                    end_date=date_str.replace('-', ''),
                    adjust=""
                )
                
                if not df.empty:
                    logger.info(f"✅ AKShare success: {stock_code}")
                    return df
                
            except ConnectionError as e:
                logger.warning(f"AKShare connection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 * (2 ** attempt))  # 连接错误时等待更长时间
            
            except Exception as e:
                logger.warning(f"AKShare attempt {attempt + 1} failed for {stock_code}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"AKShare fetch failed after {max_retries} attempts: {stock_code}")
        
        return pd.DataFrame()
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.available


class RobustMultiSourceFetcher:
    """
    健壮的多数据源获取器
    优化：Baostock 优先（最稳定），AData/AKShare 快速失败
    """
    
    def __init__(self):
        self.sources = []
        
        # 优先使用 Baostock（最稳定，速度快）
        try:
            import baostock as bs
            self.bs = bs
            self.bs_logged_in = False
            self.sources.append(('baostock', None))
            logger.info("✅ Baostock source loaded (Priority 1)")
        except ImportError:
            logger.warning("Baostock not available")
        
        # AData 作为备选（降低优先级，快速失败）
        adata_fetcher = EnhancedADataFetcher()
        if adata_fetcher.is_available():
            self.sources.append(('adata', adata_fetcher))
            logger.info("✅ Enhanced AData source loaded (Priority 2)")
        
        # AKShare 作为最后选择（降低优先级，快速失败）
        akshare_fetcher = EnhancedAKShareFetcher()
        if akshare_fetcher.is_available():
            self.sources.append(('akshare', akshare_fetcher))
            logger.info("✅ Enhanced AKShare source loaded (Priority 3)")
        
        logger.info(f"Initialized with {len(self.sources)} sources: {[s[0] for s in self.sources]}")
        logger.info("Priority: Baostock (fast) → AData (backup) → AKShare (last)")
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """
        多数据源获取（Baostock优先，其他快速失败）
        
        Args:
            stock_code: 股票代码
            date_str: 日期字符串
        
        Returns:
            DataFrame
        """
        for source_name, fetcher in self.sources:
            try:
                logger.debug(f"Trying {source_name} for {stock_code}")
                
                if source_name == 'baostock':
                    # Baostock: 稳定快速，正常重试
                    df = self._fetch_from_baostock(stock_code, date_str)
                elif source_name == 'adata':
                    # AData: 快速失败，只重试1次
                    df = fetcher.fetch_daily_data(stock_code, date_str, max_retries=1)
                else:  # akshare
                    # AKShare: 快速失败，只重试1次
                    df = fetcher.fetch_daily_data(stock_code, date_str, max_retries=1)
                
                if not df.empty:
                    logger.info(f"✅ {source_name} succeeded for {stock_code}")
                    return df
                else:
                    logger.debug(f"⚠️  {source_name} returned empty data, switching to next source")
                
            except Exception as e:
                logger.warning(f"❌ {source_name} failed for {stock_code}, switching to next source")
                continue
        
        logger.error(f"All sources failed for {stock_code}")
        return pd.DataFrame()
    
    def _fetch_from_baostock(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """从 Baostock 获取数据"""
        if not self.bs_logged_in:
            self.bs.login()
            self.bs_logged_in = True
        
        prefix = "sh." if stock_code.startswith('6') else "sz."
        rs = self.bs.query_history_k_data_plus(
            f"{prefix}{stock_code}",
            "date,code,open,high,low,close,volume,amount,turn,pctChg",
            start_date=date_str,
            end_date=date_str
        )
        
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame(data, columns=rs.fields)
    
    def fetch_batch_data(self, stock_codes: List[str], date_str: str, 
                        min_success_rate: float = 0.8) -> pd.DataFrame:
        """
        批量获取数据
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            min_success_rate: 最小成功率
        
        Returns:
            DataFrame
        """
        results = []
        success_count = 0
        
        for code in stock_codes:
            try:
                df = self.fetch_daily_data(code, date_str)
                if not df.empty:
                    results.append(df)
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to fetch {code}: {e}")
        
        success_rate = success_count / len(stock_codes) if stock_codes else 0
        logger.info(f"Batch fetch: {success_count}/{len(stock_codes)} ({success_rate:.1%})")
        
        if results:
            return pd.concat(results, ignore_index=True)
        
        return pd.DataFrame()


# 全局实例
robust_fetcher = RobustMultiSourceFetcher()
