"""
股票筛选模块
负责实现股票筛选的核心算法
"""

import logging
import pandas as pd
import numpy as np
from typing import Set, Tuple
from datetime import datetime, timedelta


class StockFilter:
    """股票筛选器"""
    
    def __init__(self, config):
        """
        初始化筛选器
        
        Args:
            config: 配置模块
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def find_common_stocks(self, volume_df: pd.DataFrame, hot_df: pd.DataFrame) -> Set[str]:
        """
        找出成交额和热度两个股池的交集
        
        Args:
            volume_df: 成交额排名DataFrame
            hot_df: 热度排名DataFrame
            
        Returns:
            交集股票代码集合
        """
        if volume_df.empty or hot_df.empty:
            self.logger.warning("输入数据为空，无法找到交集")
            return set()
        
        volume_codes = set(volume_df['code'].astype(str))
        hot_codes = set(hot_df['code'].astype(str))
        
        common_codes = volume_codes.intersection(hot_codes)
        
        self.logger.info(f"成交额股池: {len(volume_codes)} 只")
        self.logger.info(f"热度股池: {len(hot_codes)} 只")
        self.logger.info(f"交集股池: {len(common_codes)} 只")
        
        return common_codes
    
    def min_max_normalize(self, data: pd.Series) -> pd.Series:
        """
        Min-Max标准化
        将数据缩放到[0, 1]区间
        
        Args:
            data: 原始数据序列
            
        Returns:
            标准化后的数据序列
        """
        if data.empty or data.isna().all():
            return data
        
        # 确保数据是数值类型
        data = pd.to_numeric(data, errors='coerce')
        
        # 删除NaN值后计算
        data_clean = data.dropna()
        if data_clean.empty:
            return pd.Series([0.0] * len(data), index=data.index)
        
        min_val = data_clean.min()
        max_val = data_clean.max()
        
        if max_val == min_val:
            # 所有值相同，返回全1
            return pd.Series([1.0] * len(data), index=data.index)
        
        normalized = (data - min_val) / (max_val - min_val)
        # 将NaN填充为0
        normalized = normalized.fillna(0)
        return normalized
    
    def calculate_comprehensive_score(
        self, 
        volume_df: pd.DataFrame, 
        hot_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        计算综合评分
        
        Args:
            volume_df: 成交额排名DataFrame
            hot_df: 热度排名DataFrame
            
        Returns:
            包含综合评分的DataFrame，按评分降序排列
        """
        self.logger.info("开始计算综合评分...")
        
        # 找交集
        common_codes = self.find_common_stocks(volume_df, hot_df)
        
        if not common_codes:
            self.logger.warning("没有找到交集股票")
            return pd.DataFrame()
        
        # 筛选交集股票
        volume_common = volume_df[volume_df['code'].astype(str).isin(common_codes)].copy()
        hot_common = hot_df[hot_df['code'].astype(str).isin(common_codes)].copy()
        
        # 确定用于评分的列
        volume_col = self._find_volume_column(volume_common)
        hot_col = self._find_hot_column(hot_common)
        
        if volume_col is None or hot_col is None:
            self.logger.error("无法找到成交额或热度列")
            return pd.DataFrame()
        
        # 标准化处理
        volume_common['volume_normalized'] = self.min_max_normalize(volume_common[volume_col])
        hot_common['hot_normalized'] = self.min_max_normalize(hot_common[hot_col])
        
        # 合并数据 - 保留所有有用的字段
        # 从 volume_common 中选择字段
        volume_cols = ['code', 'name', volume_col, 'volume_normalized']
        # 添加价格和涨跌幅字段（如果存在）
        for col in ['最新价', '最新涨跌幅']:
            if col in volume_common.columns:
                volume_cols.append(col)
        
        # 动态添加成交量字段（可能包含日期）
        for col in volume_common.columns:
            if col == '成交量' or '成交量[' in str(col):
                if col not in volume_cols:
                    volume_cols.append(col)
                break
        
        # 从 hot_common 中选择字段
        hot_cols = ['code', hot_col, 'hot_normalized']
        # 如果 volume_common 中没有价格字段，从 hot_common 中获取
        if '最新价' not in volume_cols and '最新价' in hot_common.columns:
            hot_cols.append('最新价')
        if '最新涨跌幅' not in volume_cols and '最新涨跌幅' in hot_common.columns:
            hot_cols.append('最新涨跌幅')
        
        merged = pd.merge(
            volume_common[volume_cols],
            hot_common[hot_cols],
            on='code',
            how='inner'
        )
        
        # 计算综合评分
        weight_volume = self.config.WEIGHT_VOLUME
        weight_hot = self.config.WEIGHT_HOT
        
        merged['comprehensive_score'] = (
            weight_volume * merged['volume_normalized'] + 
            weight_hot * merged['hot_normalized']
        )
        
        # 按评分降序排列
        merged = merged.sort_values('comprehensive_score', ascending=False)
        
        # 取前N名
        top_n = self.config.FINAL_TOP_N
        result = merged.head(top_n)
        
        self.logger.info(f"综合评分计算完成，筛选出 {len(result)} 只股票")
        
        return result
    
    def apply_filters(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """
        应用过滤规则
        
        Args:
            stocks_df: 待过滤的股票DataFrame
            
        Returns:
            过滤后的DataFrame
        """
        if stocks_df.empty:
            return stocks_df
        
        original_count = len(stocks_df)
        self.logger.info(f"开始应用过滤规则，原始股票数: {original_count}")
        
        # 1. 排除ST股
        if self.config.EXCLUDE_ST:
            stocks_df = stocks_df[~stocks_df['name'].str.contains('ST', na=False)]
            self.logger.info(f"排除ST股后剩余: {len(stocks_df)} 只")
        
        # 2. 排除次新股（需要上市日期信息，这里暂时跳过）
        # 实际应用中可以通过akshare获取上市日期进行过滤
        
        # 3. 排除涨幅过大的股票（需要历史数据，在动量计算阶段处理更合适）
        
        filtered_count = len(stocks_df)
        self.logger.info(f"过滤完成，剩余 {filtered_count} 只股票 (过滤掉 {original_count - filtered_count} 只)")
        
        return stocks_df
    
    def _find_volume_column(self, df: pd.DataFrame) -> str:
        """查找成交额列名"""
        possible_names = ['volume_amount', '成交额', 'amount']
        for name in possible_names:
            if name in df.columns:
                return name
        
        # 尝试模糊匹配（包含日期的字段）
        for col in df.columns:
            if '成交额' in str(col) or 'amount' in str(col).lower():
                return col
        
        return None
    
    def _find_hot_column(self, df: pd.DataFrame) -> str:
        """查找热度列名"""
        possible_names = ['hot_score', '热度', 'hot', '个股热度']
        for name in possible_names:
            if name in df.columns:
                return name
        
        # 尝试模糊匹配
        for col in df.columns:
            if '热度' in str(col) or 'hot' in str(col).lower():
                return col
        
        return None
