"""
带状态管理的每日数据同步服务
集成同步状态表，实现智能同步管理
"""

import os
import logging
import subprocess
from datetime import date, timedelta
from typing import Dict, List
from pathlib import Path

from app.services.sync_status_service import SyncStatusService

logger = logging.getLogger(__name__)


class DailySyncWithStatus:
    """带状态管理的每日同步服务"""
    
    def __init__(self):
        self.status_service = SyncStatusService()
        # 获取项目根目录
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent.parent  # 到backend目录
        self.project_root = backend_dir.parent.parent  # 到StockGuru目录
        self.sync_script = self.project_root / 'scripts' / 'test_copy_sync.py'
    
    async def sync_date_with_status(self, sync_date: date) -> Dict:
        """
        同步指定日期的数据（带状态管理）
        
        Args:
            sync_date: 要同步的日期
            
        Returns:
            同步结果
        """
        # 1. 检查是否需要同步
        need_sync, reason = self.status_service.check_need_sync(sync_date)
        
        if not need_sync:
            logger.info(f"{sync_date}: {reason}")
            return {
                'status': 'skipped',
                'date': sync_date.isoformat(),
                'message': reason
            }
        
        logger.info(f"{sync_date}: 开始同步 - {reason}")
        
        # 2. 标记为同步中
        process_id = str(os.getpid())
        self.status_service.mark_as_syncing(sync_date, process_id)
        
        try:
            # 3. 执行同步（调用同步脚本）
            date_str = sync_date.isoformat()
            cmd = ['python3', str(self.sync_script), '--all', '--date', date_str]
            
            result_proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            # 4. 检查同步结果（从数据库查询）
            import time
            time.sleep(2)  # 等待数据库写入
            
            status = self.status_service.get_status(sync_date)
            
            if status and status.get('status') == 'success':
                logger.info(f"{sync_date}: 同步成功 - {status.get('total_records', 0)} 条")
                return {
                    'status': 'success',
                    'date': date_str,
                    'total_records': status.get('total_records', 0),
                    'message': '同步成功'
                }
            elif status and status.get('status') == 'skipped':
                logger.info(f"{sync_date}: 跳过 - 非交易日")
                return {
                    'status': 'skipped',
                    'date': date_str,
                    'message': '非交易日'
                }
            else:
                # 失败或无状态
                error_msg = result_proc.stderr if result_proc.returncode != 0 else '同步失败'
                logger.error(f"{sync_date}: 同步失败 - {error_msg}")
                return {
                    'status': 'failed',
                    'date': date_str,
                    'error': error_msg
                }
            
        except Exception as e:
            # 5. 异常处理
            error_msg = str(e)
            logger.error(f"{sync_date}: 同步异常 - {error_msg}", exc_info=True)
            
            self.status_service.mark_as_failed(
                sync_date=sync_date,
                error_message=error_msg
            )
            
            return {
                'status': 'failed',
                'date': sync_date.isoformat(),
                'error': error_msg
            }
    
    async def sync_today(self) -> Dict:
        """同步今日数据"""
        today = date.today()
        return await self.sync_date_with_status(today)
    
    async def sync_pending_dates(self, days_back: int = 30) -> Dict:
        """
        同步所有待同步的日期
        
        Args:
            days_back: 向前查找多少天
            
        Returns:
            同步结果汇总
        """
        # 获取待同步日期列表
        pending_dates = self.status_service.get_pending_dates(days_back)
        
        if not pending_dates:
            logger.info("没有待同步的日期")
            return {
                'status': 'success',
                'message': '没有待同步的日期',
                'synced_dates': []
            }
        
        logger.info(f"发现 {len(pending_dates)} 个待同步日期: {pending_dates}")
        
        # 逐个同步
        results = []
        for sync_date in pending_dates:
            result = await self.sync_date_with_status(sync_date)
            results.append({
                'date': sync_date.isoformat(),
                'status': result['status'],
                'message': result.get('message', result.get('error', ''))
            })
        
        # 统计
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count = sum(1 for r in results if r['status'] == 'failed')
        skipped_count = sum(1 for r in results if r['status'] == 'skipped')
        
        return {
            'status': 'success' if failed_count == 0 else 'partial',
            'total': len(results),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'results': results
        }
    
    def get_sync_status_summary(self, days: int = 30) -> Dict:
        """
        获取同步状态摘要
        
        Args:
            days: 查询最近多少天
            
        Returns:
            状态摘要
        """
        recent_status = self.status_service.get_recent_status(days)
        
        # 统计
        status_count = {
            'pending': 0,
            'syncing': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for record in recent_status:
            status = record['status']
            if status in status_count:
                status_count[status] += 1
        
        return {
            'total_days': len(recent_status),
            'status_count': status_count,
            'recent_records': recent_status[:10]  # 最近10条
        }


# 全局实例
_daily_sync_service = None

def get_daily_sync_service() -> DailySyncWithStatus:
    """获取每日同步服务实例"""
    global _daily_sync_service
    if _daily_sync_service is None:
        _daily_sync_service = DailySyncWithStatus()
    return _daily_sync_service
