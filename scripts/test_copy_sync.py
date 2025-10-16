#!/usr/bin/env python3
"""
测试 PostgreSQL COPY 方案性能
同步少量股票数据来验证速度提升

使用方法:
    export SUPABASE_DB_PASSWORD='your_password'
    python scripts/test_copy_sync.py --stocks 50 --date 2025-10-09
"""

import os
import sys
import logging
import argparse
import time
from datetime import date, datetime
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import baostock as bs
import psycopg2
from io import StringIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class CopySyncTester:
    """COPY 方案性能测试器"""
    
    def __init__(self):
        """初始化"""
        self.db_host = os.getenv('SUPABASE_DB_HOST', 'db.mislyhozlviaedinpnfa.supabase.co')
        self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
        self.db_port = int(os.getenv('SUPABASE_DB_PORT', '6543'))
        
        if not self.db_password:
            raise ValueError("请设置环境变量: SUPABASE_DB_PASSWORD")
        
        # 连接数据库
        self.conn = psycopg2.connect(
            host=self.db_host,
            port=self.db_port,
            database='postgres',
            user='postgres',
            password=self.db_password,
            sslmode='require'
        )
        logger.info(f"数据库连接成功: {self.db_host}:{self.db_port}")
        
        # 登录 baostock
        bs.login()
        logger.info("baostock 登录成功")
    
    def get_stocks(self, limit: int) -> List[Dict[str, str]]:
        """获取指定数量的股票"""
        logger.info(f"获取前 {limit} 只股票...")
        
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
                if len(stocks) >= limit:
                    break
        
        logger.info(f"获取到 {len(stocks)} 只股票")
        return stocks
    
    def fetch_stock_data(self, stock: Dict, date_str: str) -> Optional[pd.DataFrame]:
        """获取单只股票数据"""
        try:
            rs = bs.query_history_k_data_plus(
                stock['full_code'],
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=date_str,
                end_date=date_str,
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
            
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            
            return df
            
        except Exception as e:
            logger.warning(f"获取 {stock['code']} 失败: {e}")
            return None
    
    def insert_with_copy(self, df: pd.DataFrame) -> tuple:
        """使用 COPY 插入数据"""
        start_time = time.time()
        
        try:
            cursor = self.conn.cursor()
            
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
            
            # 插入到正式表
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
            self.conn.commit()
            cursor.close()
            
            elapsed = time.time() - start_time
            return inserted_count, elapsed
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"COPY 插入失败: {e}")
            raise
    
    def test_sync(self, stock_count: int, date_str: str):
        """测试同步性能"""
        logger.info(f"\n{'='*60}")
        logger.info(f"开始测试: {stock_count} 只股票, 日期: {date_str}")
        logger.info(f"{'='*60}\n")
        
        # 获取股票列表
        stocks = self.get_stocks(stock_count)
        
        # 获取数据
        logger.info("开始获取股票数据...")
        fetch_start = time.time()
        
        all_data = []
        success = 0
        failed = 0
        
        for idx, stock in enumerate(stocks, 1):
            df = self.fetch_stock_data(stock, date_str)
            if df is not None and not df.empty:
                all_data.append(df)
                success += 1
            else:
                failed += 1
            
            if idx % 10 == 0:
                logger.info(f"进度: {idx}/{stock_count}, 成功: {success}, 失败: {failed}")
        
        fetch_elapsed = time.time() - fetch_start
        logger.info(f"\n数据获取完成: 耗时 {fetch_elapsed:.2f} 秒")
        logger.info(f"成功: {success}, 失败: {failed}")
        
        if not all_data:
            logger.error("没有获取到任何数据")
            return
        
        # 合并数据
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"合并数据: {len(combined_df)} 条记录")
        
        # 使用 COPY 插入
        logger.info("\n使用 PostgreSQL COPY 插入数据...")
        inserted, insert_elapsed = self.insert_with_copy(combined_df)
        
        # 统计结果
        total_elapsed = time.time() - fetch_start
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 性能测试结果")
        logger.info(f"{'='*60}")
        logger.info(f"股票数量: {stock_count}")
        logger.info(f"成功获取: {success}")
        logger.info(f"数据记录: {len(combined_df)}")
        logger.info(f"成功入库: {inserted}")
        logger.info(f"")
        logger.info(f"⏱️  耗时统计:")
        logger.info(f"  数据获取: {fetch_elapsed:.2f} 秒")
        logger.info(f"  数据入库: {insert_elapsed:.2f} 秒")
        logger.info(f"  总耗时:   {total_elapsed:.2f} 秒")
        logger.info(f"")
        logger.info(f"🚀 速度:")
        logger.info(f"  平均: {stock_count / total_elapsed * 60:.1f} 股/分钟")
        logger.info(f"  入库速度: {inserted / insert_elapsed:.0f} 条/秒")
        logger.info(f"{'='*60}\n")
    
    def close(self):
        """关闭连接"""
        self.conn.close()
        bs.logout()


def main():
    parser = argparse.ArgumentParser(description='测试 PostgreSQL COPY 性能')
    parser.add_argument('--stocks', type=int, default=50, help='测试股票数量（默认50）')
    parser.add_argument('--date', type=str, default='2025-10-09', help='同步日期（默认2025-10-09）')
    args = parser.parse_args()
    
    try:
        tester = CopySyncTester()
        tester.test_sync(args.stocks, args.date)
        tester.close()
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
