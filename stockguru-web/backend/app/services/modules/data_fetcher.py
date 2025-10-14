"""
数据获取模块
负责从各种数据源获取股票数据
支持多数据源降级策略
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import requests
import json

# 尝试导入 akshare
try:
    import akshare as ak
except ImportError:
    ak = None

# 尝试导入 pywencai
try:
    import pywencai
except ImportError:
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
    
    def _fetch_from_eastmoney(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        从东方财富获取K线数据（备用数据源1）
        
        Args:
            code: 股票代码
            days: 天数
            
        Returns:
            K线数据DataFrame
        """
        try:
            self.logger.info(f"尝试从东方财富获取股票 {code} 的数据")
            
            # 东方财富API
            # 上证/深证代码需要加前缀
            if code.startswith('6'):
                secid = f'1.{code}'  # 上证
            else:
                secid = f'0.{code}'  # 深证
            
            url = 'http://push2his.eastmoney.com/api/qt/stock/kline/get'
            params = {
                'secid': secid,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K
                'fqt': '1',    # 前复权
                'end': '20500101',
                'lmt': days * 2,  # 多获取一些，确保有足够的交易日
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data') and data['data'].get('klines'):
                klines = data['data']['klines']
                
                # 解析数据
                records = []
                for kline in klines:
                    parts = kline.split(',')
                    if len(parts) >= 11:
                        records.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': float(parts[5]),
                            'amount': float(parts[6]),
                            'pct_change': float(parts[8])
                        })
                
                if records:
                    df = pd.DataFrame(records)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.tail(days)  # 只取最近N天
                    self.logger.info(f"成功从东方财富获取股票 {code} 的 {len(df)} 天数据")
                    return df
            
            self.logger.warning(f"东方财富未返回股票 {code} 的数据")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.warning(f"从东方财富获取股票 {code} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _fetch_from_sina(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        从新浪财经获取K线数据（备用数据源2）
        
        Args:
            code: 股票代码
            days: 天数
            
        Returns:
            K线数据DataFrame
        """
        try:
            self.logger.info(f"尝试从新浪财经获取股票 {code} 的数据")
            
            # 新浪财经API
            # 需要加市场前缀
            if code.startswith('6'):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days*2)
            
            url = f'https://quotes.sina.cn/cn/api/jsonp_v2.php/=/CN_MarketDataService.getKLineData'
            params = {
                'symbol': symbol,
                'scale': '240',  # 日K
                'datalen': days * 2,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析JSONP响应
            text = response.text
            if '=(' in text and text.endswith(');'):
                json_str = text.split('=(', 1)[1].rsplit(');', 1)[0]
                data = json.loads(json_str)
                
                if data:
                    records = []
                    for item in data:
                        records.append({
                            'date': item['day'],
                            'open': float(item['open']),
                            'close': float(item['close']),
                            'high': float(item['high']),
                            'low': float(item['low']),
                            'volume': float(item['volume']),
                            'amount': 0,  # 新浪不提供成交额
                            'pct_change': 0  # 需要计算
                        })
                    
                    if records:
                        df = pd.DataFrame(records)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date')
                        df = df.tail(days)
                        self.logger.info(f"成功从新浪财经获取股票 {code} 的 {len(df)} 天数据")
                        return df
            
            self.logger.warning(f"新浪财经未返回股票 {code} 的数据")
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.warning(f"从新浪财经获取股票 {code} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _generate_mock_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        生成模拟数据（最后的降级方案）
        
        Args:
            code: 股票代码
            days: 天数
            
        Returns:
            模拟的K线数据
        """
        try:
            self.logger.warning(f"使用模拟数据为股票 {code} 生成K线")
            
            # 生成日期序列（只包含工作日）
            end_date = datetime.now()
            all_dates = pd.date_range(end=end_date, periods=days*2, freq='D')
            dates = all_dates[all_dates.dayofweek < 5][:days]
            
            # 基础价格（根据股票代码生成）
            base_price = 10 + (int(code) % 100) / 10
            
            # 生成价格序列（随机游走）
            np.random.seed(int(code))
            returns = np.random.normal(0.001, 0.02, len(dates))
            prices = base_price * np.exp(np.cumsum(returns))
            
            # 生成OHLC数据
            records = []
            for i, date in enumerate(dates):
                close = prices[i]
                volatility = close * 0.02
                high = close + abs(np.random.normal(0, volatility))
                low = close - abs(np.random.normal(0, volatility))
                open_price = low + (high - low) * np.random.random()
                volume = np.random.randint(1000000, 10000000)
                
                records.append({
                    'date': date,
                    'open': round(open_price, 2),
                    'close': round(close, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'volume': volume,
                    'amount': volume * close,
                    'pct_change': returns[i] * 100
                })
            
            df = pd.DataFrame(records)
            self.logger.info(f"成功生成股票 {code} 的 {len(df)} 天模拟数据")
            return df
            
        except Exception as e:
            self.logger.error(f"生成模拟数据失败: {str(e)}")
            return pd.DataFrame()
    
    def get_stock_daily_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        获取股票日线数据（多数据源降级策略）
        
        数据源优先级:
        1. akshare (主数据源)
        2. 东方财富 (备用1)
        3. 新浪财经 (备用2)
        4. 模拟数据 (最后降级)
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            包含日线数据的DataFrame
        """
        self.logger.info(f"开始获取股票 {code} 的日线数据，使用多数据源降级策略")
        
        # 数据源列表
        data_sources = [
            ('akshare', self._fetch_from_akshare),
            ('东方财富', self._fetch_from_eastmoney),
            ('新浪财经', self._fetch_from_sina),
            ('模拟数据', self._generate_mock_data),
        ]
        
        # 按优先级尝试各个数据源
        for source_name, fetch_func in data_sources:
            try:
                self.logger.info(f"尝试从 {source_name} 获取数据")
                df = fetch_func(code, days)
                
                if not df.empty:
                    self.logger.info(f"✅ 成功从 {source_name} 获取股票 {code} 的 {len(df)} 天数据")
                    return df
                else:
                    self.logger.warning(f"❌ {source_name} 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                self.logger.warning(f"❌ {source_name} 获取失败: {str(e)}，尝试下一个数据源")
                continue
        
        # 所有数据源都失败
        self.logger.error(f"所有数据源都失败，无法获取股票 {code} 的数据")
        return pd.DataFrame()
    
    def _fetch_from_akshare(self, code: str, days: int = 60) -> pd.DataFrame:
        """
        从akshare获取K线数据（主数据源）
        
        Args:
            code: 股票代码
            days: 天数
            
        Returns:
            K线数据DataFrame
        """
        if ak is None:
            raise ImportError("akshare 未安装")
        
        # 只尝试1次，失败就切换到下一个数据源
        try:
            self.logger.debug(f"从 akshare 获取股票 {code} 的日线数据")
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust="qfq"  # 前复权
            )
            
            if df is None or df.empty:
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
            
            df = df.tail(days)
            return df
            
        except Exception as e:
            self.logger.warning(f"akshare 获取失败: {str(e)}")
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
            info = {
                'code': code,
                'name': '',
                'industry': '',
                'list_date': ''
            }
            
            # 优先从个股信息获取（最可靠的方法）
            try:
                stock_individual_info = ak.stock_individual_info_em(symbol=code)
                if stock_individual_info is not None and not stock_individual_info.empty:
                    # 获取股票名称
                    name_row = stock_individual_info[stock_individual_info['item'] == '股票简称']
                    if not name_row.empty:
                        info['name'] = str(name_row.iloc[0]['value']).strip()
                    
                    # 获取行业信息
                    industry_row = stock_individual_info[stock_individual_info['item'] == '行业']
                    if not industry_row.empty:
                        industry = str(industry_row.iloc[0]['value']).strip()
                        if industry and industry != '-' and industry != '未知':
                            info['industry'] = industry
                    
                    # 获取上市时间
                    list_date_row = stock_individual_info[stock_individual_info['item'] == '上市时间']
                    if not list_date_row.empty:
                        list_date = str(list_date_row.iloc[0]['value']).strip()
                        if list_date and list_date != '-':
                            info['list_date'] = list_date
            except Exception as e:
                self.logger.warning(f"从个股信息获取失败: {str(e)}")
            
            # 如果还没有名称，尝试从实时行情中获取
            if not info['name']:
                try:
                    realtime_df = ak.stock_zh_a_spot_em()
                    stock_row = realtime_df[realtime_df['代码'] == code]
                    if not stock_row.empty:
                        info['name'] = stock_row.iloc[0]['名称']
                        # 尝试获取行业信息
                        if not info['industry'] and '行业' in stock_row.columns:
                            industry = stock_row.iloc[0]['行业']
                            if pd.notna(industry) and str(industry).strip():
                                info['industry'] = str(industry).strip()
                except Exception as e:
                    self.logger.warning(f"从实时行情获取信息失败: {str(e)}")
            
            
            # 如果所有方法都失败，设置为未知
            if not info['industry']:
                info['industry'] = '未知'
            
            self.logger.info(f"获取股票 {code} 信息: name={info['name']}, industry={info['industry']}")
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
