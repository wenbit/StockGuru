#!/usr/bin/env python3
"""
批量同步多个日期的股票数据
自动更新 daily_sync_status 表
支持断点续传

使用方法:
    python scripts/batch_sync_dates.py --dates 2025-10-14 2025-10-16
    python scripts/batch_sync_dates.py --start 2025-10-10 --end 2025-10-16
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class BatchSyncManager:
    """批量同步管理器"""
    
    def __init__(self):
        """初始化"""
        database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        if not database_url:
            raise ValueError("请设置 DATABASE_URL 环境变量")
        
        self.database_url = database_url
        self.conn = psycopg2.connect(database_url)
        logger.info("数据库连接成功")
    
    def is_trading_day(self, date_str: str) -> bool:
        """检查是否为交易日（简单判断：非周末）"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # 0=周一, 6=周日
        return date_obj.weekday() < 5
    
    def get_sync_status(self, date_str: str) -> dict:
        """获取指定日期的同步状态"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT status, total_records, success_count
            FROM daily_sync_status
            WHERE sync_date = %s
        """, (date_str,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'status': result[0],
                'total_records': result[1],
                'success_count': result[2]
            }
        return None
    
    def update_sync_status(self, date_str: str, status: str, total_records: int, 
                          success_count: int, start_time: str, end_time: str, 
                          duration_seconds: int, error_message: str = None):
        """更新同步状态"""
        cursor = self.conn.cursor()
        
        # 先尝试更新
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
            f'批量同步完成，共获取{total_records}只股票，成功入库{success_count}条',
            date_str
        ))
        
        result = cursor.fetchone()
        
        if not result:
            # 如果没有记录，插入新记录
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
                f'批量同步完成，共获取{total_records}只股票，成功入库{success_count}条'
            ))
        
        self.conn.commit()
        cursor.close()
        logger.info(f"✅ {date_str} 同步状态已更新")
    
    def monitor_sync_process(self, process, date_str: str, max_error_count: int = 10) -> bool:
        """监控同步进程，检测持续错误"""
        import select
        import sys
        
        error_count = 0
        last_error_time = None
        error_window = 30  # 30秒内的错误计数
        
        while True:
            # 读取输出
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                line = line.strip()
                # 实时打印输出
                print(line)
                
                # 检测错误
                if '❌' in line or 'ERROR' in line or '失败' in line:
                    current_time = time.time()
                    
                    # 重置计数器（如果距离上次错误超过时间窗口）
                    if last_error_time and (current_time - last_error_time) > error_window:
                        error_count = 0
                    
                    error_count += 1
                    last_error_time = current_time
                    
                    logger.warning(f"⚠️  检测到错误 ({error_count}/{max_error_count})")
                    
                    # 如果错误过多，终止进程
                    if error_count >= max_error_count:
                        logger.error(f"❌ {date_str} 持续出现错误（{error_count}次），终止同步")
                        process.terminate()
                        time.sleep(2)
                        if process.poll() is None:
                            process.kill()
                        return False
        
        return process.returncode == 0
    
    def sync_date_with_retry(self, date_str: str, max_retries: int = 3) -> bool:
        """同步单个日期，支持重试"""
        logger.info(f"\n{'='*80}")
        logger.info(f"开始同步: {date_str}")
        logger.info(f"{'='*80}\n")
        
        # 检查是否为交易日
        if not self.is_trading_day(date_str):
            logger.info(f"⚠️  {date_str} 是周末，跳过")
            return True
        
        # 检查是否已同步
        sync_status = self.get_sync_status(date_str)
        if sync_status and sync_status['status'] == 'success':
            logger.info(f"✅ {date_str} 已同步完成（{sync_status['success_count']} 条记录），跳过")
            return True
        
        # 重试循环
        for attempt in range(1, max_retries + 1):
            logger.info(f"\n🔄 尝试 {attempt}/{max_retries}")
            
            # 记录开始时间
            start_time = datetime.now()
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                # 调用同步脚本
                import subprocess
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
                    # 查询数据库获取实际同步数量
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM daily_stock_data 
                        WHERE trade_date = %s
                    """, (date_str,))
                    success_count = cursor.fetchone()[0]
                    cursor.close()
                    
                    if success_count > 0:
                        # 更新状态
                        self.update_sync_status(
                            date_str, 'success', success_count, success_count,
                            start_time_str, end_time_str, duration_seconds
                        )
                        
                        logger.info(f"\n✅ {date_str} 同步成功")
                        logger.info(f"   总数: {success_count:,}")
                        logger.info(f"   成功: {success_count:,}")
                        logger.info(f"   耗时: {duration_seconds} 秒 ({duration_seconds/60:.1f} 分钟)\n")
                        return True
                    else:
                        logger.warning(f"⚠️  同步完成但未找到数据")
                
                # 如果失败且还有重试机会
                if attempt < max_retries:
                    logger.warning(f"⚠️  尝试 {attempt} 失败，等待5秒后重试...")
                    time.sleep(5)
                else:
                    # 最后一次尝试失败，更新状态
                    error_message = f"重试{max_retries}次后仍然失败"
                    self.update_sync_status(
                        date_str, 'failed', 0, 0,
                        start_time_str, end_time_str, duration_seconds, error_message
                    )
                    logger.error(f"\n❌ {date_str} 同步失败（已重试{max_retries}次）\n")
                    return False
                    
            except Exception as e:
                end_time = datetime.now()
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
                duration_seconds = int((end_time - start_time).total_seconds())
                
                logger.error(f"❌ 尝试 {attempt} 异常: {e}")
                
                if attempt < max_retries:
                    logger.warning(f"⚠️  等待5秒后重试...")
                    time.sleep(5)
                else:
                    # 最后一次尝试异常，更新状态
                    error_message = f"重试{max_retries}次后仍然异常: {str(e)[:500]}"
                    self.update_sync_status(
                        date_str, 'failed', 0, 0,
                        start_time_str, end_time_str, duration_seconds, error_message
                    )
                    logger.error(f"\n❌ {date_str} 同步异常（已重试{max_retries}次）\n")
                    return False
        
        return False
    
    def sync_date(self, date_str: str) -> bool:
        """同步单个日期（兼容旧接口）"""
        return self.sync_date_with_retry(date_str, max_retries=3)
    
    def batch_sync(self, dates: list):
        """批量同步多个日期"""
        logger.info(f"\n{'='*80}")
        logger.info(f"批量同步任务开始")
        logger.info(f"待同步日期: {len(dates)} 个")
        logger.info(f"{'='*80}\n")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        failed_dates = []
        
        for idx, date_str in enumerate(dates, 1):
            logger.info(f"\n📅 处理日期 {idx}/{len(dates)}: {date_str}")
            
            try:
                result = self.sync_date(date_str)
                if result:
                    success_count += 1
                    logger.info(f"✅ {date_str} 处理完成")
                else:
                    failed_count += 1
                    failed_dates.append(date_str)
                    logger.warning(f"⚠️  {date_str} 失败，已更新状态表，继续下一个日期")
            except Exception as e:
                failed_count += 1
                failed_dates.append(date_str)
                logger.error(f"❌ {date_str} 处理异常: {e}")
                logger.warning(f"⚠️  跳过 {date_str}，继续下一个日期")
            
            # 每个日期之间稍作停顿
            if idx < len(dates):
                time.sleep(2)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"批量同步任务完成")
        logger.info(f"{'='*80}")
        logger.info(f"✅ 成功: {success_count}")
        logger.info(f"❌ 失败: {failed_count}")
        if failed_dates:
            logger.info(f"失败日期: {', '.join(failed_dates)}")
        logger.info(f"{'='*80}\n")
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


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
    parser = argparse.ArgumentParser(description='批量同步多个日期的股票数据')
    parser.add_argument('--dates', nargs='+', help='指定日期列表，如: 2025-10-14 2025-10-16')
    parser.add_argument('--start', help='起始日期，如: 2025-10-10')
    parser.add_argument('--end', help='结束日期，如: 2025-10-16')
    
    args = parser.parse_args()
    
    # 确定要同步的日期列表
    dates = []
    if args.dates:
        dates = args.dates
    elif args.start and args.end:
        dates = generate_date_range(args.start, args.end)
    else:
        parser.print_help()
        sys.exit(1)
    
    # 执行批量同步
    manager = BatchSyncManager()
    try:
        manager.batch_sync(dates)
    finally:
        manager.close()


if __name__ == '__main__':
    main()
