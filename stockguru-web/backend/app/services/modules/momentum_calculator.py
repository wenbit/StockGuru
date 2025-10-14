"""
动量计算模块
负责计算股票的动量得分
"""

import logging
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, List


class MomentumCalculator:
    """动量计算器"""
    
    def __init__(self, config):
        """
        初始化动量计算器
        
        Args:
            config: 配置模块
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_momentum(self, price_series: pd.Series) -> float:
        """
        计算单只股票的动量得分
        使用线性回归方法：动量分 = 斜率 × R²
        
        Args:
            price_series: 价格序列（收盘价）
            
        Returns:
            动量得分
        """
        if price_series is None or len(price_series) < 2:
            self.logger.warning("价格序列数据不足，无法计算动量")
            return 0.0
        
        try:
            # 计算相对价格（归一化到第一天）
            first_price = price_series.iloc[0]
            if first_price == 0:
                return 0.0
            
            relative_prices = price_series / first_price
            
            # 准备回归数据
            x = np.arange(len(relative_prices)).reshape(-1, 1)
            y = relative_prices.values
            
            # 线性回归
            lr = LinearRegression()
            lr.fit(x, y)
            
            # 计算斜率和R²
            slope = lr.coef_[0]
            r_squared = lr.score(x, y)
            
            # 动量得分 = 斜率 × R² × 10000（放大便于比较）
            momentum_score = 10000 * slope * r_squared
            
            return momentum_score
            
        except Exception as e:
            self.logger.error(f"计算动量得分失败: {str(e)}")
            return 0.0
    
    def batch_calculate(
        self, 
        stocks_df: pd.DataFrame, 
        stock_data_dict: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        批量计算多只股票的动量得分
        
        Args:
            stocks_df: 候选股票DataFrame（包含code、name等信息）
            stock_data_dict: 股票日线数据字典，key为股票代码，value为日线DataFrame
            
        Returns:
            添加了动量得分的DataFrame，按动量得分降序排列
        """
        self.logger.info(f"开始批量计算 {len(stocks_df)} 只股票的动量得分...")
        
        momentum_scores = []
        valid_stocks = []
        
        for idx, row in stocks_df.iterrows():
            code = str(row['code'])
            name = row.get('name', '')
            
            # 获取该股票的日线数据
            if code not in stock_data_dict:
                self.logger.warning(f"股票 {code} {name} 没有日线数据，跳过")
                continue
            
            stock_data = stock_data_dict[code]
            
            if stock_data.empty or 'close' not in stock_data.columns:
                self.logger.warning(f"股票 {code} {name} 日线数据无效，跳过")
                continue
            
            # 获取最近N天的收盘价
            days = self.config.MOMENTUM_DAYS
            close_prices = stock_data['close'].tail(days)
            
            if len(close_prices) < days * 0.8:  # 至少要有80%的数据
                self.logger.warning(f"股票 {code} {name} 数据不足 ({len(close_prices)}/{days}天)，跳过")
                continue
            
            # 计算动量得分
            momentum = self.calculate_momentum(close_prices)
            
            momentum_scores.append(momentum)
            valid_stocks.append(row)
            
            self.logger.debug(f"股票 {code} {name} 动量得分: {momentum:.2f}")
        
        if not valid_stocks:
            self.logger.warning("没有有效的股票数据")
            return pd.DataFrame()
        
        # 构建结果DataFrame
        result_df = pd.DataFrame(valid_stocks)
        result_df['momentum_score'] = momentum_scores
        
        # 按动量得分降序排列
        result_df = result_df.sort_values('momentum_score', ascending=False)
        
        # 取前N名
        top_n = self.config.MOMENTUM_TOP_N
        result_df = result_df.head(top_n)
        
        self.logger.info(f"动量计算完成，筛选出前 {len(result_df)} 只股票")
        
        return result_df
    
    def calculate_ma(self, price_series: pd.Series, period: int) -> pd.Series:
        """
        计算移动平均线
        
        Args:
            price_series: 价格序列
            period: 均线周期
            
        Returns:
            移动平均线序列
        """
        return price_series.rolling(window=period).mean()
    
    def calculate_all_ma(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有配置的均线
        
        Args:
            stock_data: 股票日线数据
            
        Returns:
            添加了均线列的DataFrame
        """
        if stock_data.empty or 'close' not in stock_data.columns:
            return stock_data
        
        result = stock_data.copy()
        
        for period in self.config.MA_PERIODS:
            ma_col = f'ma{period}'
            result[ma_col] = self.calculate_ma(result['close'], period)
        
        return result
