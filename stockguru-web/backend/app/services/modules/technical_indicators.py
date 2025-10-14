"""
技术指标计算模块
提供常用的技术分析指标计算
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                       fast: int = 12, 
                       slow: int = 26, 
                       signal: int = 9) -> Dict[str, pd.Series]:
        """
        计算 MACD 指标
        
        Args:
            prices: 收盘价序列
            fast: 快速EMA周期 (默认12)
            slow: 慢速EMA周期 (默认26)
            signal: 信号线周期 (默认9)
            
        Returns:
            包含 DIF, DEA, MACD 的字典
        """
        try:
            # 计算快速和慢速EMA
            ema_fast = prices.ewm(span=fast, adjust=False).mean()
            ema_slow = prices.ewm(span=slow, adjust=False).mean()
            
            # DIF = 快线 - 慢线
            dif = ema_fast - ema_slow
            
            # DEA = DIF的EMA
            dea = dif.ewm(span=signal, adjust=False).mean()
            
            # MACD柱 = (DIF - DEA) * 2
            macd = (dif - dea) * 2
            
            return {
                'dif': dif,
                'dea': dea,
                'macd': macd
            }
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            return {
                'dif': pd.Series(),
                'dea': pd.Series(),
                'macd': pd.Series()
            }
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算 RSI 指标 (相对强弱指标)
        
        Args:
            prices: 收盘价序列
            period: 计算周期 (默认14)
            
        Returns:
            RSI 值序列 (0-100)
        """
        try:
            # 计算价格变化
            delta = prices.diff()
            
            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 计算平均涨跌幅
            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()
            
            # 计算RS和RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            return pd.Series()
    
    @staticmethod
    def calculate_boll(prices: pd.Series, 
                       period: int = 20, 
                       std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        计算布林带指标
        
        Args:
            prices: 收盘价序列
            period: 计算周期 (默认20)
            std_dev: 标准差倍数 (默认2)
            
        Returns:
            包含 upper, middle, lower 的字典
        """
        try:
            # 中轨 = 移动平均线
            middle = prices.rolling(window=period).mean()
            
            # 标准差
            std = prices.rolling(window=period).std()
            
            # 上轨 = 中轨 + 标准差 * 倍数
            upper = middle + (std * std_dev)
            
            # 下轨 = 中轨 - 标准差 * 倍数
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
        except Exception as e:
            logger.error(f"计算BOLL失败: {str(e)}")
            return {
                'upper': pd.Series(),
                'middle': pd.Series(),
                'lower': pd.Series()
            }
    
    @staticmethod
    def calculate_kdj(high: pd.Series, 
                      low: pd.Series, 
                      close: pd.Series,
                      n: int = 9, 
                      m1: int = 3, 
                      m2: int = 3) -> Dict[str, pd.Series]:
        """
        计算 KDJ 指标 (随机指标)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            n: RSV周期 (默认9)
            m1: K值平滑周期 (默认3)
            m2: D值平滑周期 (默认3)
            
        Returns:
            包含 K, D, J 的字典
        """
        try:
            # 计算RSV (未成熟随机值)
            lowest_low = low.rolling(window=n, min_periods=1).min()
            highest_high = high.rolling(window=n, min_periods=1).max()
            
            rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
            rsv = rsv.fillna(50)  # 填充NaN为50
            
            # 计算K值 (RSV的移动平均)
            k = rsv.ewm(alpha=1/m1, adjust=False).mean()
            
            # 计算D值 (K值的移动平均)
            d = k.ewm(alpha=1/m2, adjust=False).mean()
            
            # 计算J值
            j = 3 * k - 2 * d
            
            return {
                'k': k,
                'd': d,
                'j': j
            }
        except Exception as e:
            logger.error(f"计算KDJ失败: {str(e)}")
            return {
                'k': pd.Series(),
                'd': pd.Series(),
                'j': pd.Series()
            }
    
    @staticmethod
    def calculate_volume_ma(volume: pd.Series, periods: list = [5, 10, 20]) -> Dict[str, pd.Series]:
        """
        计算成交量移动平均线
        
        Args:
            volume: 成交量序列
            periods: 周期列表 (默认[5, 10, 20])
            
        Returns:
            包含各周期MA的字典
        """
        try:
            result = {}
            for period in periods:
                result[f'ma{period}'] = volume.rolling(window=period).mean()
            return result
        except Exception as e:
            logger.error(f"计算成交量MA失败: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        
        Args:
            df: 包含 open, high, low, close, volume 的DataFrame
            
        Returns:
            添加了所有技术指标的DataFrame
        """
        try:
            result_df = df.copy()
            
            # MACD
            macd_data = TechnicalIndicators.calculate_macd(df['close'])
            result_df['macd_dif'] = macd_data['dif']
            result_df['macd_dea'] = macd_data['dea']
            result_df['macd'] = macd_data['macd']
            
            # RSI
            result_df['rsi'] = TechnicalIndicators.calculate_rsi(df['close'])
            
            # BOLL
            boll_data = TechnicalIndicators.calculate_boll(df['close'])
            result_df['boll_upper'] = boll_data['upper']
            result_df['boll_middle'] = boll_data['middle']
            result_df['boll_lower'] = boll_data['lower']
            
            # KDJ
            kdj_data = TechnicalIndicators.calculate_kdj(
                df['high'], df['low'], df['close']
            )
            result_df['kdj_k'] = kdj_data['k']
            result_df['kdj_d'] = kdj_data['d']
            result_df['kdj_j'] = kdj_data['j']
            
            # 成交量MA
            volume_ma = TechnicalIndicators.calculate_volume_ma(df['volume'])
            for key, value in volume_ma.items():
                result_df[f'volume_{key}'] = value
            
            logger.info(f"成功计算所有技术指标，数据行数: {len(result_df)}")
            return result_df
            
        except Exception as e:
            logger.error(f"计算所有技术指标失败: {str(e)}")
            return df
    
    @staticmethod
    def get_indicator_signals(df: pd.DataFrame) -> Dict[str, str]:
        """
        根据技术指标生成交易信号
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            包含各指标信号的字典
        """
        try:
            signals = {}
            
            if len(df) < 2:
                return signals
            
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # MACD信号
            if 'macd_dif' in df.columns and 'macd_dea' in df.columns:
                if latest['macd_dif'] > latest['macd_dea'] and previous['macd_dif'] <= previous['macd_dea']:
                    signals['macd'] = '金叉 (买入信号)'
                elif latest['macd_dif'] < latest['macd_dea'] and previous['macd_dif'] >= previous['macd_dea']:
                    signals['macd'] = '死叉 (卖出信号)'
                else:
                    signals['macd'] = '持有'
            
            # RSI信号
            if 'rsi' in df.columns:
                rsi_value = latest['rsi']
                if rsi_value < 30:
                    signals['rsi'] = '超卖 (买入信号)'
                elif rsi_value > 70:
                    signals['rsi'] = '超买 (卖出信号)'
                else:
                    signals['rsi'] = '正常'
            
            # BOLL信号
            if all(col in df.columns for col in ['close', 'boll_upper', 'boll_lower']):
                close = latest['close']
                if close > latest['boll_upper']:
                    signals['boll'] = '突破上轨 (超买)'
                elif close < latest['boll_lower']:
                    signals['boll'] = '突破下轨 (超卖)'
                else:
                    signals['boll'] = '正常区间'
            
            # KDJ信号
            if all(col in df.columns for col in ['kdj_k', 'kdj_d']):
                if latest['kdj_k'] > latest['kdj_d'] and previous['kdj_k'] <= previous['kdj_d']:
                    signals['kdj'] = '金叉 (买入信号)'
                elif latest['kdj_k'] < latest['kdj_d'] and previous['kdj_k'] >= previous['kdj_d']:
                    signals['kdj'] = '死叉 (卖出信号)'
                else:
                    signals['kdj'] = '持有'
            
            return signals
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {str(e)}")
            return {}
