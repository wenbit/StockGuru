"""
Polars 数据处理服务
使用 Polars 替代 Pandas，性能提升 5-10 倍
"""

import logging
from typing import List, Dict, Optional
from datetime import date

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    logging.warning("Polars 未安装，将使用 Pandas")
    import pandas as pd

logger = logging.getLogger(__name__)


class PolarsDataProcessor:
    """Polars 数据处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.use_polars = POLARS_AVAILABLE
        
        if self.use_polars:
            self.logger.info("使用 Polars 进行数据处理（性能提升 5-10倍）")
        else:
            self.logger.warning("Polars 未安装，使用 Pandas")
    
    def process_daily_data(self, data: List[Dict]) -> any:
        """
        处理每日数据
        
        Args:
            data: 原始数据列表
            
        Returns:
            处理后的 DataFrame（Polars 或 Pandas）
        """
        if not data:
            return self._empty_dataframe()
        
        if self.use_polars:
            return self._process_with_polars(data)
        else:
            return self._process_with_pandas(data)
    
    def _process_with_polars(self, data: List[Dict]) -> pl.DataFrame:
        """使用 Polars 处理"""
        # 创建 DataFrame
        df = pl.DataFrame(data)
        
        # 数据类型转换
        df = df.with_columns([
            pl.col('open_price').cast(pl.Float64),
            pl.col('close_price').cast(pl.Float64),
            pl.col('high_price').cast(pl.Float64),
            pl.col('low_price').cast(pl.Float64),
            pl.col('volume').cast(pl.Int64),
            pl.col('amount').cast(pl.Float64),
            pl.col('change_pct').cast(pl.Float64),
            pl.col('turnover_rate').cast(pl.Float64)
        ])
        
        # 计算衍生字段
        df = df.with_columns([
            # 涨跌额
            (pl.col('close_price') - pl.col('open_price')).alias('change_amount'),
            # 振幅
            ((pl.col('high_price') - pl.col('low_price')) / pl.col('close_price') * 100)
            .round(2).alias('amplitude')
        ])
        
        return df
    
    def _process_with_pandas(self, data: List[Dict]) -> pd.DataFrame:
        """使用 Pandas 处理（回退方案）"""
        df = pd.DataFrame(data)
        
        # 数据类型转换
        numeric_cols = ['open_price', 'close_price', 'high_price', 'low_price',
                       'volume', 'amount', 'change_pct', 'turnover_rate']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 计算衍生字段
        df['change_amount'] = df['close_price'] - df['open_price']
        df['amplitude'] = ((df['high_price'] - df['low_price']) / df['close_price'] * 100).round(2)
        
        return df
    
    def filter_active_stocks(self, df: any, min_volume: int = 1000000) -> any:
        """
        筛选活跃股票
        
        Args:
            df: DataFrame
            min_volume: 最小成交量
            
        Returns:
            筛选后的 DataFrame
        """
        if self.use_polars:
            return df.filter(pl.col('volume') > min_volume)
        else:
            return df[df['volume'] > min_volume]
    
    def calculate_momentum(self, df: any, window: int = 5) -> any:
        """
        计算动量指标
        
        Args:
            df: DataFrame
            window: 窗口期
            
        Returns:
            添加动量列的 DataFrame
        """
        if self.use_polars:
            # Polars 滚动计算
            df = df.with_columns([
                pl.col('change_pct').rolling_mean(window).alias(f'momentum_{window}d'),
                pl.col('volume').rolling_mean(window).alias(f'avg_volume_{window}d')
            ])
        else:
            # Pandas 滚动计算
            df[f'momentum_{window}d'] = df['change_pct'].rolling(window).mean()
            df[f'avg_volume_{window}d'] = df['volume'].rolling(window).mean()
        
        return df
    
    def aggregate_by_date(self, df: any) -> any:
        """
        按日期聚合统计
        
        Args:
            df: DataFrame
            
        Returns:
            聚合后的 DataFrame
        """
        if self.use_polars:
            return df.group_by('trade_date').agg([
                pl.count().alias('total_stocks'),
                pl.col('change_pct').mean().alias('avg_change'),
                pl.col('volume').sum().alias('total_volume'),
                pl.col('amount').sum().alias('total_amount'),
                (pl.col('change_pct') > 0).sum().alias('up_count'),
                (pl.col('change_pct') < 0).sum().alias('down_count')
            ]).sort('trade_date', descending=True)
        else:
            return df.groupby('trade_date').agg({
                'stock_code': 'count',
                'change_pct': 'mean',
                'volume': 'sum',
                'amount': 'sum'
            }).rename(columns={'stock_code': 'total_stocks'})
    
    def top_gainers(self, df: any, n: int = 10) -> any:
        """
        获取涨幅前N名
        
        Args:
            df: DataFrame
            n: 数量
            
        Returns:
            Top N DataFrame
        """
        if self.use_polars:
            return df.sort('change_pct', descending=True).head(n)
        else:
            return df.nlargest(n, 'change_pct')
    
    def to_dict_list(self, df: any) -> List[Dict]:
        """
        转换为字典列表
        
        Args:
            df: DataFrame
            
        Returns:
            字典列表
        """
        if self.use_polars:
            return df.to_dicts()
        else:
            return df.to_dict('records')
    
    def to_pandas(self, df: any) -> pd.DataFrame:
        """
        转换为 Pandas DataFrame
        
        Args:
            df: Polars DataFrame
            
        Returns:
            Pandas DataFrame
        """
        if self.use_polars and isinstance(df, pl.DataFrame):
            return df.to_pandas()
        return df
    
    def _empty_dataframe(self) -> any:
        """返回空 DataFrame"""
        if self.use_polars:
            return pl.DataFrame()
        else:
            return pd.DataFrame()
    
    def benchmark_comparison(self, data: List[Dict], iterations: int = 100):
        """
        性能基准测试
        
        Args:
            data: 测试数据
            iterations: 迭代次数
        """
        import time
        
        if not POLARS_AVAILABLE:
            self.logger.warning("Polars 未安装，无法进行对比测试")
            return
        
        # Polars 测试
        start = time.time()
        for _ in range(iterations):
            df_pl = pl.DataFrame(data)
            df_pl = df_pl.filter(pl.col('volume') > 1000000)
            df_pl = df_pl.sort('change_pct', descending=True)
        polars_time = time.time() - start
        
        # Pandas 测试
        start = time.time()
        for _ in range(iterations):
            df_pd = pd.DataFrame(data)
            df_pd = df_pd[df_pd['volume'] > 1000000]
            df_pd = df_pd.sort_values('change_pct', ascending=False)
        pandas_time = time.time() - start
        
        speedup = pandas_time / polars_time
        
        self.logger.info(f"性能对比（{iterations}次迭代）:")
        self.logger.info(f"  Polars: {polars_time:.3f}秒")
        self.logger.info(f"  Pandas: {pandas_time:.3f}秒")
        self.logger.info(f"  加速比: {speedup:.2f}x")
        
        return {
            'polars_time': polars_time,
            'pandas_time': pandas_time,
            'speedup': speedup
        }


# 全局实例
_processor_instance = None

def get_processor() -> PolarsDataProcessor:
    """获取全局处理器实例"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = PolarsDataProcessor()
    return _processor_instance
