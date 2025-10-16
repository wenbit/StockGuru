#!/usr/bin/env python3
"""
本地数据初始化脚本 - 同步近1年历史数据
使用 PostgreSQL COPY 命令实现高速批量导入

运行方式:
    python scripts/init_historical_data.py --days 365

环境变量:
    SUPABASE_DB_HOST=db.xxx.supabase.co
    SUPABASE_DB_PASSWORD=your_password
"""

import os
import sys
import logging
import argparse
from datetime import date, timedelta
from typing import List, Dict
import pandas as pd
import numpy as np
import baostock as bs
import psycopg2
from psycopg2 import pool
from io import StringIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('init_historical_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HistoricalDataInitializer:
    """历史数据初始化器"""
    
    def __init__(self):
        """初始化连接池"""
        self.db_host = os.getenv('SUPABASE_DB_HOST')
        self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
        self.db_port = int(os.getenv('SUPABASE_DB_PORT', '6543'))  # 使用 Pooler
        
        if not self.db_host or not self.db_password:
            raise ValueError("请设置环境变量: SUPABASE_DB_HOST, SUPABASE_DB_PASSWORD")
        
        # 创建连接池
        self.connection_pool = pool.SimpleConnectionPool(
            1, 5,  # 最小/最大连接数
            host=self.db_host,
            port=self.db_port,
            database='postgres',
            user='postgres',
            password=self.db_password,
            sslmode='require'
        )
        
        logger.info(f"数据库连接池已创建: {self.db_host}:{self.db_port}")
        
        # baostock 登录
        bs.login()
        logger.info("baostock 登录成功")
    
    def get_trading_days(self, days: int) -> List[str]:
        """获取最近N天的交易日列表"""
        logger.info(f"获取最近 {days} 天的交易日...")
        
        end_date = date.today() - timedelta(days=1)  # 昨天
        start_date = end_date - timedelta(days=days)
        
        # 获取交易日历
        rs = bs.query_trade_dates(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        trading_days = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            if row[1] == '1':  # is_trading_day
                trading_days.append(row[0])
        
        logger.info(f"获取到 {len(trading_days)} 个交易日")
        return trading_days
    
    def get_all_stocks(self) -> List[Dict[str, str]]:
        """获取所有A股列表"""
        logger.info("获取全市场A股列表...")
        
        rs = bs.query_all_stock(day=date.today().strftime('%Y-%m-%d'))
        
        stocks = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            if row[1].startswith('sh.') or row[1].startswith('sz.'):
                stocks.append({
                    'code': row[0],
                    'full_code': row[1],
                    'name': row[2]
                })
        
        logger.info(f"获取到 {len(stocks)} 只A股")
        return stocks
    
    def fetch_stock_data(self, stock: Dict, start_date: str, end_date: str) -> pd.DataFrame:
        """获取单只股票的历史数据"""
        try:
            rs = bs.query_history_k_data_plus(
                stock['full_code'],
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2"
            )
            
            if rs.error_code != '0':
                return None
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return None
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 数据处理
            numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount', 'turn', 'pctChg']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            df.rename(columns={
                'date': 'trade_date',
                'open': 'open_price',
                'close': 'close_price',
                'high': 'high_price',
                'low': 'low_price',
                'pctChg': 'change_pct',
                'turn': 'turnover_rate'
            }, inplace=True)
            
            df = df.assign(
                stock_code=stock['code'],
                stock_name=stock['name'],
                change_amount=df['close_price'] - df['close_price'].shift(1),
                amplitude=((df['high_price'] - df['low_price']) / df['close_price'].shift(1) * 100).round(2)
            )
            
            df = df[[
                'stock_code', 'stock_name', 'trade_date',
                'open_price', 'close_price', 'high_price', 'low_price',
                'volume', 'amount', 'change_pct', 'change_amount',
                'turnover_rate', 'amplitude'
            ]]
            
            # 处理 NaN
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            
            return df
            
        except Exception as e:
            logger.warning(f"获取 {stock['code']} 数据失败: {e}")
            return None
    
    def bulk_insert_with_copy(self, df: pd.DataFrame):
        """使用 PostgreSQL COPY 批量插入"""
        conn = self.connection_pool.getconn()
        try:
            cursor = conn.cursor()
            
            # 创建临时表
            cursor.execute("""
                CREATE TEMP TABLE temp_daily_stock_data (
                    stock_code TEXT,
                    stock_name TEXT,
                    trade_date DATE,
                    open_price NUMERIC,
                    close_price NUMERIC,
                    high_price NUMERIC,
                    low_price NUMERIC,
                    volume BIGINT,
                    amount NUMERIC,
                    change_pct NUMERIC,
                    change_amount NUMERIC,
                    turnover_rate NUMERIC,
                    amplitude NUMERIC
                )
            """)
            
            # 准备 CSV 数据
            buffer = StringIO()
            df.to_csv(buffer, index=False, header=False, na_rep='\\N', sep='\t')
            buffer.seek(0)
            
            # COPY 到临时表
            cursor.copy_from(
                buffer,
                'temp_daily_stock_data',
                sep='\t',
                null='\\N',
                columns=df.columns.tolist()
            )
            
            # 从临时表插入到正式表（处理冲突）
            cursor.execute("""
                INSERT INTO daily_stock_data (
                    stock_code, stock_name, trade_date,
                    open_price, close_price, high_price, low_price,
                    volume, amount, change_pct, change_amount,
                    turnover_rate, amplitude
                )
                SELECT * FROM temp_daily_stock_data
                ON CONFLICT (stock_code, trade_date) DO NOTHING
            """)
            
            inserted_count = cursor.rowcount
            conn.commit()
            
            return inserted_count
            
        except Exception as e:
            conn.rollback()
            logger.error(f"批量插入失败: {e}")
            raise
        finally:
            cursor.close()
            self.connection_pool.putconn(conn)
    
    def sync_date_range(self, start_date: str, end_date: str):
        """同步指定日期范围的数据"""
        logger.info(f"开始同步 {start_date} 到 {end_date} 的数据...")
        
        stocks = self.get_all_stocks()
        total_stocks = len(stocks)
        
        all_data = []
        success_count = 0
        failed_count = 0
        
        for idx, stock in enumerate(stocks, start=1):
            df = self.fetch_stock_data(stock, start_date, end_date)
            
            if df is not None and not df.empty:
                all_data.append(df)
                success_count += 1
            else:
                failed_count += 1
            
            if idx % 100 == 0:
                logger.info(f"进度: {idx}/{total_stocks}, 成功: {success_count}, 失败: {failed_count}")
        
        # 合并所有数据
        if all_data:
            logger.info("合并数据并批量入库...")
            combined_df = pd.concat(all_data, ignore_index=True)
            inserted_count = self.bulk_insert_with_copy(combined_df)
            logger.info(f"成功入库 {inserted_count} 条记录")
        
        logger.info(f"同步完成: 成功 {success_count}, 失败 {failed_count}")
    
    def sync_by_month(self, days: int):
        """按月分批同步（避免内存溢出）"""
        trading_days = self.get_trading_days(days)
        
        # 按月分组
        months = {}
        for day in trading_days:
            month_key = day[:7]  # YYYY-MM
            if month_key not in months:
                months[month_key] = []
            months[month_key].append(day)
        
        logger.info(f"共 {len(months)} 个月需要同步")
        
        for month, days_in_month in sorted(months.items()):
            start_date = days_in_month[0]
            end_date = days_in_month[-1]
            logger.info(f"\n{'='*60}")
            logger.info(f"同步 {month} 月数据 ({len(days_in_month)} 个交易日)")
            logger.info(f"{'='*60}")
            self.sync_date_range(start_date, end_date)
    
    def close(self):
        """关闭连接"""
        self.connection_pool.closeall()
        bs.logout()
        logger.info("连接已关闭")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='初始化历史股票数据')
    parser.add_argument('--days', type=int, default=365, help='同步最近N天的数据（默认365天）')
    args = parser.parse_args()
    
    try:
        initializer = HistoricalDataInitializer()
        initializer.sync_by_month(args.days)
        initializer.close()
        
        logger.info("\n" + "="*60)
        logger.info("✅ 历史数据初始化完成！")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
