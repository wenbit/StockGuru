#!/usr/bin/env python3
"""
交易日历工具
支持多种方式判断交易日
"""

import logging
from datetime import datetime, date
from typing import Optional
import psycopg2

logger = logging.getLogger(__name__)


class TradingCalendar:
    """交易日历"""
    
    def __init__(self, method: str = 'simple', db_conn=None):
        """
        初始化
        
        Args:
            method: 判断方式 ('simple', 'calendar', 'database')
            db_conn: 数据库连接（method='database'时需要）
        """
        self.method = method
        self.db_conn = db_conn
        
        # 尝试导入 chinese_calendar
        self.chinese_calendar = None
        if method == 'calendar':
            try:
                import chinese_calendar
                self.chinese_calendar = chinese_calendar
                logger.info("使用 chinese_calendar 库判断交易日")
            except ImportError:
                logger.warning("chinese_calendar 未安装，回退到简单判断")
                self.method = 'simple'
    
    def is_trading_day(self, date_str: str) -> bool:
        """
        判断是否为交易日
        
        Args:
            date_str: 日期字符串 'YYYY-MM-DD'
        
        Returns:
            是否为交易日
        """
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"日期格式错误: {date_str}, {e}")
            return False
        
        if self.method == 'database':
            return self._is_trading_day_database(date_str)
        elif self.method == 'calendar' and self.chinese_calendar:
            return self._is_trading_day_calendar(date_obj)
        else:
            return self._is_trading_day_simple(date_obj)
    
    def _is_trading_day_simple(self, date_obj: date) -> bool:
        """
        简单判断：非周末即为交易日
        
        注意：此方法无法识别节假日
        """
        # 0=周一, 6=周日
        is_weekday = date_obj.weekday() < 5
        
        if not is_weekday:
            logger.debug(f"{date_obj} 是周末")
        
        return is_weekday
    
    def _is_trading_day_calendar(self, date_obj: date) -> bool:
        """
        使用 chinese_calendar 库判断
        
        优点：可以识别法定节假日和调休
        缺点：需要安装第三方库
        """
        try:
            is_workday = self.chinese_calendar.is_workday(date_obj)
            
            if not is_workday:
                # 判断是周末还是节假日
                if date_obj.weekday() >= 5:
                    logger.debug(f"{date_obj} 是周末")
                else:
                    holiday_name = self.chinese_calendar.get_holiday_detail(date_obj)
                    logger.debug(f"{date_obj} 是节假日: {holiday_name}")
            
            return is_workday
        except Exception as e:
            logger.warning(f"chinese_calendar 判断失败: {e}，回退到简单判断")
            return self._is_trading_day_simple(date_obj)
    
    def _is_trading_day_database(self, date_str: str) -> bool:
        """
        查询数据库判断
        
        优点：最准确，基于实际交易数据
        缺点：需要数据库连接，且依赖历史数据
        """
        if not self.db_conn:
            logger.warning("未提供数据库连接，回退到简单判断")
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return self._is_trading_day_simple(date_obj)
        
        try:
            cursor = self.db_conn.cursor()
            
            # 方法1: 查询该日期是否有交易数据
            cursor.execute("""
                SELECT COUNT(*) 
                FROM daily_stock_data 
                WHERE trade_date = %s 
                LIMIT 1
            """, (date_str,))
            
            has_data = cursor.fetchone()[0] > 0
            cursor.close()
            
            if has_data:
                logger.debug(f"{date_str} 是交易日（数据库有数据）")
                return True
            
            # 方法2: 如果没有数据，查询同步状态表
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT status 
                FROM daily_sync_status 
                WHERE sync_date = %s
            """, (date_str,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                # 如果状态表中标记为非交易日
                if result[0] == 'non_trading_day':
                    logger.debug(f"{date_str} 是非交易日（状态表标记）")
                    return False
            
            # 如果数据库中没有信息，回退到简单判断
            logger.debug(f"{date_str} 数据库无信息，使用简单判断")
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return self._is_trading_day_simple(date_obj)
            
        except Exception as e:
            logger.warning(f"数据库查询失败: {e}，回退到简单判断")
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            return self._is_trading_day_simple(date_obj)
    
    def get_recent_trading_days(self, days: int = 5) -> list:
        """
        获取最近N个交易日
        
        Args:
            days: 天数
        
        Returns:
            交易日列表（降序）
        """
        from datetime import timedelta
        
        trading_days = []
        current_date = date.today()
        
        while len(trading_days) < days:
            date_str = current_date.strftime('%Y-%m-%d')
            if self.is_trading_day(date_str):
                trading_days.append(date_str)
            current_date -= timedelta(days=1)
        
        return trading_days
    
    def get_next_trading_day(self, date_str: str) -> Optional[str]:
        """
        获取下一个交易日
        
        Args:
            date_str: 起始日期
        
        Returns:
            下一个交易日，如果未来30天内没有则返回None
        """
        from datetime import timedelta
        
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
        
        # 最多向后查找30天
        for i in range(1, 31):
            next_date = current_date + timedelta(days=i)
            next_date_str = next_date.strftime('%Y-%m-%d')
            if self.is_trading_day(next_date_str):
                return next_date_str
        
        return None


# ==================== 工具函数 ====================

def install_chinese_calendar():
    """安装 chinese_calendar 库"""
    import subprocess
    import sys
    
    print("正在安装 chinese_calendar...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chinese-calendar"])
        print("✅ chinese_calendar 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ chinese_calendar 安装失败: {e}")
        return False


def test_trading_calendar():
    """测试交易日历功能"""
    print("=" * 80)
    print("测试交易日历功能")
    print("=" * 80)
    
    # 测试日期
    test_dates = [
        '2025-10-10',  # 周五
        '2025-10-11',  # 周六
        '2025-10-12',  # 周日
        '2025-10-13',  # 周一
        '2025-10-01',  # 国庆节
    ]
    
    # 测试简单判断
    print("\n1. 简单判断（只判断周末）:")
    calendar_simple = TradingCalendar(method='simple')
    for date_str in test_dates:
        is_trading = calendar_simple.is_trading_day(date_str)
        print(f"  {date_str}: {'✅ 交易日' if is_trading else '❌ 非交易日'}")
    
    # 测试 chinese_calendar
    print("\n2. chinese_calendar 判断（识别节假日）:")
    calendar_lib = TradingCalendar(method='calendar')
    for date_str in test_dates:
        is_trading = calendar_lib.is_trading_day(date_str)
        print(f"  {date_str}: {'✅ 交易日' if is_trading else '❌ 非交易日'}")
    
    # 测试获取最近交易日
    print("\n3. 获取最近5个交易日:")
    recent_days = calendar_simple.get_recent_trading_days(5)
    for day in recent_days:
        print(f"  {day}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # 运行测试
    test_trading_calendar()
    
    # 提示安装 chinese_calendar
    print("\n提示: 安装 chinese_calendar 可以更准确地判断交易日")
    print("安装命令: pip install chinese-calendar")
