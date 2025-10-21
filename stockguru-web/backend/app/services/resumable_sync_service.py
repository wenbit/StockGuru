"""
支持断点续传的同步服务
实现进度记录、失败重试、断点续传等功能
"""

import os
import logging
import baostock as bs
from datetime import date, datetime
from typing import List, Dict, Tuple, Optional
from app.core.database import DatabaseConnection

logger = logging.getLogger(__name__)


class ResumableSyncService:
    """支持断点续传的同步服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bs_logged_in = False
    
    def _ensure_bs_login(self):
        """确保baostock已登录"""
        if not self.bs_logged_in:
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"Baostock登录失败: {lg.error_msg}")
            self.bs_logged_in = True
            self.logger.info("Baostock登录成功")
    
    def _bs_logout(self):
        """登出baostock"""
        if self.bs_logged_in:
            bs.logout()
            self.bs_logged_in = False
            self.logger.info("Baostock已登出")
    
    def get_all_stock_codes(self) -> List[Dict]:
        """获取所有A股代码"""
        self._ensure_bs_login()
        
        stocks = []
        rs = bs.query_stock_basic()
        
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            code = row[0]  # 股票代码
            name = row[2]  # 股票名称
            
            # 只要A股（sh/sz开头）
            if code.startswith('sh.') or code.startswith('sz.'):
                stocks.append({
                    'code': code,
                    'name': name
                })
        
        self.logger.info(f"获取到 {len(stocks)} 只A股")
        return stocks
    
    def init_progress(self, sync_date: date) -> int:
        """
        初始化同步进度记录
        
        Args:
            sync_date: 同步日期
            
        Returns:
            初始化的股票数量
        """
        try:
            # 获取所有股票
            stocks = self.get_all_stock_codes()
            
            with DatabaseConnection() as cursor:
                # 批量插入进度记录（如果不存在）
                for stock in stocks:
                    cursor.execute("""
                        INSERT INTO sync_progress (sync_date, stock_code, stock_name, status)
                        VALUES (%s, %s, %s, 'pending')
                        ON CONFLICT (sync_date, stock_code) DO NOTHING
                    """, (sync_date, stock['code'], stock['name']))
                
                # 统计待同步数量
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM sync_progress
                    WHERE sync_date = %s AND status = 'pending'
                """, (sync_date,))
                
                result = cursor.fetchone()
                pending_count = result['count']
                
                self.logger.info(f"{sync_date}: 初始化完成，待同步 {pending_count} 只股票")
                return pending_count
                
        except Exception as e:
            self.logger.error(f"初始化进度失败: {e}", exc_info=True)
            raise
    
    def get_progress(self, sync_date: date) -> Dict:
        """
        获取同步进度
        
        Args:
            sync_date: 同步日期
            
        Returns:
            进度信息
        """
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'success') as success,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending
                    FROM sync_progress
                    WHERE sync_date = %s
                """, (sync_date,))
                
                result = cursor.fetchone()
                
                if not result or result['total'] == 0:
                    return {
                        'total': 0,
                        'success': 0,
                        'failed': 0,
                        'pending': 0,
                        'progress': 0.0
                    }
                
                total = result['total']
                success = result['success']
                failed = result['failed']
                pending = result['pending']
                
                progress = (success / total * 100) if total > 0 else 0.0
                
                return {
                    'total': total,
                    'success': success,
                    'failed': failed,
                    'pending': pending,
                    'progress': round(progress, 2)
                }
                
        except Exception as e:
            self.logger.error(f"获取进度失败: {e}", exc_info=True)
            return {'total': 0, 'success': 0, 'failed': 0, 'pending': 0, 'progress': 0.0}
    
    def get_pending_stocks(self, sync_date: date, limit: int = None) -> List[Dict]:
        """
        获取待同步的股票列表
        
        Args:
            sync_date: 同步日期
            limit: 限制数量
            
        Returns:
            待同步股票列表
        """
        try:
            with DatabaseConnection() as cursor:
                sql = """
                    SELECT stock_code, stock_name, retry_count
                    FROM sync_progress
                    WHERE sync_date = %s AND status = 'pending'
                    ORDER BY retry_count ASC, stock_code ASC
                """
                
                if limit:
                    sql += f" LIMIT {limit}"
                
                cursor.execute(sql, (sync_date,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取待同步股票失败: {e}", exc_info=True)
            return []
    
    def get_failed_stocks(self, sync_date: date) -> List[Dict]:
        """获取失败的股票列表"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    SELECT stock_code, stock_name, error_message, retry_count
                    FROM sync_progress
                    WHERE sync_date = %s AND status = 'failed'
                    ORDER BY retry_count ASC
                """, (sync_date,))
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取失败股票失败: {e}", exc_info=True)
            return []
    
    def fetch_stock_data(self, stock_code: str, date_str: str) -> Optional[Dict]:
        """
        获取单只股票的日线数据
        
        Args:
            stock_code: 股票代码（如 sh.600000）
            date_str: 日期字符串（YYYY-MM-DD）
            
        Returns:
            股票数据字典
        """
        try:
            self._ensure_bs_login()
        except Exception as e:
            self.logger.error(f"Baostock登录失败: {e}")
            return None
        
        try:
            # 转换日期格式
            date_baostock = date_str.replace('-', '')
            
            # 查询日线数据
            rs = bs.query_history_k_data_plus(
                stock_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=date_baostock,
                end_date=date_baostock,
                frequency="d",
                adjustflag="3"  # 不复权
            )
            
            if rs is None or not hasattr(rs, 'error_code'):
                self.logger.warning(f"查询返回空结果 {stock_code}")
                return None
            
            if rs.error_code != '0':
                self.logger.warning(f"查询失败 {stock_code}: {rs.error_msg}")
                return None
            
            # 获取数据
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return None
            
            # 解析数据
            row = data_list[0]
            return {
                'trade_date': row[0],
                'stock_code': row[1].split('.')[1],  # 去掉sh./sz.前缀
                'open_price': float(row[2]) if row[2] else None,
                'high_price': float(row[3]) if row[3] else None,
                'low_price': float(row[4]) if row[4] else None,
                'close_price': float(row[5]) if row[5] else None,
                'volume': int(float(row[6])) if row[6] else None,
                'amount': float(row[7]) if row[7] else None,
                'turnover_rate': float(row[8]) if row[8] else None,
                'change_pct': float(row[9]) if row[9] else None,
            }
            
        except Exception as e:
            self.logger.warning(f"获取股票 {stock_code} 数据失败: {e}")
            return None
    
    def save_stock_data(self, sync_date: date, stock_code: str, data: Dict) -> bool:
        """
        保存股票数据到数据库
        
        Args:
            sync_date: 同步日期
            stock_code: 股票代码
            data: 股票数据
            
        Returns:
            是否成功
        """
        try:
            with DatabaseConnection() as cursor:
                # 插入或更新股票数据
                cursor.execute("""
                    INSERT INTO daily_stock_data 
                    (stock_code, stock_name, trade_date, open_price, close_price, 
                     high_price, low_price, volume, amount, change_pct, turnover_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (stock_code, trade_date) 
                    DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        close_price = EXCLUDED.close_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        volume = EXCLUDED.volume,
                        amount = EXCLUDED.amount,
                        change_pct = EXCLUDED.change_pct,
                        turnover_rate = EXCLUDED.turnover_rate,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    data['stock_code'],
                    data.get('stock_name', ''),
                    data['trade_date'],
                    data.get('open_price'),
                    data.get('close_price'),
                    data.get('high_price'),
                    data.get('low_price'),
                    data.get('volume'),
                    data.get('amount'),
                    data.get('change_pct'),
                    data.get('turnover_rate')
                ))
                
                return True
                
        except Exception as e:
            self.logger.error(f"保存股票数据失败 {stock_code}: {e}", exc_info=True)
            return False
    
    def mark_stock_success(self, sync_date: date, stock_code: str):
        """标记股票同步成功"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE sync_progress
                    SET status = 'success',
                        synced_at = CURRENT_TIMESTAMP,
                        error_message = NULL
                    WHERE sync_date = %s AND stock_code = %s
                """, (sync_date, stock_code))
        except Exception as e:
            self.logger.error(f"标记成功失败 {stock_code}: {e}")
    
    def mark_stock_failed(self, sync_date: date, stock_code: str, error_msg: str):
        """标记股票同步失败"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE sync_progress
                    SET status = 'failed',
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE sync_date = %s AND stock_code = %s
                """, (error_msg, sync_date, stock_code))
        except Exception as e:
            self.logger.error(f"标记失败失败 {stock_code}: {e}")
    
    def reset_failed_to_pending(self, sync_date: date) -> int:
        """
        将失败的股票重置为待同步状态
        
        Args:
            sync_date: 同步日期
            
        Returns:
            重置的数量
        """
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE sync_progress
                    SET status = 'pending',
                        error_message = NULL
                    WHERE sync_date = %s AND status = 'failed'
                    RETURNING stock_code
                """, (sync_date,))
                
                count = len(cursor.fetchall())
                self.logger.info(f"{sync_date}: 重置 {count} 只失败股票为待同步")
                return count
                
        except Exception as e:
            self.logger.error(f"重置失败股票失败: {e}", exc_info=True)
            return 0
    
    def clear_progress(self, sync_date: date):
        """清除指定日期的进度记录"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    DELETE FROM sync_progress
                    WHERE sync_date = %s
                """, (sync_date,))
                self.logger.info(f"{sync_date}: 进度记录已清除")
        except Exception as e:
            self.logger.error(f"清除进度记录失败: {e}", exc_info=True)
    
    def sync_with_resume(self, sync_date: date, batch_size: int = 50, 
                        max_retries: int = 3) -> Dict:
        """
        执行断点续传同步
        
        Args:
            sync_date: 同步日期
            batch_size: 每批处理数量
            max_retries: 最大重试次数
            
        Returns:
            同步结果
        """
        date_str = sync_date.strftime('%Y-%m-%d')
        self.logger.info(f"开始同步 {date_str}（支持断点续传）")
        
        try:
            self._ensure_bs_login()
            
            # 1. 检查是否已初始化
            progress = self.get_progress(sync_date)
            if progress['total'] == 0:
                self.logger.info("首次同步，初始化进度记录...")
                self.init_progress(sync_date)
                progress = self.get_progress(sync_date)
            else:
                self.logger.info(f"继续上次同步: 总数={progress['total']}, "
                               f"成功={progress['success']}, "
                               f"失败={progress['failed']}, "
                               f"待同步={progress['pending']}")
            
            # 2. 获取待同步股票
            pending_stocks = self.get_pending_stocks(sync_date)
            
            if not pending_stocks:
                self.logger.info("没有待同步的股票")
                return {
                    'status': 'success',
                    'date': date_str,
                    'total': progress['total'],
                    'success': progress['success'],
                    'failed': progress['failed'],
                    'message': '所有股票已同步完成'
                }
            
            # 3. 分批同步
            total_pending = len(pending_stocks)
            processed = 0
            success_count = 0
            failed_count = 0
            
            for i in range(0, total_pending, batch_size):
                batch = pending_stocks[i:i + batch_size]
                
                for stock in batch:
                    stock_code = stock['stock_code']
                    stock_name = stock['stock_name']
                    retry_count = stock['retry_count']
                    
                    # 超过最大重试次数，跳过
                    if retry_count >= max_retries:
                        self.logger.warning(f"跳过 {stock_code}（已重试{retry_count}次）")
                        continue
                    
                    # 获取数据
                    data = self.fetch_stock_data(stock_code, date_str)
                    
                    if data:
                        # 添加股票名称
                        data['stock_name'] = stock_name
                        
                        # 保存数据
                        if self.save_stock_data(sync_date, stock_code, data):
                            self.mark_stock_success(sync_date, stock_code)
                            success_count += 1
                        else:
                            self.mark_stock_failed(sync_date, stock_code, "保存数据失败")
                            failed_count += 1
                    else:
                        self.mark_stock_failed(sync_date, stock_code, "获取数据失败或无数据")
                        failed_count += 1
                    
                    processed += 1
                    
                    # 每100只打印一次进度
                    if processed % 100 == 0:
                        current_progress = self.get_progress(sync_date)
                        self.logger.info(
                            f"进度: {processed}/{total_pending} "
                            f"(成功:{current_progress['success']}, "
                            f"失败:{current_progress['failed']}, "
                            f"完成度:{current_progress['progress']:.1f}%)"
                        )
            
            # 4. 最终统计
            final_progress = self.get_progress(sync_date)
            
            self.logger.info(
                f"同步完成: 总数={final_progress['total']}, "
                f"成功={final_progress['success']}, "
                f"失败={final_progress['failed']}, "
                f"待同步={final_progress['pending']}"
            )
            
            return {
                'status': 'success' if final_progress['pending'] == 0 else 'partial',
                'date': date_str,
                'total': final_progress['total'],
                'success': final_progress['success'],
                'failed': final_progress['failed'],
                'pending': final_progress['pending'],
                'progress': final_progress['progress'],
                'message': f"本次处理 {processed} 只，成功 {success_count}，失败 {failed_count}"
            }
            
        except Exception as e:
            self.logger.error(f"同步失败: {e}", exc_info=True)
            return {
                'status': 'error',
                'date': date_str,
                'error': str(e)
            }
        finally:
            self._bs_logout()


# 全局实例
_resumable_sync_service = None

def get_resumable_sync_service() -> ResumableSyncService:
    """获取断点续传同步服务实例"""
    global _resumable_sync_service
    if _resumable_sync_service is None:
        _resumable_sync_service = ResumableSyncService()
    return _resumable_sync_service
