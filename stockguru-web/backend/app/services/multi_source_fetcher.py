"""
多数据源融合架构
借鉴 AData 的多数据源融合设计
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import date
import pandas as pd
import logging

from app.exceptions import DataSourceError
from app.utils.smart_request import smart_request

logger = logging.getLogger(__name__)


class DataSourceTemplate(ABC):
    """数据源模板基类（借鉴 AData）"""
    
    # 统一的列定义
    COLUMNS = [
        'stock_code', 'stock_name', 'trade_date',
        'open_price', 'close_price', 'high_price', 'low_price',
        'volume', 'amount', 'change_pct', 'change_amount',
        'turnover_rate', 'amplitude'
    ]
    
    @abstractmethod
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """获取单只股票日线数据"""
        pass
    
    @abstractmethod
    def fetch_batch_data(self, stock_codes: List[str], date_str: str) -> pd.DataFrame:
        """批量获取股票数据"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """数据源名称"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass


class BaostockSource(DataSourceTemplate):
    """Baostock 数据源（兜底）"""
    
    def __init__(self):
        try:
            import baostock as bs
            self.bs = bs
            self.logged_in = False
            self.available = True
        except ImportError:
            logger.warning("Baostock not installed")
            self.bs = None
            self.available = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        if not self.available:
            raise DataSourceError("Baostock not available", source_name="baostock")
        
        if not self.logged_in:
            self.bs.login()
            self.logged_in = True
        
        # 实现 baostock 获取逻辑
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
        
        df = pd.DataFrame(data, columns=rs.fields)
        # 数据转换...
        return self._normalize_data(df)
    
    def fetch_batch_data(self, stock_codes: List[str], date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            try:
                df = self.fetch_daily_data(code, date_str)
                if not df.empty:
                    results.append(df)
            except Exception as e:
                logger.warning(f"Failed to fetch {code}: {e}")
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "baostock"
    
    def is_available(self) -> bool:
        return self.available
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 实现数据标准化逻辑
        return df


class ADataSource(DataSourceTemplate):
    """AData 数据源"""
    
    def __init__(self):
        try:
            import adata
            self.adata = adata
            self.available = True
        except ImportError:
            logger.warning("AData not installed")
            self.adata = None
            self.available = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        if not self.available:
            raise DataSourceError("AData not available", source_name="adata")
        
        try:
            df = self.adata.stock.market.get_market(
                stock_code=stock_code,
                k_type=1,
                start_date=date_str,
                end_date=date_str
            )
            return self._normalize_data(df)
        except Exception as e:
            logger.error(f"AData fetch failed: {e}")
            return pd.DataFrame()
    
    def fetch_batch_data(self, stock_codes: List[str], date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            try:
                df = self.fetch_daily_data(code, date_str)
                if not df.empty:
                    results.append(df)
            except Exception as e:
                logger.warning(f"Failed to fetch {code}: {e}")
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "adata"
    
    def is_available(self) -> bool:
        return self.available
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 实现数据标准化逻辑
        return df


class AKShareSource(DataSourceTemplate):
    """AKShare 数据源"""
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.available = True
        except ImportError:
            logger.warning("AKShare not installed")
            self.ak = None
            self.available = False
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        if not self.available:
            raise DataSourceError("AKShare not available", source_name="akshare")
        
        try:
            df = self.ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=date_str.replace('-', ''),
                end_date=date_str.replace('-', ''),
                adjust=""
            )
            return self._normalize_data(df)
        except Exception as e:
            logger.error(f"AKShare fetch failed: {e}")
            return pd.DataFrame()
    
    def fetch_batch_data(self, stock_codes: List[str], date_str: str) -> pd.DataFrame:
        results = []
        for code in stock_codes:
            try:
                df = self.fetch_daily_data(code, date_str)
                if not df.empty:
                    results.append(df)
            except Exception as e:
                logger.warning(f"Failed to fetch {code}: {e}")
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
    def get_source_name(self) -> str:
        return "akshare"
    
    def is_available(self) -> bool:
        return self.available
    
    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        # 实现数据标准化逻辑
        return df


class MultiSourceFetcher:
    """多数据源融合获取器（借鉴 AData）"""
    
    def __init__(self, enable_adata: bool = True, enable_akshare: bool = True):
        """
        初始化多数据源
        
        Args:
            enable_adata: 是否启用 AData
            enable_akshare: 是否启用 AKShare
        """
        self.sources = []
        
        # 优先级顺序：AData > AKShare > Baostock
        if enable_adata:
            adata_source = ADataSource()
            if adata_source.is_available():
                self.sources.append(adata_source)
        
        if enable_akshare:
            akshare_source = AKShareSource()
            if akshare_source.is_available():
                self.sources.append(akshare_source)
        
        # Baostock 作为兜底
        baostock_source = BaostockSource()
        if baostock_source.is_available():
            self.sources.append(baostock_source)
        
        logger.info(f"Initialized with {len(self.sources)} data sources: "
                   f"{[s.get_source_name() for s in self.sources]}")
    
    def fetch_daily_data(self, stock_code: str, date_str: str) -> pd.DataFrame:
        """
        多数据源获取单只股票数据（自动切换）
        
        Args:
            stock_code: 股票代码
            date_str: 日期字符串
        
        Returns:
            DataFrame
        """
        for source in self.sources:
            try:
                logger.debug(f"Trying {source.get_source_name()} for {stock_code}")
                df = source.fetch_daily_data(stock_code, date_str)
                
                if not df.empty:
                    logger.info(f"✅ {source.get_source_name()} succeeded: {stock_code}")
                    return df
                
            except Exception as e:
                logger.warning(f"❌ {source.get_source_name()} failed: {e}")
                continue
        
        logger.error(f"All data sources failed for {stock_code}")
        return pd.DataFrame()
    
    def fetch_batch_data(
        self,
        stock_codes: List[str],
        date_str: str,
        min_success_rate: float = 0.8
    ) -> pd.DataFrame:
        """
        批量获取股票数据（自动切换数据源）
        
        Args:
            stock_codes: 股票代码列表
            date_str: 日期字符串
            min_success_rate: 最小成功率（0.8 = 80%）
        
        Returns:
            DataFrame
        """
        for source in self.sources:
            try:
                logger.info(f"Trying {source.get_source_name()} for batch ({len(stock_codes)} stocks)")
                df = source.fetch_batch_data(stock_codes, date_str)
                
                # 验证数据完整性
                success_rate = len(df) / len(stock_codes) if stock_codes else 0
                
                if success_rate >= min_success_rate:
                    logger.info(
                        f"✅ {source.get_source_name()} batch succeeded: "
                        f"{len(df)}/{len(stock_codes)} ({success_rate:.1%})"
                    )
                    return df
                else:
                    logger.warning(
                        f"⚠️  {source.get_source_name()} success rate too low: "
                        f"{success_rate:.1%} < {min_success_rate:.1%}"
                    )
                
            except Exception as e:
                logger.warning(f"❌ {source.get_source_name()} batch failed: {e}")
                continue
        
        logger.error("All data sources failed for batch fetch")
        return pd.DataFrame()


# 全局实例
multi_source_fetcher = MultiSourceFetcher()
