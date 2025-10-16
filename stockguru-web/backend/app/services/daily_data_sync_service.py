"""
每日股票数据同步服务
负责从数据源同步全市场A股的每日交易数据
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

# 尝试导入 akshare
try:
    import akshare as ak
except ImportError:
    ak = None
    logger.warning("akshare 未安装")


class DailyDataSyncService:
    """每日数据同步服务"""
    
    def __init__(self):
        """初始化同步服务"""
        if ak is None:
            raise ImportError("akshare 未安装，请运行: pip install akshare")
        
        self.logger = logging.getLogger(__name__)
    
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
        
        Args:
            check_date: 要检查的日期
            
        Returns:
            是否为交易日
        """
        try:
            # 获取交易日历
            tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
            
            # 转换日期格式
            trade_dates = pd.to_datetime(tool_trade_date_hist_sina_df['trade_date']).dt.date
            
            return check_date in trade_dates.values
            
        except Exception as e:
            self.logger.error(f"判断交易日失败: {e}")
            # 简单判断：周一到周五
            return check_date.weekday() < 5
    
    def get_all_stock_codes(self) -> List[Dict[str, str]]:
        """
        获取所有A股股票代码列表
        
        Returns:
            股票代码和名称列表
        """
        try:
            self.logger.info("获取全市场A股列表...")
            
            # 获取沪深A股列表
            stock_info_a_code_name_df = ak.stock_info_a_code_name()
            
            stocks = []
            for _, row in stock_info_a_code_name_df.iterrows():
                stocks.append({
                    'code': str(row['code']),
                    'name': str(row['name'])
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
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取单只股票的日线数据
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            日线数据 DataFrame
        """
        try:
            # 使用 akshare 获取前复权日线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                return None
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open_price',
                '收盘': 'close_price',
                '最高': 'high_price',
                '最低': 'low_price',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change_amount',
                '换手率': 'turnover_rate',
                '振幅': 'amplitude'
            })
            
            # 添加股票信息
            df['stock_code'] = stock_code
            df['stock_name'] = stock_name
            
            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
            
            return df
            
        except Exception as e:
            self.logger.warning(f"获取股票 {stock_code} {stock_name} 数据失败: {e}")
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
        
        try:
            log_response = supabase.table('sync_logs').insert(log_data).execute()
            log_id = log_response.data[0]['id']
        except Exception as e:
            self.logger.error(f"创建同步日志失败: {e}")
            log_id = None
        
        try:
            self.logger.info(f"开始同步 {sync_date} 的数据...")
            
            # 获取所有股票代码
            stocks = self.get_all_stock_codes()
            total_stocks = len(stocks)
            
            if log_id:
                supabase.table('sync_logs').update({
                    'total_stocks': total_stocks
                }).eq('id', log_id).execute()
            
            # 格式化日期
            date_str = sync_date.strftime('%Y%m%d')
            
            # 并发获取数据
            success_count = 0
            failed_count = 0
            all_data = []
            
            def fetch_wrapper(stock):
                return self.fetch_stock_daily_data(
                    stock['code'], 
                    stock['name'],
                    date_str, 
                    date_str
                )
            
            # 使用线程池并发获取（限制并发数避免被限流）
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(fetch_wrapper, stock) for stock in stocks]
                
                for i, future in enumerate(futures):
                    try:
                        df = future.result(timeout=10)
                        if df is not None and not df.empty:
                            all_data.append(df)
                            success_count += 1
                        else:
                            failed_count += 1
                        
                        # 每100只股票记录一次进度
                        if (i + 1) % 100 == 0:
                            self.logger.info(f"进度: {i + 1}/{total_stocks}")
                        
                        # 添加延迟避免限流
                        if (i + 1) % 50 == 0:
                            time.sleep(2)
                            
                    except Exception as e:
                        failed_count += 1
                        self.logger.warning(f"处理股票失败: {e}")
            
            # 合并所有数据
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # 转换为字典列表
                records = combined_df.to_dict('records')
                
                # 批量插入数据库（分批处理，每批1000条）
                batch_size = 1000
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    try:
                        supabase.table('daily_stock_data').upsert(batch).execute()
                        self.logger.info(f"插入数据: {i + batch_size}/{len(records)}")
                    except Exception as e:
                        self.logger.error(f"插入数据失败: {e}")
            
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
_sync_service = None

def get_sync_service() -> DailyDataSyncService:
    """获取同步服务实例"""
    global _sync_service
    if _sync_service is None:
        _sync_service = DailyDataSyncService()
    return _sync_service
