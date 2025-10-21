"""
定时任务调度器
使用 APScheduler 实现每日数据同步
"""

import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

logger = logging.getLogger(__name__)

# 导入统一的同步管理器
from app.services.sync_manager import get_sync_manager


class DataSyncScheduler:
    """数据同步调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler()
        self.logger = logging.getLogger(__name__)
        # 不再使用局部锁，使用统一的同步管理器
    
    async def sync_today_data(self):
        """
        同步今日数据的任务
        每天19点执行，如果失败则每小时重试
        """
        sync_manager = get_sync_manager()
        
        # 检查是否有任务正在运行
        if sync_manager.is_syncing():
            current_task = sync_manager.get_current_task()
            self.logger.info(f"同步任务正在进行中，跳过本次执行: {current_task}")
            return
        
        try:
            self.logger.info("开始执行每日数据同步任务...")
            
            # 同步今天的数据
            today = date.today()
            
            # 使用统一的同步管理器
            result = sync_manager.sync_date_range(
                start_date=today,
                end_date=today,
                task_type='scheduler_daily'
            )
            
            if result['status'] == 'success':
                self.logger.info(f"今日数据同步成功: {result}")
                # 成功后取消重试任务
                if self.scheduler.get_job('retry_sync'):
                    self.scheduler.remove_job('retry_sync')
            elif result['status'] == 'skipped':
                self.logger.info(f"今日非交易日，跳过同步")
                # 非交易日也取消重试
                if self.scheduler.get_job('retry_sync'):
                    self.scheduler.remove_job('retry_sync')
            else:
                self.logger.warning(f"今日数据同步失败，将在1小时后重试")
                # 添加重试任务（如果不存在）
                if not self.scheduler.get_job('retry_sync'):
                    self.scheduler.add_job(
                        self.sync_today_data,
                        trigger=IntervalTrigger(hours=1),
                        id='retry_sync',
                        name='每小时重试同步',
                        replace_existing=True
                    )
            
        except Exception as e:
            self.logger.error(f"同步任务执行失败: {e}", exc_info=True)
            # 添加重试任务
            if not self.scheduler.get_job('retry_sync'):
                self.scheduler.add_job(
                    self.sync_today_data,
                    trigger=IntervalTrigger(hours=1),
                    id='retry_sync',
                    name='每小时重试同步',
                    replace_existing=True
                )
        finally:
            # 同步锁由 sync_manager 管理
            pass
    
    async def check_and_sync_missing_days(self):
        """
        检查并同步缺失的交易日数据
        每天早上8点执行
        """
        try:
            self.logger.info("检查缺失的交易日数据...")
            
            from app.services.daily_data_sync_service import get_sync_service
            sync_service = get_sync_service()
            supabase = sync_service._get_supabase()
            
            if not supabase:
                self.logger.error("Supabase 未连接")
                return
            
            # 获取最近30天的交易日
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            # 查询已同步的日期
            response = supabase.table('sync_logs')\
                .select('sync_date')\
                .eq('status', 'success')\
                .gte('sync_date', start_date.isoformat())\
                .execute()
            
            synced_dates = set(row['sync_date'] for row in response.data)
            
            # 检查每一天
            current_date = start_date
            missing_dates = []
            
            while current_date <= end_date:
                if sync_service.is_trading_day(current_date):
                    if current_date.isoformat() not in synced_dates:
                        missing_dates.append(current_date)
                current_date += timedelta(days=1)
            
            if missing_dates:
                self.logger.info(f"发现 {len(missing_dates)} 个缺失的交易日: {missing_dates}")
                
                # 同步缺失的日期
                for missing_date in missing_dates:
                    try:
                        result = await sync_service.sync_date_data(missing_date)
                        self.logger.info(f"补充同步 {missing_date}: {result}")
                        await asyncio.sleep(2)  # 避免请求过快
                    except Exception as e:
                        self.logger.error(f"补充同步 {missing_date} 失败: {e}")
            else:
                self.logger.info("没有缺失的交易日数据")
            
        except Exception as e:
            self.logger.error(f"检查缺失数据失败: {e}", exc_info=True)
    
    def start(self):
        """启动调度器"""
        try:
            # 每天19点执行同步任务
            self.scheduler.add_job(
                self.sync_today_data,
                trigger=CronTrigger(hour=19, minute=0),
                id='daily_sync',
                name='每日19点同步数据',
                replace_existing=True
            )
            
            # 每天早上8点检查缺失数据
            self.scheduler.add_job(
                self.check_and_sync_missing_days,
                trigger=CronTrigger(hour=8, minute=0),
                id='check_missing',
                name='每日8点检查缺失数据',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.logger.info("定时任务调度器已启动")
            self.logger.info("- 每日19点: 同步当日数据")
            self.logger.info("- 每日8点: 检查缺失数据")
            
        except Exception as e:
            self.logger.error(f"启动调度器失败: {e}")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("定时任务调度器已关闭")


# 全局调度器实例
_scheduler = None

def get_scheduler() -> DataSyncScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataSyncScheduler()
    return _scheduler
