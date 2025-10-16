"""
每日股票数据同步服务 V2
使用 baostock 作为主要数据源（免费、稳定、无限流）
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# 尝试导入 baostock
try:
    import baostock as bs
except ImportError:
    bs = None
    logger.warning("baostock 未安装")


class DailyDataSyncServiceV2:
    """每日数据同步服务 V2 - 使用 baostock"""
    
    def __init__(self):
        """初始化同步服务"""
        if bs is None:
            raise ImportError("baostock 未安装，请运行: pip install baostock")
        
        self.logger = logging.getLogger(__name__)
        self.bs_logged_in = False
    
    def _login_baostock(self):
        """登录 baostock"""
        if not self.bs_logged_in:
            lg = bs.login()
            if lg.error_code != '0':
                self.logger.error(f"baostock 登录失败: {lg.error_msg}")
                return False
            self.bs_logged_in = True
            self.logger.info("baostock 登录成功")
        return True
    
    def _logout_baostock(self):
        """登出 baostock"""
        if self.bs_logged_in:
            bs.logout()
            self.bs_logged_in = False
    
    def _get_supabase(self):
        """获取 Supabase 客户端"""
        try:
            from app.core.supabase import get_supabase_client
            return get_supabase_client()
        except Exception as e:
            self.logger.error(f"Supabase 连接失败: {e}")
            return None
    
    def is_trading_day(self, check_date: date) -> bool:
        """
        判断是否为交易日
        简单判断：周一到周五
        """
        return check_date.weekday() < 5
    
    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """
        获取所有A股股票代码列表
        
        Returns:
            股票代码和名称列表
        """
        try:
            if not self._login_baostock():
                return []
            
            self.logger.info("获取全市场A股列表...")
            
            # 获取沪深A股列表
            rs = bs.query_stock_basic()
            
            stocks = []
            while (rs.error_code == '0') & rs.next():
                row = rs.get_row_data()
                # row[0]: code, row[1]: code_name, row[2]: ipoDate, row[3]: outDate, row[4]: type, row[5]: status
                code = row[0]  # 格式如 sh.600000 或 sz.000001
                name = row[1]
                stock_type = row[4]
                status = row[5]
                
                # 只获取A股且状态为1（正常上市）
                if stock_type == '1' and status == '1':
                    # 转换代码格式：sh.600000 -> 600000
                    simple_code = code.split('.')[1] if '.' in code else code
                    stocks.append({
                        'code': simple_code,
                        'name': name,
                        'full_code': code  # 保留完整代码用于查询
                    })
            
            self.logger.info(f"获取到 {len(stocks)} 只A股")
            return stocks
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
    
    def fetch_stock_daily_data(
        self, 
        stock_code: str,
        stock_name: str,
        full_code: str,
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取单只股票的日线数据
        
        Args:
            stock_code: 股票代码（如 000001）
            stock_name: 股票名称
            full_code: 完整代码（如 sz.000001）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日线数据 DataFrame
        """
        try:
            # 使用 baostock 获取日线数据（已在开始时登录）
            rs = bs.query_history_k_data_plus(
                full_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"  # 2: 前复权
            )
            
            if rs.error_code != '0':
                return None
            
            # 转换为 DataFrame
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return None
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            if df.empty:
                return None
            
            # 数据类型转换
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df['turn'] = pd.to_numeric(df['turn'], errors='coerce')
            df['pctChg'] = pd.to_numeric(df['pctChg'], errors='coerce')
            
            # 标准化列名
            df = df.rename(columns={
                'date': 'trade_date',
                'open': 'open_price',
                'close': 'close_price',
                'high': 'high_price',
                'low': 'low_price',
                'volume': 'volume',
                'amount': 'amount',
                'pctChg': 'change_pct',
                'turn': 'turnover_rate'
            })
            
            # 添加股票信息
            df['stock_code'] = stock_code
            df['stock_name'] = stock_name
            
            # 计算涨跌额
            df['change_amount'] = df['close_price'] - df['close_price'].shift(1)
            
            # 计算振幅
            df['amplitude'] = ((df['high_price'] - df['low_price']) / df['close_price'].shift(1) * 100).round(2)
            
            # 转换日期格式为字符串（JSON 可序列化）
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
            
            # 选择需要的列
            df = df[[
                'stock_code', 'stock_name', 'trade_date',
                'open_price', 'close_price', 'high_price', 'low_price',
                'volume', 'amount', 'change_pct', 'change_amount',
                'turnover_rate', 'amplitude'
            ]]
            
            # 处理 NaN/Inf 值（替换为 None，Supabase JSON 可序列化）
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"获取股票 {stock_code} {stock_name} 数据失败: {e}")
            return None

    def _fetch_stock_with_retry(self, stock: Dict[str, str], date_str: str, retries: int = 2, delay: float = 0.1) -> Optional[pd.DataFrame]:
        """带重试地获取单只股票数据"""
        for attempt in range(1, retries + 1):
            df = None
            try:
                df = self.fetch_stock_daily_data(
                    stock['code'],
                    stock['name'],
                    stock['full_code'],
                    date_str,
                    date_str
                )
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                if attempt == retries:
                    self.logger.debug(f"获取 {stock['code']} 数据失败 (尝试 {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
        return None
    
    async def sync_date_data(self, sync_date: date) -> Dict:
        """
        同步指定日期的数据
        
        Args:
            sync_date: 要同步的日期
            
        Returns:
            同步结果
        """
        supabase = self._get_supabase()
        if not supabase:
            raise Exception("Supabase 未连接")
        
        # 检查是否为交易日
        if not self.is_trading_day(sync_date):
            self.logger.info(f"{sync_date} 不是交易日，跳过同步")
            return {
                'date': sync_date.isoformat(),
                'status': 'skipped',
                'message': '非交易日'
            }
        
        # 创建同步日志
        log_data = {
            'sync_date': sync_date.isoformat(),
            'sync_type': 'daily',
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        log_id = None
        try:
            log_response = supabase.table('sync_logs').insert(log_data).execute()
            log_id = log_response.data[0]['id']
        except Exception as e:
            self.logger.error(f"创建同步日志失败: {e}")
        
        try:
            self.logger.info(f"开始同步 {sync_date} 的数据...")
            
            # 获取所有股票代码
            stocks = self.get_all_stock_codes()
            total_stocks = len(stocks)
            
            if log_id:
                supabase.table('sync_logs').update({
                    'total_stocks': total_stocks
                }).eq('id', log_id).execute()
            
            date_str = sync_date.strftime('%Y-%m-%d')
            
            success_count = 0
            failed_count = 0
            batch_frames: List[pd.DataFrame] = []
            batch_size = 500  # 增大批次，减少入库次数
            total_inserted = 0

            self.logger.info(f"开始串行获取数据（baostock 不支持多线程）, batch_size={batch_size}")

            for idx, stock in enumerate(stocks, start=1):
                df = self._fetch_stock_with_retry(stock, date_str, retries=1)

                if df is not None and not df.empty:
                    batch_frames.append(df)
                    success_count += 1
                else:
                    failed_count += 1

                # 批量入库
                if batch_frames and (len(batch_frames) >= batch_size or idx == total_stocks):
                    try:
                        batch_df = pd.concat(batch_frames, ignore_index=True)
                        records = batch_df.to_dict('records')
                        supabase.table('daily_stock_data').upsert(records).execute()
                        total_inserted += len(records)
                    except Exception as insert_err:
                        self.logger.error(f"入库失败（批次大小 {len(batch_frames)}）: {insert_err}")
                    finally:
                        batch_frames = []

                # 进度日志（减少输出频率）
                if idx % 500 == 0 or idx == total_stocks:
                    self.logger.info(
                        f"进度: {idx}/{total_stocks}, 成功: {success_count}, 失败: {failed_count}, 已入库: {total_inserted}"
                    )

            # 登出 baostock
            self._logout_baostock()

            self.logger.info(
                f"最终进度: {total_stocks}/{total_stocks}, 成功: {success_count}, 失败: {failed_count}, 已入库: {total_inserted}"
            )

            # 更新同步日志
            if log_id:
                supabase.table('sync_logs').update({
                    'status': 'success',
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'completed_at': datetime.now().isoformat()
                }).eq('id', log_id).execute()
            
            self.logger.info(f"同步完成: 成功 {success_count}, 失败 {failed_count}")
            
            return {
                'date': sync_date.isoformat(),
                'status': 'success',
                'total': total_stocks,
                'success': success_count,
                'failed': failed_count
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"同步失败: {error_msg}")
            
            # 登出 baostock
            self._logout_baostock()
            
            # 更新失败状态
            if log_id:
                supabase.table('sync_logs').update({
                    'status': 'failed',
                    'error_message': error_msg,
                    'completed_at': datetime.now().isoformat()
                }).eq('id', log_id).execute()
            
            raise
    
    async def sync_historical_data(self, days: int = 90) -> Dict:
        """
        同步历史数据（初始化用）
        
        Args:
            days: 同步最近N天的数据
            
        Returns:
            同步结果
        """
        self.logger.info(f"开始同步最近 {days} 天的历史数据...")
        
        results = []
        today = date.today()
        
        for i in range(days):
            sync_date = today - timedelta(days=i)
            
            try:
                result = await self.sync_date_data(sync_date)
                results.append(result)
                
                # 避免请求过快
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"同步 {sync_date} 失败: {e}")
                results.append({
                    'date': sync_date.isoformat(),
                    'status': 'failed',
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return {
            'total_days': days,
            'success_days': success_count,
            'results': results
        }


# 全局实例
_sync_service_v2 = None

def get_sync_service_v2() -> DailyDataSyncServiceV2:
    """获取同步服务实例 V2"""
    global _sync_service_v2
    if _sync_service_v2 is None:
        _sync_service_v2 = DailyDataSyncServiceV2()
    return _sync_service_v2
