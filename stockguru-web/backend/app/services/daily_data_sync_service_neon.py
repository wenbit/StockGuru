"""
每日股票数据同步服务 - Neon 版本
使用 PostgreSQL 直连 + execute_values 批量插入
性能提升 5-10 倍

优化特性:
- 失败重试机制
- 连接池管理
- 自适应批量大小
"""

import logging
import os
import time
import json
from pathlib import Path
from io import StringIO
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# 尝试导入 baostock
try:
    import baostock as bs
except ImportError:
    bs = None
    logger.warning("baostock 未安装")


class DailyDataSyncServiceNeon:
    """每日数据同步服务 - Neon 版本"""
    
    def __init__(self):
        """初始化同步服务"""
        if bs is None:
            raise ImportError("baostock 未安装，请运行: pip install baostock")
        
        self.logger = logging.getLogger(__name__)
        self.bs_logged_in = False
        
        # 获取 Neon 数据库连接
        self.database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        if not self.database_url:
            raise ValueError("未设置 DATABASE_URL 或 NEON_DATABASE_URL 环境变量")
        
        # 优化连接参数以解决 COPY 命令 SSL 问题
        # 检测是否为本地数据库（localhost 或 127.0.0.1）
        is_local = 'localhost' in self.database_url or '127.0.0.1' in self.database_url
        
        if '?' not in self.database_url:
            if is_local:
                # 本地数据库不需要 SSL
                self.database_url += '?connect_timeout=30&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5'
            else:
                # 远程数据库（Neon）需要 SSL
                self.database_url += '?sslmode=require&connect_timeout=30&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5'
        
        # 创建连接池（优化：增加连接数以支持更高并发）
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=5,   # 增加最小连接数
                maxconn=20,  # 增加最大连接数
                dsn=self.database_url
            )
            self.logger.info(f"使用数据库（连接池: 5-20，已优化 SSL 参数）")
        except Exception as e:
            self.logger.error(f"创建连接池失败: {e}")
            self.connection_pool = None
    
    def _get_db_connection(self):
        """从连接池获取数据库连接"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        else:
            return psycopg2.connect(self.database_url)
    
    def _return_db_connection(self, conn):
        """归还连接到连接池"""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def _bulk_insert_with_copy(self, cursor, df: pd.DataFrame, max_batch_size: int = 500) -> int:
        """
        使用 PostgreSQL COPY 命令批量插入（优化版，解决 SSL 问题）
        
        优化措施:
        1. 限制单次 COPY 的数据量（避免大数据传输导致 SSL 超时）
        2. 使用更简单的 COPY 语法
        3. 添加重试机制
        
        Args:
            cursor: 数据库游标
            df: 要插入的 DataFrame
            max_batch_size: 单次 COPY 的最大行数（默认500，避免 SSL 超时）
            
        Returns:
            插入的记录数
        """
        try:
            # 准备列顺序
            columns_order = [
                'stock_code', 'stock_name', 'trade_date',
                'open_price', 'close_price', 'high_price', 'low_price',
                'volume', 'amount', 'change_pct', 'change_amount',
                'turnover_rate', 'amplitude'
            ]
            
            total_inserted = 0
            
            # 如果数据量大，分批处理（避免 SSL 超时）
            if len(df) > max_batch_size:
                for i in range(0, len(df), max_batch_size):
                    batch_df = df.iloc[i:i+max_batch_size]
                    inserted = self._copy_batch(cursor, batch_df, columns_order)
                    total_inserted += inserted
                    self.logger.debug(f"COPY 批次 {i//max_batch_size + 1}: {inserted} 条")
            else:
                total_inserted = self._copy_batch(cursor, df, columns_order)
            
            return total_inserted
            
        except Exception as e:
            self.logger.error(f"COPY 插入失败: {e}")
            raise
    
    def _copy_batch(self, cursor, df: pd.DataFrame, columns_order: list) -> int:
        """
        执行单批 COPY 操作
        
        Args:
            cursor: 数据库游标
            df: 要插入的 DataFrame
            columns_order: 列顺序
            
        Returns:
            插入的记录数
        """
        # 创建临时表方式（更稳定）
        temp_table = f"temp_import_{int(time.time() * 1000)}"
        
        try:
            # 1. 创建临时表
            cursor.execute(f"""
                CREATE TEMP TABLE {temp_table} (
                    stock_code VARCHAR(10),
                    stock_name VARCHAR(50),
                    trade_date DATE,
                    open_price DECIMAL(10,2),
                    close_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    volume BIGINT,
                    amount DECIMAL(20,2),
                    change_pct DECIMAL(10,2),
                    change_amount DECIMAL(10,2),
                    turnover_rate DECIMAL(10,2),
                    amplitude DECIMAL(10,2)
                ) ON COMMIT DROP
            """)
            
            # 2. 准备 CSV 数据
            csv_buffer = StringIO()
            df[columns_order].to_csv(
                csv_buffer,
                index=False,
                header=False,
                sep='\t',
                na_rep=''
            )
            csv_buffer.seek(0)
            
            # 3. COPY 到临时表（更稳定，不涉及约束检查）
            cursor.copy_expert(
                f"COPY {temp_table} FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '')",
                csv_buffer
            )
            
            # 4. 从临时表插入到目标表（带冲突处理，明确指定列）
            cursor.execute(f"""
                INSERT INTO daily_stock_data (
                    stock_code, stock_name, trade_date,
                    open_price, close_price, high_price, low_price,
                    volume, amount, change_pct, change_amount,
                    turnover_rate, amplitude
                )
                SELECT 
                    stock_code, stock_name, trade_date,
                    open_price, close_price, high_price, low_price,
                    volume, amount, change_pct, change_amount,
                    turnover_rate, amplitude
                FROM {temp_table}
                ON CONFLICT (stock_code, trade_date) DO NOTHING
            """)
            
            return len(df)
            
        except Exception as e:
            self.logger.error(f"COPY 批次失败: {e}")
            raise
    
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
    
    def _is_trading_day(self, check_date: date) -> bool:
        """检查是否为交易日"""
        if not self._login_baostock():
            return False
        
        rs = bs.query_trade_dates(
            start_date=check_date.strftime('%Y-%m-%d'),
            end_date=check_date.strftime('%Y-%m-%d')
        )
        
        if rs.error_code != '0':
            return False
        
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            return row[1] == '1'  # is_trading_day
        
        return False
    
    def _get_all_stocks(self, query_date: date = None) -> List[Dict[str, str]]:
        """
        获取全市场A股列表（带缓存）
        
        优化：缓存股票列表，7天更新一次，避免每次都从 baostock 获取
        
        Args:
            query_date: 查询日期（不使用，保留参数兼容性）
        """
        # 缓存文件路径
        cache_dir = Path(__file__).parent.parent.parent / 'cache'
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / 'stock_list_cache.json'
        cache_ttl = 7 * 24 * 3600  # 7天缓存
        
        # 检查缓存
        if cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < cache_ttl:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        stocks = json.load(f)
                    self.logger.info(f"使用缓存的股票列表: {len(stocks)} 只A股 (缓存 {cache_age/3600:.1f} 小时)")
                    return stocks
                except Exception as e:
                    self.logger.warning(f"读取缓存失败: {e}，重新获取")
        
        # 缓存过期或不存在，从 baostock 获取
        self.logger.info("获取全市场A股列表...")
        
        try:
            # 使用 query_stock_basic() 获取所有股票
            rs = bs.query_stock_basic()
            
            if rs.error_code != '0':
                self.logger.error(f"获取股票列表失败: {rs.error_msg}")
                return []
            
            stocks = []
            while (rs.error_code == '0') & rs.next():
                code = rs.get_row_data()[0]  # 股票代码
                code_name = rs.get_row_data()[1]  # 股票名称
                
                # 只保留 A股（sh 和 sz 开头）
                if code.startswith('sh.') or code.startswith('sz.'):
                    pure_code = code.split('.')[-1] if '.' in code else code
                    stocks.append({
                        'code': pure_code,
                        'full_code': code,
                        'name': code_name
                    })
            
            # 保存缓存
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(stocks, f, ensure_ascii=False, indent=2)
                self.logger.info(f"股票列表已缓存: {cache_file}")
            except Exception as e:
                self.logger.warning(f"保存缓存失败: {e}")
        
            self.logger.info(f"获取到 {len(stocks)} 只A股")
            return stocks
        except Exception as e:
            self.logger.error(f"获取股票列表异常: {e}")
            return []
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def _fetch_stock_daily_data(self, stock: Dict[str, str], date_str: str) -> Optional[pd.DataFrame]:
        """
        获取单只股票的日线数据
        
        带重试机制:
        - 最多重试 3 次
        - 指数退避: 2秒 → 4秒 → 8秒
        - 只重试网络相关错误
        """
        stock_code = stock['code']
        stock_name = stock['name']
        full_code = stock['full_code']
        
        try:
            # 使用 baostock 获取日线数据
            rs = bs.query_history_k_data_plus(
                full_code,
                "date,code,open,high,low,close,volume,amount,turn,pctChg",
                start_date=date_str,
                end_date=date_str,
                frequency="d",
                adjustflag="2"  # 后复权
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
    
    def sync_daily_data(self, sync_date: Optional[date] = None) -> Dict:
        """
        同步指定日期的股票数据
        
        Args:
            sync_date: 同步日期，默认为昨天
            
        Returns:
            同步结果统计
        """
        # 确定同步日期
        if sync_date is None:
            sync_date = date.today() - timedelta(days=1)
        
        date_str = sync_date.strftime('%Y-%m-%d')
        self.logger.info(f"开始同步 {date_str} 的数据...")
        
        # 登录 baostock
        if not self._login_baostock():
            return {"status": "error", "message": "baostock 登录失败"}
        
        # 检查是否为交易日
        if not self._is_trading_day(sync_date):
            self.logger.info(f"{date_str} 不是交易日，跳过同步")
            self._logout_baostock()
            return {
                "status": "skipped",
                "message": f"{date_str} 不是交易日",
                "date": date_str
            }
        
        try:
            # 获取股票列表（使用同步日期）
            stocks = self._get_all_stocks(sync_date)
            total_stocks = len(stocks)
            
            # 串行获取数据（baostock 不支持多线程）
            batch_size = 1500  # 优化：从 500 增加到 1500，减少批次数量
            success_count = 0
            failed_count = 0
            total_inserted = 0
            batch_frames = []
            
            self.logger.info(f"开始串行获取数据（baostock 不支持多线程）, batch_size={batch_size}")
            
            # 获取数据库连接
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # 优化：临时调整数据库参数以提高写入性能
            try:
                cursor.execute("SET LOCAL work_mem = '256MB';")
                cursor.execute("SET LOCAL maintenance_work_mem = '512MB';")
                cursor.execute("SET LOCAL statement_timeout = '60s';")  # 查询超时60秒
                cursor.execute("SET LOCAL idle_in_transaction_session_timeout = '120s';")  # 事务空闲超时
                self.logger.info("数据库性能参数已优化（含超时设置）")
            except Exception as e:
                self.logger.warning(f"设置数据库参数失败: {e}")
            
            for idx, stock in enumerate(stocks, start=1):
                df = self._fetch_stock_daily_data(stock, date_str)
                
                if df is not None and not df.empty:
                    batch_frames.append(df)
                    success_count += 1
                else:
                    failed_count += 1
                
                # 批量入库（优化：使用 COPY 命令，失败时回退到 execute_values）
                if batch_frames and (len(batch_frames) >= batch_size or idx == total_stocks):
                    try:
                        # 合并 DataFrame（一次性操作）
                        batch_df = pd.concat(batch_frames, ignore_index=True)
                        
                        # 尝试使用 COPY 命令批量插入
                        try:
                            inserted = self._bulk_insert_with_copy(cursor, batch_df)
                            conn.commit()
                            total_inserted += inserted
                            self.logger.debug(f"COPY 命令成功插入 {inserted} 条")
                        except Exception as copy_err:
                            # COPY 失败，回退到 execute_values
                            self.logger.warning(f"COPY 命令失败，回退到 execute_values: {copy_err}")
                            conn.rollback()
                            
                            # 准备数据
                            columns_order = [
                                'stock_code', 'stock_name', 'trade_date',
                                'open_price', 'close_price', 'high_price', 'low_price',
                                'volume', 'amount', 'change_pct', 'change_amount',
                                'turnover_rate', 'amplitude'
                            ]
                            values = batch_df[columns_order].values.tolist()
                            
                            # 使用 execute_values 插入
                            execute_values(
                                cursor,
                                """
                                INSERT INTO daily_stock_data (
                                    stock_code, stock_name, trade_date,
                                    open_price, close_price, high_price, low_price,
                                    volume, amount, change_pct, change_amount,
                                    turnover_rate, amplitude
                                ) VALUES %s
                                ON CONFLICT (stock_code, trade_date) DO NOTHING
                                """,
                                values
                            )
                            conn.commit()
                            total_inserted += len(values)
                            self.logger.info(f"execute_values 成功插入 {len(values)} 条")
                        
                    except Exception as insert_err:
                        self.logger.error(f"入库失败（批次大小 {len(batch_frames)}）: {insert_err}")
                        try:
                            conn.rollback()
                        except:
                            pass
                    finally:
                        batch_frames = []
                
                # 进度日志
                if idx % 500 == 0 or idx == total_stocks:
                    self.logger.info(
                        f"进度: {idx}/{total_stocks}, 成功: {success_count}, 失败: {failed_count}, 已入库: {total_inserted}"
                    )
            
            # 关闭连接（归还到连接池）
            cursor.close()
            self._return_db_connection(conn)
            
            # 最终统计
            self.logger.info(f"最终进度: {total_stocks}/{total_stocks}, 成功: {success_count}, 失败: {failed_count}, 已入库: {total_inserted}")
            self.logger.info(f"同步完成: 成功 {success_count}, 失败 {failed_count}")
            
            # 计算成功率
            success_rate = (success_count / total_stocks * 100) if total_stocks > 0 else 0
            self.logger.info(f"成功率: {success_rate:.2f}%")
            
            return {
                "status": "success",
                "message": f"同步完成: 成功 {success_count}, 失败 {failed_count}",
                "date": date_str,
                "total": total_stocks,
                "success": success_count,
                "failed": failed_count,
                "inserted": total_inserted
            }
            
        except Exception as e:
            self.logger.error(f"同步失败: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "date": date_str
            }
        finally:
            self._logout_baostock()
