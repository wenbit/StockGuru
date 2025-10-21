"""
统一的数据同步管理器
确保所有同步任务（Web界面、定时任务）使用同一个同步方法和全局锁
"""

import logging
import threading
from datetime import date, datetime, timedelta
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

# 全局同步锁和状态
_sync_lock = threading.Lock()
_is_syncing = False
_current_task_info: Optional[Dict] = None


class SyncManager:
    """统一的同步管理器"""
    
    @staticmethod
    def is_syncing() -> bool:
        """检查是否有同步任务正在运行"""
        global _is_syncing
        with _sync_lock:
            return _is_syncing
    
    @staticmethod
    def get_current_task() -> Optional[Dict]:
        """获取当前运行的任务信息"""
        global _current_task_info
        with _sync_lock:
            return _current_task_info.copy() if _current_task_info else None
    
    @staticmethod
    def acquire_sync_lock(task_type: str, task_info: Dict) -> bool:
        """
        尝试获取同步锁
        
        Args:
            task_type: 任务类型 (web_batch/scheduler_daily/scheduler_missing)
            task_info: 任务信息
        
        Returns:
            是否成功获取锁
        """
        global _is_syncing, _current_task_info
        
        with _sync_lock:
            if _is_syncing:
                logger.warning(f"同步任务正在进行中，拒绝新任务: {task_type}")
                logger.info(f"当前任务: {_current_task_info}")
                return False
            
            _is_syncing = True
            _current_task_info = {
                'task_type': task_type,
                'start_time': datetime.now().isoformat(),
                **task_info
            }
            logger.info(f"获取同步锁成功: {task_type}, 任务信息: {_current_task_info}")
            return True
    
    @staticmethod
    def release_sync_lock():
        """释放同步锁"""
        global _is_syncing, _current_task_info
        
        with _sync_lock:
            if _is_syncing:
                logger.info(f"释放同步锁: {_current_task_info}")
                _is_syncing = False
                _current_task_info = None
            else:
                logger.warning("尝试释放未持有的同步锁")
    
    @staticmethod
    def sync_date_range(
        start_date: date,
        end_date: date,
        task_type: str,
        progress_callback=None
    ) -> Dict:
        """
        同步日期范围的数据（统一的同步方法）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            task_type: 任务类型
            progress_callback: 进度回调函数
        
        Returns:
            同步结果
        """
        # 尝试获取锁
        task_info = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_days': (end_date - start_date).days + 1
        }
        
        if not SyncManager.acquire_sync_lock(task_type, task_info):
            return {
                'status': 'rejected',
                'message': '已有同步任务正在运行',
                'current_task': SyncManager.get_current_task()
            }
        
        try:
            # 使用 test_copy_sync 的同步逻辑
            import sys
            from pathlib import Path
            
            # 添加scripts目录到Python路径
            # __file__ -> sync_manager.py
            # parent -> services/
            # parent -> app/
            # parent -> backend/
            # parent -> stockguru-web/
            # parent -> StockGuru/ (真正的项目根目录)
            project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            scripts_dir = project_root / 'scripts'
            scripts_dir_str = str(scripts_dir)
            
            logger.info(f"项目根目录: {project_root}")
            logger.info(f"添加 scripts 目录到 Python 路径: {scripts_dir_str}")
            
            if scripts_dir_str not in sys.path:
                sys.path.insert(0, scripts_dir_str)
            
            # 验证目录存在
            if not scripts_dir.exists():
                raise FileNotFoundError(f"Scripts 目录不存在: {scripts_dir_str}")
            
            # 验证文件存在
            test_sync_file = scripts_dir / 'test_copy_sync.py'
            if not test_sync_file.exists():
                raise FileNotFoundError(f"test_copy_sync.py 不存在: {test_sync_file}")
            
            from test_copy_sync import CopySyncTester
            logger.info("成功导入 CopySyncTester")
            
            start_time = time.time()
            total_days = (end_date - start_date).days + 1
            success_count = 0
            failed_count = 0
            skipped_count = 0
            total_records = 0
            
            # 遍历日期范围
            current_date = start_date
            processed = 0
            
            while current_date <= end_date:
                tester = None
                try:
                    date_str = current_date.isoformat()
                    processed += 1
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(
                            processed=processed,
                            total=total_days,
                            current_date=date_str,
                            success=success_count,
                            failed=failed_count,
                            skipped=skipped_count
                        )
                    
                    logger.info(f"[{processed}/{total_days}] 开始检查: {date_str}")
                    
                    # 优化的同步逻辑：先检查同步记录表
                    from app.services.sync_status_service import SyncStatusService
                    from app.core.database import DatabaseConnection
                    
                    # 1. 先检查同步记录
                    sync_status = SyncStatusService.get_status(current_date)
                    need_sync = True  # 默认需要同步
                    
                    if sync_status:
                        status_value = sync_status.get('status')
                        
                        # 只有 success 和 skipped 状态才跳过同步
                        if status_value == 'success':
                            # 验证数据是否真的存在
                            try:
                                with DatabaseConnection() as cursor:
                                    cursor.execute(
                                        "SELECT COUNT(*) as count FROM daily_stock_data WHERE trade_date = %s",
                                        (current_date,)
                                    )
                                    result = cursor.fetchone()
                                    data_count = result['count'] if result else 0
                                    
                                    if data_count > 0:
                                        # 数据存在且状态为成功，跳过同步
                                        need_sync = False
                                        success_count += 1
                                        total_records += data_count
                                        logger.info(f"{date_str} ✅ 已同步成功（{data_count}条），跳过")
                                    else:
                                        # 状态是成功但没有数据，需要重新同步
                                        logger.warning(f"{date_str} ⚠️  状态为成功但无数据，需要重新同步")
                                        need_sync = True
                            except Exception as e:
                                logger.error(f"检查数据失败: {e}")
                                need_sync = True
                                
                        elif status_value == 'skipped':
                            # 跳过状态（非交易日），不需要同步
                            need_sync = False
                            skipped_count += 1
                            logger.info(f"{date_str} ⏭️  已跳过（非交易日）")
                            
                        elif status_value in ['syncing', 'failed', 'pending']:
                            # 同步中、失败、待同步状态，需要重新同步
                            logger.info(f"{date_str} 🔄 状态为 {status_value}，需要重新同步")
                            need_sync = True
                    else:
                        # 没有同步记录，需要同步
                        logger.info(f"{date_str} 📝 无同步记录，需要同步")
                        need_sync = True
                    
                    # 2. 根据检查结果决定是否同步
                    if not need_sync:
                        # 跳过同步
                        pass
                    else:
                        # 创建同步器并执行同步
                        tester = CopySyncTester()
                        tester.test_sync(None, date_str)
                        tester.close()
                        tester = None
                        
                        # 等待数据库写入
                        time.sleep(1)
                        
                        # 检查结果
                        status = SyncStatusService.get_status(current_date)
                        if status:
                            if status.get('status') == 'success':
                                success_count += 1
                                total_records += status.get('total_records', 0)
                                logger.info(f"{date_str} 同步成功")
                            elif status.get('status') == 'skipped':
                                skipped_count += 1
                                logger.info(f"{date_str} 跳过（非交易日）")
                            else:
                                failed_count += 1
                                logger.error(f"{date_str} 同步失败")
                        else:
                            skipped_count += 1
                            logger.info(f"{date_str} 跳过（无状态记录）")
                
                except Exception as e:
                    logger.error(f"同步 {current_date} 失败: {e}", exc_info=True)
                    failed_count += 1
                finally:
                    if tester:
                        try:
                            tester.close()
                        except:
                            pass
                
                current_date += timedelta(days=1)
            
            # 计算总耗时
            total_time = time.time() - start_time
            minutes = int(total_time // 60)
            seconds = int(total_time % 60)
            
            result = {
                'status': 'success',
                'total_days': total_days,
                'success_count': success_count,
                'failed_count': failed_count,
                'skipped_count': skipped_count,
                'total_records': total_records,
                'duration_seconds': int(total_time),
                'duration_text': f'{minutes}分{seconds}秒',
                'message': f'同步完成: 成功{success_count}, 失败{failed_count}, 跳过{skipped_count}'
            }
            
            logger.info(f"同步任务完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"同步任务失败: {e}", exc_info=True)
            return {
                'status': 'failed',
                'message': str(e)
            }
        finally:
            SyncManager.release_sync_lock()


# 全局实例
_sync_manager = SyncManager()

def get_sync_manager() -> SyncManager:
    """获取同步管理器实例"""
    return _sync_manager
