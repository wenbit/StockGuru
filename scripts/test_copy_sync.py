#!/usr/bin/env python3
"""
测试 PostgreSQL COPY 方案性能
同步少量股票数据来验证速度提升

使用方法:
    # 方式1: 使用 DATABASE_URL (推荐)
    export DATABASE_URL='postgresql://user:password@host:port/database?sslmode=require'
    python scripts/test_copy_sync.py --stocks 50 --date 2025-10-09
    
    # 方式2: 使用独立环境变量
    export SUPABASE_DB_PASSWORD='your_password'
    python scripts/test_copy_sync.py --stocks 50 --date 2025-10-09
"""

import os
import sys
import logging
import argparse
import time
from datetime import date, datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
import numpy as np
import baostock as bs
import psycopg2
from io import StringIO
from dotenv import load_dotenv

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

# 加载.env文件
project_root = Path(__file__).parent.parent
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

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
        # 优先使用 DATABASE_URL
        database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        
        if database_url:
            # 使用 DATABASE_URL 连接，添加连接保活参数
            logger.info("使用 DATABASE_URL 连接数据库")
            self.conn = psycopg2.connect(
                database_url,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=30
            )
            logger.info("数据库连接成功 (DATABASE_URL, keepalive enabled)")
        else:
            # 回退到独立环境变量
            self.db_host = os.getenv('SUPABASE_DB_HOST', 'db.mislyhozlviaedinpnfa.supabase.co')
            self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
            self.db_port = int(os.getenv('SUPABASE_DB_PORT', '6543'))
            
            if not self.db_password:
                raise ValueError(
                    "请设置环境变量: DATABASE_URL 或 SUPABASE_DB_PASSWORD\n"
                    "示例: export DATABASE_URL='postgresql://user:password@host:port/database?sslmode=require'"
                )
            
            # 连接数据库，添加连接保活参数
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database='postgres',
                user='postgres',
                password=self.db_password,
                sslmode='require',
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=30
            )
            logger.info(f"数据库连接成功 (keepalive enabled): {self.db_host}:{self.db_port}")
        
        # 登录 baostock
        bs.login()
        logger.info("baostock 登录成功")
        
        # 保存连接参数以便重连
        self.database_url = database_url
        self.db_params = {
            'host': self.db_host if not database_url else None,
            'port': self.db_port if not database_url else None,
            'database': 'postgres' if not database_url else None,
            'user': 'postgres' if not database_url else None,
            'password': self.db_password if not database_url else None,
            'sslmode': 'require' if not database_url else None
        }
        
        # 记录连接时间，用于定期重连
        self.last_reconnect_time = time.time()
        self.reconnect_interval = 300  # 每5分钟主动重连一次
    
    def _reconnect(self):
        """重新连接数据库"""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
        except:
            pass
        
        if self.database_url:
            # 重连时也使用保活参数
            self.conn = psycopg2.connect(
                self.database_url,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5,
                connect_timeout=30
            )
            logger.info("数据库重新连接成功 (DATABASE_URL, keepalive enabled)")
        else:
            # 添加保活参数到重连
            params = {k: v for k, v in self.db_params.items() if v is not None}
            params.update({
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
                'connect_timeout': 30
            })
            self.conn = psycopg2.connect(**params)
            logger.info(f"数据库重新连接成功 (keepalive enabled): {self.db_host}:{self.db_port}")
        
        # 更新重连时间
        self.last_reconnect_time = time.time()
    
    def _check_and_reconnect_if_needed(self):
        """检查连接时长，如果超过阈值则主动重连"""
        elapsed = time.time() - self.last_reconnect_time
        if elapsed > self.reconnect_interval:
            logger.info(f"⚠️  连接已持续 {elapsed:.0f} 秒，主动重连以避免超时...")
            self._reconnect()
    
    def get_synced_stocks(self, date_str: str) -> set:
        """获取指定日期已同步的股票代码列表"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT stock_code 
                FROM daily_stock_data 
                WHERE trade_date = %s
            """, (date_str,))
            synced_codes = {row[0] for row in cursor.fetchall()}
            cursor.close()
            return synced_codes
        except Exception as e:
            logger.warning(f"查询已同步股票失败: {e}")
            return set()
    
    def get_stocks(self, limit: int = None, query_date: str = None) -> List[Dict[str, str]]:
        """获取指定数量的股票"""
        if limit:
            logger.info(f"获取前 {limit} 只股票...")
        else:
            logger.info(f"获取所有A股股票...")
        
        # 动态获取股票列表（自动包含新股、排除退市股）
        # 使用指定日期或当前日期
        from datetime import date
        if query_date:
            query_day = query_date
        else:
            query_day = date.today().strftime('%Y-%m-%d')
        rs = bs.query_all_stock(day=query_day)
        logger.info(f"查询日期: {query_day}")
        
        stocks = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            # fields: ['code', 'tradeStatus', 'code_name']
            # row[0] = code (如 'sh.600000')
            # row[1] = tradeStatus
            # row[2] = code_name
            
            code = row[0]
            name = row[2]
            
            # 只获取 A股票（6位数字代码）
            # 排除指数（如 sh.000001）和其他非股票代码
            if code and '.' in code:
                stock_code = code.split('.')[1]
                # A股代码规则：
                # 沪市主板: 600xxx, 601xxx, 603xxx, 605xxx
                # 沪市科创板: 688xxx
                # 深市主板: 000xxx, 001xxx
                # 深市中小板: 002xxx, 003xxx, 004xxx
                # 深市创业板: 300xxx, 301xxx
                # 北交所: 8xxxxx, 43xxxx
                if (stock_code.startswith('600') or stock_code.startswith('601') or 
                    stock_code.startswith('603') or stock_code.startswith('605') or
                    stock_code.startswith('688') or  # 科创板
                    stock_code.startswith('000') or stock_code.startswith('001') or
                    stock_code.startswith('002') or stock_code.startswith('003') or stock_code.startswith('004') or
                    stock_code.startswith('300') or stock_code.startswith('301') or  # 创业板
                    stock_code.startswith('8') or stock_code.startswith('43')):  # 北交所
                    stocks.append({
                        'code': stock_code,
                        'full_code': code,
                        'name': name
                    })
                    if limit and len(stocks) >= limit:
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
    
    def insert_with_copy(self, df: pd.DataFrame, max_retries: int = 3) -> tuple:
        """使用 COPY 插入数据，支持重试"""
        start_time = time.time()
        
        # 主动检查并重连（避免连接超时）
        self._check_and_reconnect_if_needed()
        
        for attempt in range(max_retries):
            try:
                # 检查连接是否有效，如果无效则重新连接
                try:
                    self.conn.isolation_level
                except:
                    logger.warning(f"数据库连接已断开，正在重新连接... (尝试 {attempt + 1}/{max_retries})")
                    self._reconnect()
                
                cursor = self.conn.cursor()
                
                # 先删除可能存在的临时表，然后创建新的
                cursor.execute("DROP TABLE IF EXISTS temp_daily_stock_data")
                
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
                try:
                    self.conn.rollback()
                except:
                    pass
                
                if attempt < max_retries - 1:
                    logger.warning(f"❌ 批量入库失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    logger.error(f"❌ 批量入库失败，已达最大重试次数: {e}")
                    raise
        
        # 如果所有重试都失败
        raise Exception("批量入库失败，已达最大重试次数")
    
    def update_sync_status(self, sync_date: str, status: str, total_records: int = 0, 
                           success_count: int = 0, failed_count: int = 0, remarks: str = None):
        """更新同步状态记录"""
        try:
            cursor = self.conn.cursor()
            
            # 检查记录是否存在
            cursor.execute(
                "SELECT id FROM daily_sync_status WHERE sync_date = %s",
                (sync_date,)
            )
            existing = cursor.fetchone()
            
            # 使用北京时间（转换为字符串格式，确保时区信息被保留）
            beijing_now = datetime.now(BEIJING_TZ)
            beijing_now_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
            
            if existing:
                # 更新现有记录
                end_time_str = beijing_now_str if status in ('success', 'failed', 'skipped') else None
                cursor.execute("""
                    UPDATE daily_sync_status 
                    SET status = %s,
                        total_records = %s,
                        success_count = %s,
                        failed_count = %s,
                        remarks = %s,
                        end_time = COALESCE(%s::timestamp, end_time),
                        updated_at = %s::timestamp
                    WHERE sync_date = %s
                """, (status, total_records, success_count, failed_count, remarks, end_time_str, beijing_now_str, sync_date))
            else:
                # 创建新记录（使用北京时间）
                cursor.execute("""
                    INSERT INTO daily_sync_status (
                        sync_date, status, total_records, success_count, failed_count, 
                        remarks, start_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::timestamp)
                """, (sync_date, status, total_records, success_count, failed_count, remarks, beijing_now_str))
            
            self.conn.commit()
            cursor.close()
            logger.debug(f"已更新同步记录: {sync_date} - {status}")
        except Exception as e:
            logger.error(f"更新同步记录失败: {e}")
            try:
                self.conn.rollback()
            except:
                pass
    
    def test_sync(self, stock_count: Optional[int], date_str: str):
        """测试同步性能"""
        logger.info(f"\n{'='*60}")
        if stock_count:
            logger.info(f"开始测试: {stock_count} 只股票, 日期: {date_str}")
        else:
            logger.info(f"开始测试: 全量A股, 日期: {date_str}")
        logger.info(f"{'='*60}\n")
        
        # 创建同步记录（状态：syncing）
        self.update_sync_status(date_str, 'syncing', remarks='开始同步')
        
        # 获取股票列表（使用同步日期来获取当时的股票列表）
        stocks = self.get_stocks(stock_count, query_date=date_str)
        actual_count = len(stocks)
        
        # 判断是否为非交易日：如果获取到的股票数为0，说明是非交易日
        if actual_count == 0:
            logger.info(f"⚠️  {date_str} 非交易日（获取到0只股票），跳过同步")
            # 更新同步记录（状态：skipped）
            self.update_sync_status(date_str, 'skipped', remarks='非交易日')
            logger.info("✅ 所有股票已同步完成！")
            return
        
        # 查询已同步的股票（断点续传）
        synced_stocks = self.get_synced_stocks(date_str)
        if synced_stocks:
            logger.info(f"📋 发现已同步 {len(synced_stocks)} 只股票，将跳过...")
            # 过滤掉已同步的股票
            stocks = [s for s in stocks if s['code'] not in synced_stocks]
            logger.info(f"📋 剩余待同步: {len(stocks)} 只股票")
        
        if not stocks:
            logger.info("✅ 所有股票已同步完成！")
            return
        
        # 获取数据
        logger.info("开始获取股票数据...")
        fetch_start = time.time()
        
        all_data = []
        success = 0
        failed = 0
        total_inserted = 0
        batch_size = 500  # 每500只股票入库一次（与生产环境一致）
        remaining_count = len(stocks)  # 剩余待同步数量
        already_synced = len(synced_stocks)  # 已同步数量
        
        for idx, stock in enumerate(stocks, 1):
            df = self.fetch_stock_data(stock, date_str)
            if df is not None and not df.empty:
                all_data.append(df)
                success += 1
            else:
                failed += 1
            
            # 每500只或最后一批，进行入库
            if len(all_data) >= batch_size or idx == remaining_count:
                if all_data:
                    try:
                        combined_df = pd.concat(all_data, ignore_index=True)
                        inserted, _ = self.insert_with_copy(combined_df)
                        total_inserted += inserted
                        logger.info(f"✅ 已入库 {len(all_data)} 只股票，{inserted} 条新记录，累计: {already_synced + total_inserted}")
                        
                        # 实时更新同步记录
                        current_inserted = already_synced + total_inserted
                        self.update_sync_status(
                            date_str, 
                            'syncing', 
                            total_records=current_inserted,  # 总记录数：当前已入库的数据条数
                            success_count=current_inserted,  # 成功数：当前已入库的数据条数
                            failed_count=failed,  # 失败数：已失败的股票数量
                            remarks=f'同步中: 获取{success}/{actual_count}只, 失败{failed}只, 已入库{current_inserted}条'
                        )
                        
                        all_data = []  # 清空缓存
                    except Exception as e:
                        logger.error(f"❌ 批量入库失败: {e}")
            
            # 实时进度显示
            if idx % 10 == 0 or idx == remaining_count:
                elapsed = time.time() - fetch_start
                speed = idx / elapsed if elapsed > 0 else 0
                eta = (remaining_count - idx) / speed if speed > 0 else 0
                current_total = already_synced + success
                logger.info(
                    f"进度: {current_total}/{actual_count} ({current_total*100//actual_count}%), "
                    f"成功: {success}, 失败: {failed}, "
                    f"已入库: {already_synced + total_inserted}, "
                    f"速度: {speed:.1f}股/秒, "
                    f"预计剩余: {eta:.0f}秒"
                )
        
        fetch_elapsed = time.time() - fetch_start
        logger.info(f"\n数据获取完成: 耗时 {fetch_elapsed:.2f} 秒")
        logger.info(f"成功: {success}, 失败: {failed}")
        logger.info(f"总入库: {total_inserted} 条记录")
        
        if success == 0:
            logger.error("没有获取到任何数据")
            # 更新同步记录（状态：failed）
            self.update_sync_status(date_str, 'failed', remarks='没有获取到任何数据')
            return
        
        # 已经实时入库，不需要再次入库
        inserted = total_inserted
        insert_elapsed = 0
        
        # 统计结果
        total_elapsed = time.time() - fetch_start
        
        # 判断最终状态：只有全部成功才标记为success，有任何失败就标记为failed
        final_status = 'success' if failed == 0 else 'failed'
        final_inserted_count = already_synced + total_inserted  # 累计入库总数
        final_remarks = f'同步完成: 获取{success}只, 失败{failed}只, 入库{final_inserted_count}条'
        
        # 更新同步记录
        self.update_sync_status(
            date_str, 
            final_status, 
            total_records=final_inserted_count,  # 总记录数：实际入库的数据条数
            success_count=final_inserted_count,  # 成功数：实际入库的数据条数
            failed_count=failed,  # 失败数：本次失败的股票数量
            remarks=final_remarks
        )
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 性能测试结果")
        logger.info(f"{'='*60}")
        logger.info(f"股票数量: {actual_count}")
        logger.info(f"成功获取: {success}")
        logger.info(f"成功入库: {inserted}")
        logger.info(f"")
        logger.info(f"⏱️  耗时统计:")
        logger.info(f"  数据获取: {fetch_elapsed:.2f} 秒 ({fetch_elapsed/60:.1f} 分钟)")
        logger.info(f"  数据入库: {insert_elapsed:.2f} 秒")
        logger.info(f"  总耗时:   {total_elapsed:.2f} 秒 ({total_elapsed/60:.1f} 分钟)")
        logger.info(f"")
        logger.info(f"🚀 速度:")
        logger.info(f"  平均: {actual_count / total_elapsed * 60:.1f} 股/分钟")
        if insert_elapsed > 0:
            logger.info(f"  入库速度: {inserted / insert_elapsed:.0f} 条/秒")
        else:
            logger.info(f"  入库速度: 实时入库（边获取边入库）")
        logger.info(f"{'='*60}\n")
    
    def close(self):
        """关闭连接"""
        self.conn.close()
        bs.logout()


def main():
    from datetime import date, timedelta
    
    # 默认使用昨天的日期（今天的数据可能还没有）
    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    parser = argparse.ArgumentParser(description='测试 PostgreSQL COPY 性能')
    parser.add_argument('--stocks', type=int, default=50, help='测试股票数量（默认50，0表示全量）')
    parser.add_argument('--date', type=str, default=yesterday, help=f'同步日期（默认昨天: {yesterday}）')
    parser.add_argument('--all', action='store_true', help='同步所有A股（等同于 --stocks 0）')
    args = parser.parse_args()
    
    try:
        tester = CopySyncTester()
        # 如果指定 --all 或 --stocks 0，则获取所有股票
        stock_count = None if (args.all or args.stocks == 0) else args.stocks
        tester.test_sync(stock_count, args.date)
        tester.close()
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
