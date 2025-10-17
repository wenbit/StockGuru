"""
增量同步服务
只同步变化的数据，避免重复同步
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


class IncrementalSyncService:
    """增量同步服务"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)
        
        # 创建连接池
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=database_url
            )
        except Exception as e:
            self.logger.error(f"创建连接池失败: {e}")
            self.connection_pool = None
    
    def get_missing_dates(self, start_date: date, end_date: date) -> List[date]:
        """
        获取缺失的交易日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            缺失的日期列表
        """
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # 查询已有的日期
            cursor.execute("""
                SELECT DISTINCT trade_date 
                FROM daily_stock_data
                WHERE trade_date BETWEEN %s AND %s
                ORDER BY trade_date
            """, (start_date, end_date))
            
            existing_dates = {row[0] for row in cursor.fetchall()}
            
            # 生成所有日期
            all_dates = []
            current = start_date
            while current <= end_date:
                all_dates.append(current)
                current += timedelta(days=1)
            
            # 找出缺失的日期
            missing_dates = [d for d in all_dates if d not in existing_dates]
            
            self.connection_pool.putconn(conn)
            
            self.logger.info(f"日期范围: {start_date} 到 {end_date}")
            self.logger.info(f"已有日期: {len(existing_dates)} 天")
            self.logger.info(f"缺失日期: {len(missing_dates)} 天")
            
            return missing_dates
            
        except Exception as e:
            self.logger.error(f"获取缺失日期失败: {e}")
            return []
    
    def get_incomplete_dates(self, min_stocks: int = 2000) -> List[date]:
        """
        获取数据不完整的日期（股票数量少于阈值）
        
        Args:
            min_stocks: 最小股票数量阈值
            
        Returns:
            数据不完整的日期列表
        """
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # 查询每日股票数量
            cursor.execute("""
                SELECT trade_date, COUNT(*) as stock_count
                FROM daily_stock_data
                GROUP BY trade_date
                HAVING COUNT(*) < %s
                ORDER BY trade_date DESC
                LIMIT 30
            """, (min_stocks,))
            
            incomplete_dates = [row[0] for row in cursor.fetchall()]
            
            self.connection_pool.putconn(conn)
            
            if incomplete_dates:
                self.logger.warning(f"发现 {len(incomplete_dates)} 个数据不完整的日期")
                for d in incomplete_dates[:5]:
                    self.logger.warning(f"  - {d}")
            
            return incomplete_dates
            
        except Exception as e:
            self.logger.error(f"获取不完整日期失败: {e}")
            return []
    
    def get_last_sync_date(self) -> Optional[date]:
        """
        获取最后同步日期
        
        Returns:
            最后同步的日期
        """
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(trade_date) 
                FROM daily_stock_data
            """)
            
            result = cursor.fetchone()
            last_date = result[0] if result and result[0] else None
            
            self.connection_pool.putconn(conn)
            
            if last_date:
                self.logger.info(f"最后同步日期: {last_date}")
            else:
                self.logger.warning("数据库中无数据")
            
            return last_date
            
        except Exception as e:
            self.logger.error(f"获取最后同步日期失败: {e}")
            return None
    
    def get_sync_strategy(self) -> Dict:
        """
        获取智能同步策略
        
        Returns:
            同步策略字典
        """
        last_sync = self.get_last_sync_date()
        today = date.today()
        
        if not last_sync:
            # 首次同步：同步最近30天
            return {
                'strategy': 'initial',
                'dates': [today - timedelta(days=i) for i in range(30, 0, -1)],
                'reason': '首次同步，获取最近30天数据'
            }
        
        # 检查缺失日期
        missing_dates = self.get_missing_dates(last_sync, today)
        
        if missing_dates:
            return {
                'strategy': 'fill_missing',
                'dates': missing_dates,
                'reason': f'补充缺失的 {len(missing_dates)} 个日期'
            }
        
        # 检查不完整日期
        incomplete_dates = self.get_incomplete_dates()
        
        if incomplete_dates:
            return {
                'strategy': 'fix_incomplete',
                'dates': incomplete_dates,
                'reason': f'修复 {len(incomplete_dates)} 个数据不完整的日期'
            }
        
        # 正常增量同步
        days_behind = (today - last_sync).days
        
        if days_behind > 0:
            sync_dates = [last_sync + timedelta(days=i) for i in range(1, days_behind + 1)]
            return {
                'strategy': 'incremental',
                'dates': sync_dates,
                'reason': f'增量同步最近 {days_behind} 天'
            }
        
        return {
            'strategy': 'up_to_date',
            'dates': [],
            'reason': '数据已是最新'
        }
    
    def get_data_quality_report(self) -> Dict:
        """
        获取数据质量报告
        
        Returns:
            数据质量报告
        """
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
            total_records = cursor.fetchone()[0]
            
            # 日期范围
            cursor.execute("""
                SELECT MIN(trade_date), MAX(trade_date), COUNT(DISTINCT trade_date)
                FROM daily_stock_data
            """)
            min_date, max_date, date_count = cursor.fetchone()
            
            # 平均每日股票数
            cursor.execute("""
                SELECT AVG(stock_count)::INT
                FROM (
                    SELECT COUNT(*) as stock_count
                    FROM daily_stock_data
                    GROUP BY trade_date
                ) sub
            """)
            avg_stocks_per_day = cursor.fetchone()[0]
            
            # 数据完整性
            cursor.execute("""
                SELECT trade_date, COUNT(*) as stock_count
                FROM daily_stock_data
                GROUP BY trade_date
                HAVING COUNT(*) < 2000
                ORDER BY trade_date DESC
                LIMIT 10
            """)
            incomplete_dates = cursor.fetchall()
            
            self.connection_pool.putconn(conn)
            
            return {
                'total_records': total_records,
                'date_range': {
                    'start': min_date,
                    'end': max_date,
                    'days': date_count
                },
                'avg_stocks_per_day': avg_stocks_per_day,
                'incomplete_dates': [
                    {'date': str(d), 'count': c} 
                    for d, c in incomplete_dates
                ],
                'quality_score': 100 if not incomplete_dates else 80
            }
            
        except Exception as e:
            self.logger.error(f"获取数据质量报告失败: {e}")
            return {}
