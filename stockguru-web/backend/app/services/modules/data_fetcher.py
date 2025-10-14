"""
数据获取模块
负责从外部数据源获取股票数据
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    import pywencai
except ImportError:
    logging.warning("pywencai 未安装，部分功能将不可用")
    pywencai = None

try:
    import akshare as ak
except ImportError:
    logging.warning("akshare 未安装，部分功能将不可用")
    ak = None


class DataFetcher:
    """数据获取器"""
    
    def __init__(self):
        """初始化数据获取器"""
        self.logger = logging.getLogger(__name__)
        
    def get_volume_top_stocks(self, date: str, top_n: int = 100) -> pd.DataFrame:
        """
        获取成交额排名前N的股票
        
        Args:
            date: 查询日期，格式：YYYY-MM-DD
            top_n: 排名数量
            
        Returns:
            包含股票代码、名称、成交额等信息的DataFrame
        """
        if pywencai is None:
            raise ImportError("pywencai 未安装，请运行: pip install pywencai")
        
        try:
            self.logger.info(f"正在获取 {date} 成交额前 {top_n} 的股票...")
            query = f'{date}成交额前{top_n}'
            df = pywencai.get(query=query, loop=True)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到成交额数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_columns(df, data_type='volume')
            
            # 去除重复的行（基于股票代码）
            if 'code' in df.columns:
                df = df.drop_duplicates(subset=['code'], keep='first')
            
            self.logger.info(f"成功获取 {len(df)} 只股票的成交额数据")
            return df
            
        except Exception as e:
            self.logger.error(f"获取成交额数据失败: {str(e)}")
            raise
    
    def get_hot_top_stocks(self, date: str, top_n: int = 100) -> pd.DataFrame:
        """
        获取热度排名前N的股票
        
        Args:
            date: 查询日期，格式：YYYY-MM-DD
            top_n: 排名数量
            
        Returns:
            包含股票代码、名称、热度等信息的DataFrame
        """
        if pywencai is None:
            raise ImportError("pywencai 未安装，请运行: pip install pywencai")
        
        try:
            self.logger.info(f"正在获取 {date} 热度前 {top_n} 的股票...")
            query = f'{date}个股热度前{top_n}'
            df = pywencai.get(query=query, loop=True)
            
            if df is None or df.empty:
                self.logger.warning(f"未获取到热度数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = self._standardize_columns(df, data_type='hot')
            
            # 去除重复的行（基于股票代码）
            if 'code' in df.columns:
                df = df.drop_duplicates(subset=['code'], keep='first')
            
            # 重置索引，避免重复标签问题
            df = df.reset_index(drop=True)
            
            self.logger.info(f"成功获取 {len(df)} 只股票的热度数据")
            return df
            
        except Exception as e:
            self.logger.error(f"获取热度数据失败: {str(e)}")
            raise
    
    def get_stock_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取指定股票的日线行情数据
        
        Args:
            code: 股票代码（如：600000）
            days: 获取最近N天的数据
            
        Returns:
            包含日期、开盘价、收盘价、最高价、最低价、成交量等的DataFrame
        """
        if ak is None:
            raise ImportError("akshare 未安装，请运行: pip install akshare")
        
        # 重试机制
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"正在获取股票 {code} 的日线数据... (尝试 {attempt + 1}/{max_retries})")
                
                # akshare 获取A股日线数据
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=(datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d'),
                    adjust="qfq"  # 前复权
                )
                
                if df is None or df.empty:
                    self.logger.warning(f"股票 {code} 未获取到日线数据")
                    return pd.DataFrame()
                
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '涨跌幅': 'pct_change'
                })
                
                # 只取最近N天
                df = df.tail(days)
                
                self.logger.debug(f"成功获取股票 {code} 的 {len(df)} 天日线数据")
                return df
                
            except Exception as e:
                self.logger.warning(f"获取股票 {code} 日线数据失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"获取股票 {code} 日线数据最终失败，已重试 {max_retries} 次")
                    return pd.DataFrame()
    
    def get_stock_info(self, code: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            包含股票名称、行业等信息的字典
        """
        if ak is None:
            raise ImportError("akshare 未安装，请运行: pip install akshare")
        
        try:
            # 获取股票基本信息
            # 注意：akshare的接口可能会变化，这里提供基础实现
            info = {
                'code': code,
                'name': '',
                'industry': '未知',
                'list_date': ''
            }
            
            # 尝试从实时行情中获取名称
            try:
                realtime_df = ak.stock_zh_a_spot_em()
                stock_row = realtime_df[realtime_df['代码'] == code]
                if not stock_row.empty:
                    info['name'] = stock_row.iloc[0]['名称']
            except:
                pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取股票 {code} 基本信息失败: {str(e)}")
            return {'code': code, 'name': '', 'industry': '未知', 'list_date': ''}
    
    def _standardize_columns(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        标准化DataFrame的列名
        
        Args:
            df: 原始DataFrame
            data_type: 数据类型 ('volume' 或 'hot')
            
        Returns:
            标准化后的DataFrame
        """
        # 处理重复的列名
        if df.columns.duplicated().any():
            new_columns = []
            col_counts = {}
            for col in df.columns:
                if col in col_counts:
                    col_counts[col] += 1
                    new_columns.append(f"{col}_{col_counts[col]}")
                else:
                    col_counts[col] = 0
                    new_columns.append(col)
            df.columns = new_columns
        
        # 如果已经有code列，先删除其他可能的代码列
        if 'code' in df.columns:
            # 删除其他代码相关列
            cols_to_drop = [col for col in df.columns if col != 'code' and ('代码' in str(col) or col == '股票代码')]
            df = df.drop(columns=cols_to_drop, errors='ignore')
        else:
            # 没有code列，需要映射
            for col in df.columns:
                if '股票代码' == col or '证券代码' == col:
                    df = df.rename(columns={col: 'code'})
                    break
        
        # 处理name列
        if 'name' not in df.columns:
            for col in df.columns:
                if '股票简称' == col or '股票名称' == col or '证券名称' == col:
                    df = df.rename(columns={col: 'name'})
                    break
        
        # 处理成交额和热度列（保持原列名，便于后续识别）
        # 不需要重命名，因为我们会在筛选模块中动态查找
        
        # 清理股票代码格式（去除市场前缀）
        if 'code' in df.columns:
            def clean_code(x):
                s = str(x)
                if s == 'nan' or not s:
                    return ''
                return ''.join(c for c in s if c.isdigit())
            df['code'] = df['code'].apply(clean_code)
        
        return df
    
    def batch_get_stock_data(self, codes: List[str], days: int = 60) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的日线数据
        
        Args:
            codes: 股票代码列表
            days: 获取天数
            
        Returns:
            字典，key为股票代码，value为对应的DataFrame
        """
        result = {}
        total = len(codes)
        
        for i, code in enumerate(codes, 1):
            self.logger.info(f"正在获取股票数据 ({i}/{total}): {code}")
            df = self.get_stock_daily_data(code, days)
            if not df.empty:
                result[code] = df
        
        return result
