#!/usr/bin/env python3
"""
改进版批量同步脚本
集成配置管理、异常处理、交易日历等改进
"""

import os
import sys
import logging
import argparse
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from psycopg2 import pool

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入自定义模块
from scripts.sync_config import config
from scripts.sync_exceptions import (
    SyncException, DatabaseConnectionError, ProcessTimeoutError,
    classify_exception, should_retry, get_retry_delay
)
from scripts.trading_calendar import TradingCalendar

# 配置日志
from logging.handlers import RotatingFileHandler

def setup_logging():
    """配置日志系统"""
    # 确保日志目录存在
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()


class ImprovedBatchSyncManager:
    """改进版批量同步管理器"""
    
    def __init__(self):
        """初始化"""
        logger.info("初始化批量同步管理器...")
        
        # 验证配置
        try:
            config.validate()
            logger.info("配置验证通过")
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            raise
        
        # 创建连接池
        try:
            self.db_pool = pool.ThreadedConnectionPool(
                minconn=config.DB_POOL_MIN_CONN,
                maxconn=config.DB_POOL_MAX_CONN,
                dsn=config.DATABASE_URL,
                connect_timeout=config.DB_CONNECT_TIMEOUT
            )
            logger.info(f"数据库连接池创建成功 (min={config.DB_POOL_MIN_CONN}, max={config.DB_POOL_MAX_CONN})")
        except Exception as e:
            logger.error(f"数据库连接池创建失败: {e}")
            raise DatabaseConnectionError(f"连接池创建失败: {e}")
        
        # 创建交易日历
        conn = self.get_connection()
        try:
            self.calendar = TradingCalendar(
                method=config.TRADING_DAY_METHOD,
                db_conn=conn
            )
            logger.info(f"交易日历初始化完成 (method={config.TRADING_DAY_METHOD})")
        finally:
            self.put_connection(conn)
        
        # 性能指标
        self.metrics = {
            'total_dates': 0,
            'success_dates': 0,
            'failed_dates': 0,
            'skipped_dates': 0,
            'total_records': 0,
            'total_duration': 0,
            'start_time': None,
            'end_time': None
        }
    
    def get_connection(self):
        """从连接池获取连接"""
        try:
            return self.db_pool.getconn()
        except Exception as e:
            logger.error(f"获取数据库连接失败: {e}")
            raise DatabaseConnectionError(f"获取连接失败: {e}")
    
    def put_connection(self, conn):
        """归还连接到连接池"""
        try:
            self.db_pool.putconn(conn)
        except Exception as e:
            logger.warning(f"归还连接失败: {e}")
    
    def health_check(self) -> bool:
        """健康检查"""
        if not config.ENABLE_HEALTH_CHECK:
            return True
        
        logger.info("执行健康检查...")
        
        # 检查数据库
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            self.put_connection(conn)
            logger.info("✅ 数据库健康检查通过")
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {e}")
            return False
        
        # 检查 baostock
        try:
            import baostock as bs
            result = bs.login()
            if result.error_code == '0':
                bs.logout()
                logger.info("✅ Baostock 健康检查通过")
            else:
                logger.error(f"❌ Baostock 健康检查失败: {result.error_msg}")
                return False
        except Exception as e:
            logger.error(f"❌ Baostock 健康检查失败: {e}")
            return False
        
        return True
    
    def is_trading_day(self, date_str: str) -> bool:
        """判断是否为交易日"""
        return self.calendar.is_trading_day(date_str)
    
    def get_sync_status(self, date_str: str) -> dict:
        """获取同步状态"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, total_records, success_count, error_message
                FROM daily_sync_status
                WHERE sync_date = %s
            """, (date_str,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'status': result[0],
                    'total_records': result[1],
                    'success_count': result[2],
                    'error_message': result[3]
                }
            return None
        finally:
            self.put_connection(conn)
    
    def update_sync_status(self, date_str: str, status: str, total_records: int,
                          success_count: int, start_time: str, end_time: str,
                          duration_seconds: int, error_message: str = None):
        """更新同步状态"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 尝试更新
            cursor.execute("""
                UPDATE daily_sync_status
                SET
                    status = %s,
                    total_records = %s,
                    success_count = %s,
                    failed_count = %s,
                    start_time = %s,
                    end_time = %s,
                    duration_seconds = %s,
                    error_message = %s,
                    remarks = %s,
                    updated_at = NOW()
                WHERE sync_date = %s
                RETURNING sync_date
            """, (
                status, total_records, success_count,
                total_records - success_count,
                start_time, end_time, duration_seconds, error_message,
                f'批量同步，共{total_records}条，成功{success_count}条',
                date_str
            ))
            
            result = cursor.fetchone()
            
            if not result:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO daily_sync_status (
                        sync_date, status, total_records, success_count, failed_count,
                        start_time, end_time, duration_seconds, error_message, remarks,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """, (
                    date_str, status, total_records, success_count,
                    total_records - success_count,
                    start_time, end_time, duration_seconds, error_message,
                    f'批量同步，共{total_records}条，成功{success_count}条'
                ))
            
            conn.commit()
            cursor.close()
            logger.info(f"✅ {date_str} 状态已更新: {status}")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 更新状态失败: {e}")
            raise
        finally:
            self.put_connection(conn)
    
    def monitor_sync_process(self, process, date_str: str) -> bool:
        """监控同步进程"""
        error_count = 0
        last_error_time = None
        start_time = time.time()
        
        while True:
            # 检查超时
            if time.time() - start_time > config.SYNC_TIMEOUT_SECONDS:
                logger.error(f"❌ {date_str} 同步超时 ({config.SYNC_TIMEOUT_SECONDS}秒)")
                process.terminate()
                time.sleep(2)
                if process.poll() is None:
                    process.kill()
                raise ProcessTimeoutError(f"同步超时: {config.SYNC_TIMEOUT_SECONDS}秒")
            
            # 读取输出
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                line = line.strip()
                print(line)  # 实时输出
                
                # 检测错误（排除进度日志中的正常信息）
                if ('❌' in line or 'ERROR' in line or '失败' in line) and '预计剩余' not in line and '进度:' not in line:
                    current_time = time.time()
                    
                    # 重置计数器（超过时间窗口）
                    if last_error_time and (current_time - last_error_time) > config.ERROR_WINDOW_SECONDS:
                        error_count = 0
                    
                    error_count += 1
                    last_error_time = current_time
                    
                    logger.warning(f"⚠️  检测到错误 ({error_count}/{config.MAX_ERROR_COUNT})")
                    
                    # 超过阈值，终止进程
                    if error_count >= config.MAX_ERROR_COUNT:
                        logger.error(f"❌ {date_str} 持续错误 ({error_count}次)，终止同步")
                        process.terminate()
                        time.sleep(2)
                        if process.poll() is None:
                            process.kill()
                        return False
        
        return process.returncode == 0
    
    def is_sync_process_running(self, date_str: str) -> bool:
        """检查指定日期的同步进程是否正在运行"""
        try:
            import subprocess
            # 查找包含该日期的同步进程
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            # 检查是否有该日期的同步进程
            for line in result.stdout.split('\n'):
                if 'test_copy_sync.py' in line and date_str in line and 'grep' not in line:
                    logger.warning(f"⚠️  检测到 {date_str} 的同步进程正在运行")
                    # 提取PID
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        logger.warning(f"   进程PID: {pid}")
                    return True
            return False
        except Exception as e:
            logger.warning(f"检查进程状态失败: {e}")
            return False
    
    def sync_date_with_retry(self, date_str: str) -> bool:
        """同步单个日期（支持重试）"""
        logger.info(f"\n{'='*80}")
        logger.info(f"开始同步: {date_str}")
        logger.info(f"{'='*80}\n")
        
        # 检查是否有同步进程正在运行
        if self.is_sync_process_running(date_str):
            logger.warning(f"⚠️  {date_str} 已有同步进程在运行，跳过")
            self.metrics['skipped_dates'] += 1
            return True
        
        # 检查是否为交易日
        if not self.is_trading_day(date_str):
            logger.info(f"⚠️  {date_str} 非交易日，跳过")
            # 写入数据库记录
            start_time = datetime.now()
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_time_str = start_time_str
            self.update_sync_status(
                date_str, 'skipped', 0, 0,
                start_time_str, end_time_str, 0,
                error_message='非交易日（周末/节假日）'
            )
            self.metrics['skipped_dates'] += 1
            return True
        
        # 检查是否已同步
        sync_status = self.get_sync_status(date_str)
        if sync_status and sync_status['status'] == 'success':
            logger.info(f"✅ {date_str} 已同步完成 ({sync_status['success_count']} 条)，跳过")
            self.metrics['skipped_dates'] += 1
            return True
        
        # 重试循环
        for attempt in range(1, config.MAX_RETRIES_PER_DATE + 1):
            logger.info(f"\n🔄 尝试 {attempt}/{config.MAX_RETRIES_PER_DATE}")
            
            start_time = datetime.now()
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                # 启动同步进程
                process = subprocess.Popen(
                    ['python3', 'scripts/test_copy_sync.py', '--all', '--date', date_str],
                    cwd=project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # 监控进程
                success = self.monitor_sync_process(process, date_str)
                
                # 记录结束时间
                end_time = datetime.now()
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                duration_seconds = int((end_time - start_time).total_seconds())
                
                if success:
                    # 查询实际同步数量
                    conn = self.get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM daily_stock_data 
                            WHERE trade_date = %s
                        """, (date_str,))
                        success_count = cursor.fetchone()[0]
                        cursor.close()
                    finally:
                        self.put_connection(conn)
                    
                    if success_count > 0:
                        # 有数据：正常交易日
                        self.update_sync_status(
                            date_str, 'success', success_count, success_count,
                            start_time_str, end_time_str, duration_seconds
                        )
                        
                        # 更新指标
                        self.metrics['success_dates'] += 1
                        self.metrics['total_records'] += success_count
                        self.metrics['total_duration'] += duration_seconds
                        
                        logger.info(f"\n✅ {date_str} 同步成功")
                        logger.info(f"   记录数: {success_count:,}")
                        logger.info(f"   耗时: {duration_seconds}秒 ({duration_seconds/60:.1f}分钟)\n")
                        return True
                    else:
                        # 无数据：非交易日（节假日/周末）
                        self.update_sync_status(
                            date_str, 'skipped', 0, 0,
                            start_time_str, end_time_str, duration_seconds,
                            error_message='非交易日，无数据'
                        )
                        
                        self.metrics['skipped_dates'] += 1
                        
                        logger.info(f"\n⚠️  {date_str} 非交易日（0条数据）")
                        logger.info(f"   耗时: {duration_seconds}秒\n")
                        return True
                
                # 失败处理
                if attempt < config.MAX_RETRIES_PER_DATE:
                    retry_delay = config.RETRY_WAIT_SECONDS
                    logger.warning(f"⚠️  尝试 {attempt} 失败，等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 最后一次失败
                    error_message = f"重试{config.MAX_RETRIES_PER_DATE}次后仍然失败"
                    self.update_sync_status(
                        date_str, 'failed', 0, 0,
                        start_time_str, end_time_str, duration_seconds, error_message
                    )
                    self.metrics['failed_dates'] += 1
                    logger.error(f"\n❌ {date_str} 同步失败（已重试{config.MAX_RETRIES_PER_DATE}次）\n")
                    return False
            
            except SyncException as e:
                # 自定义异常
                logger.error(f"❌ 尝试 {attempt} 异常: {e}")
                
                if not should_retry(e):
                    logger.error(f"❌ 异常不可重试，放弃")
                    end_time = datetime.now()
                    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                    duration_seconds = int((end_time - start_time).total_seconds())
                    self.update_sync_status(
                        date_str, 'failed', 0, 0,
                        start_time_str, end_time_str, duration_seconds, str(e)
                    )
                    self.metrics['failed_dates'] += 1
                    return False
                
                if attempt < config.MAX_RETRIES_PER_DATE:
                    retry_delay = get_retry_delay(e, attempt, config.RETRY_WAIT_SECONDS)
                    logger.warning(f"⚠️  等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
            
            except Exception as e:
                # 未分类异常
                classified_exc = classify_exception(e)
                logger.error(f"❌ 尝试 {attempt} 异常: {classified_exc}")
                
                if attempt < config.MAX_RETRIES_PER_DATE:
                    retry_delay = get_retry_delay(classified_exc, attempt, config.RETRY_WAIT_SECONDS)
                    logger.warning(f"⚠️  等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
        
        return False
    
    def batch_sync(self, dates: list):
        """批量同步"""
        logger.info(f"\n{'='*80}")
        logger.info(f"批量同步任务开始")
        logger.info(f"待同步日期: {len(dates)} 个")
        logger.info(f"{'='*80}\n")
        
        # 健康检查
        if not self.health_check():
            logger.error("❌ 健康检查失败，终止同步")
            return
        
        # 初始化指标
        self.metrics['total_dates'] = len(dates)
        self.metrics['start_time'] = datetime.now()
        
        failed_dates = []
        
        # 遍历日期
        for idx, date_str in enumerate(dates, 1):
            logger.info(f"\n📅 处理日期 {idx}/{len(dates)}: {date_str}")
            
            try:
                result = self.sync_date_with_retry(date_str)
                if not result:
                    failed_dates.append(date_str)
                    logger.warning(f"⚠️  {date_str} 失败，继续下一个")
            except Exception as e:
                failed_dates.append(date_str)
                logger.error(f"❌ {date_str} 异常: {e}")
                logger.warning(f"⚠️  跳过 {date_str}，继续下一个")
            
            # 日期间隔
            if idx < len(dates):
                time.sleep(config.DATE_INTERVAL_SECONDS)
        
        # 记录结束时间
        self.metrics['end_time'] = datetime.now()
        
        # 输出统计
        self.print_summary(failed_dates)
    
    def print_summary(self, failed_dates: list):
        """打印统计摘要"""
        logger.info(f"\n{'='*80}")
        logger.info(f"批量同步任务完成")
        logger.info(f"{'='*80}")
        logger.info(f"✅ 成功: {self.metrics['success_dates']}")
        logger.info(f"❌ 失败: {self.metrics['failed_dates']}")
        logger.info(f"⏭️  跳过: {self.metrics['skipped_dates']}")
        logger.info(f"📊 总记录: {self.metrics['total_records']:,}")
        
        if self.metrics['start_time'] and self.metrics['end_time']:
            total_time = (self.metrics['end_time'] - self.metrics['start_time']).total_seconds()
            logger.info(f"⏱️  总耗时: {total_time:.0f}秒 ({total_time/60:.1f}分钟)")
        
        if self.metrics['success_dates'] > 0:
            avg_duration = self.metrics['total_duration'] / self.metrics['success_dates']
            avg_records = self.metrics['total_records'] / self.metrics['success_dates']
            logger.info(f"📈 平均耗时: {avg_duration:.0f}秒/日")
            logger.info(f"📈 平均记录: {avg_records:.0f}条/日")
        
        if failed_dates:
            logger.info(f"失败日期: {', '.join(failed_dates)}")
        
        logger.info(f"{'='*80}\n")
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'db_pool'):
            self.db_pool.closeall()
            logger.info("数据库连接池已关闭")


def generate_date_range(start_date: str, end_date: str) -> list:
    """生成日期范围"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return dates


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='改进版批量同步脚本')
    parser.add_argument('--dates', nargs='+', help='指定日期列表')
    parser.add_argument('--start', help='起始日期')
    parser.add_argument('--end', help='结束日期')
    parser.add_argument('--config', action='store_true', help='显示配置')
    
    args = parser.parse_args()
    
    # 显示配置
    if args.config:
        config.print_config()
        return
    
    # 确定日期列表
    dates = []
    if args.dates:
        dates = args.dates
    elif args.start and args.end:
        dates = generate_date_range(args.start, args.end)
    else:
        parser.print_help()
        sys.exit(1)
    
    # 执行同步
    manager = ImprovedBatchSyncManager()
    try:
        manager.batch_sync(dates)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
    except Exception as e:
        logger.error(f"\n❌ 批量同步异常: {e}", exc_info=True)
    finally:
        manager.close()


if __name__ == '__main__':
    main()
