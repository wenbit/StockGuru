"""
同步状态管理API
提供同步状态查询、手动触发同步等功能
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import date, timedelta, datetime
from typing import Optional, Dict
from pydantic import BaseModel
import logging
import threading

from app.services.sync_status_service import SyncStatusService
from app.services.daily_sync_with_status import get_daily_sync_service
from app.services.sync_manager import get_sync_manager

router = APIRouter(prefix="/api/v1/sync-status", tags=["同步状态"])
logger = logging.getLogger(__name__)

# 全局进度追踪
_batch_sync_progress: Dict[str, Dict] = {}


@router.get("/today")
async def get_today_status():
    """获取今日同步状态"""
    try:
        today = date.today()
        status = SyncStatusService.get_status(today)
        
        if not status:
            return {
                "status": "not_found",
                "date": today.isoformat(),
                "message": "未找到今日同步记录"
            }
        
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取今日状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/date/{sync_date}")
async def get_date_status(sync_date: str):
    """获取指定日期的同步状态"""
    try:
        target_date = date.fromisoformat(sync_date)
        status = SyncStatusService.get_status(target_date)
        
        if not status:
            return {
                "status": "not_found",
                "date": sync_date,
                "message": "未找到同步记录"
            }
        
        return {
            "status": "success",
            "data": status
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"获取日期状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_status(days: int = 30):
    """获取最近N天的同步状态"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="天数范围应在 1-365 之间")
        
        status_list = SyncStatusService.get_recent_status(days)
        
        return {
            "status": "success",
            "total": len(status_list),
            "data": status_list
        }
    except Exception as e:
        logger.error(f"获取最近状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_dates(days_back: int = 30):
    """获取需要同步的日期列表"""
    try:
        if days_back < 1 or days_back > 365:
            raise HTTPException(status_code=400, detail="天数范围应在 1-365 之间")
        
        pending_dates = SyncStatusService.get_pending_dates(days_back)
        
        return {
            "status": "success",
            "total": len(pending_dates),
            "dates": [d.isoformat() for d in pending_dates]
        }
    except Exception as e:
        logger.error(f"获取待同步日期失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_status_summary(days: int = 30):
    """获取同步状态摘要"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="天数范围应在 1-365 之间")
        
        sync_service = get_daily_sync_service()
        summary = sync_service.get_sync_status_summary(days)
        
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        logger.error(f"获取状态摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/today")
async def trigger_sync_today():
    """手动触发今日数据同步"""
    try:
        sync_service = get_daily_sync_service()
        result = await sync_service.sync_today()
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"触发今日同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/date/{sync_date}")
async def trigger_sync_date(sync_date: str):
    """手动触发指定日期的数据同步"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_daily_sync_service()
        result = await sync_service.sync_date_with_status(target_date)
        
        return {
            "status": "success",
            "data": result
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"触发日期同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/pending")
async def trigger_sync_pending(days_back: int = 30):
    """同步所有待同步的日期"""
    try:
        if days_back < 1 or days_back > 365:
            raise HTTPException(status_code=400, detail="天数范围应在 1-365 之间")
        
        sync_service = get_daily_sync_service()
        result = await sync_service.sync_pending_dates(days_back)
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"触发待同步日期同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check/{sync_date}")
async def check_need_sync(sync_date: str):
    """检查指定日期是否需要同步"""
    try:
        target_date = date.fromisoformat(sync_date)
        need_sync, reason = SyncStatusService.check_need_sync(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "need_sync": need_sync,
            "reason": reason
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"检查同步需求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_sync_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选")
):
    """分页查询同步记录"""
    try:
        records, total, stats = SyncStatusService.get_sync_list(
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "status": "success",
            "data": {
                "records": records,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "stats": stats
            }
        }
    except Exception as e:
        logger.error(f"查询同步列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class BatchSyncRequest(BaseModel):
    start_date: str
    end_date: str


def batch_sync_background(start_date_str: str, end_date_str: str, task_id: str):
    """后台批量同步任务（使用统一的同步管理器）"""
    import time
    
    start_time = time.time()
    sync_manager = get_sync_manager()
    
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        
        # 计算总天数
        total_days = (end_date - start_date).days + 1
        
        # 初始化进度
        _batch_sync_progress[task_id] = {
            'status': 'running',
            'total': total_days,
            'current': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'current_date': '',
            'message': '正在初始化...',
            'start_time': start_date_str,  # 同步开始日期
            'end_time': end_date_str,      # 同步结束日期
            'task_start_time': datetime.now().isoformat(),  # 任务开始时间
            'estimated_completion': None,
            'errors': []  # 记录错误详情
        }
        
        logger.info(f"批量同步任务开始: {start_date_str} 至 {end_date_str}, 共 {total_days} 天")
        
        # 不再创建批量同步的总记录，每一天会在实际同步时创建自己的记录
        # 这样更合理，避免在同步记录表中出现中间日期的混淆记录
        
        # 定义进度回调函数
        def progress_callback(processed, total, current_date, success, failed, skipped):
            # 计算预计完成时间
            elapsed = time.time() - start_time
            if processed > 0:
                avg_time_per_day = elapsed / processed
                remaining_days = total - processed
                estimated_seconds = remaining_days * avg_time_per_day
                estimated_completion = datetime.now() + timedelta(seconds=estimated_seconds)
            else:
                estimated_completion = None
            
            # 更新进度
            progress_percent = round((processed / total) * 100, 1) if total > 0 else 0
            _batch_sync_progress[task_id].update({
                'current': processed,
                'success': success,
                'failed': failed,
                'skipped': skipped,
                'current_date': current_date,
                'message': f'正在同步 {current_date}... ({progress_percent}%)',
                'progress_percent': progress_percent,
                'estimated_completion': estimated_completion.isoformat() if estimated_completion else None
            })
            
            # 不再更新批量同步记录，因为我们不再创建它
        
        # 使用统一的同步管理器执行同步
        result = sync_manager.sync_date_range(
            start_date=start_date,
            end_date=end_date,
            task_type='web_batch',
            progress_callback=progress_callback
        )
        
        if result['status'] == 'rejected':
            # 任务被拒绝（已有任务在运行）
            _batch_sync_progress[task_id].update({
                'status': 'failed',
                'message': result['message']
            })
            logger.warning(f"批量同步任务被拒绝: {result['message']}")
            return
        
        # 获取结果
        success_count = result.get('success_count', 0)
        failed_count = result.get('failed_count', 0)
        skipped_count = result.get('skipped_count', 0)
        total_records = result.get('total_records', 0)
        
        # 以下代码保持不变，用于更新进度和数据库记录
        processed = total_days
        current_date = end_date
            # 同步已由 sync_manager 完成，这里只需要处理结果
        
        # 计算总耗时
        total_time = time.time() - start_time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        
        # 标记完成
        completion_msg = f'批量同步完成: 成功{success_count}, 失败{failed_count}, 跳过{skipped_count}, 耗时{minutes}分{seconds}秒'
        _batch_sync_progress[task_id].update({
            'status': 'completed',
            'message': completion_msg,
            'end_time': datetime.now().isoformat(),
            'duration_seconds': int(total_time),
            'progress_percent': 100
        })
        
        logger.info(f"批量同步完成: 成功{success_count}, 失败{failed_count}, 跳过{skipped_count}, 耗时{minutes}分{seconds}秒")
        
        # 不再更新批量同步记录，每一天都有自己的独立记录
    except Exception as e:
        logger.error(f"批量同步任务失败: {e}", exc_info=True)
        if task_id in _batch_sync_progress:
            _batch_sync_progress[task_id].update({
                'status': 'failed',
                'message': f'同步失败: {str(e)}'
            })
        
        # 不再更新批量同步记录
    finally:
        # 同步锁由 sync_manager 管理，这里不需要手动释放
        logger.info(f"同步任务结束，任务ID: {task_id}")
        
        # 30分钟后清理进度数据（避免内存泄漏）
        import threading
        def cleanup_progress():
            time.sleep(1800)  # 30分钟
            if task_id in _batch_sync_progress:
                del _batch_sync_progress[task_id]
                logger.info(f"已清理任务进度数据: {task_id}")
        
        threading.Thread(target=cleanup_progress, daemon=True).start()


@router.post("/sync/batch")
async def trigger_batch_sync(request: BatchSyncRequest, background_tasks: BackgroundTasks):
    """批量同步指定日期范围的数据（异步执行）"""
    try:
        # 检查是否有同步任务正在运行
        sync_manager = get_sync_manager()
        if sync_manager.is_syncing():
            current_task = sync_manager.get_current_task()
            return {
                "status": "error",
                "message": "已有同步任务正在运行，请等待当前任务完成后再试",
                "current_task": current_task
            }
        
        # 验证日期格式
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
        
        if start_date > end_date:
            return {
                "status": "error",
                "message": "开始日期不能晚于结束日期"
            }
        
        # 计算天数
        days = (end_date - start_date).days + 1
        
        if days > 90:
            return {
                "status": "error",
                "message": "日期范围不能超过90天"
            }
        
        # 生成任务ID
        task_id = f"{request.start_date}_{request.end_date}_{int(datetime.now().timestamp())}"
        
        # 添加后台任务
        background_tasks.add_task(batch_sync_background, request.start_date, request.end_date, task_id)
        
        return {
            "status": "success",
            "data": {
                "task_id": task_id,
                "total_days": days,
                "message": f"批量同步任务已启动，将同步 {days} 天的数据"
            }
        }
    except ValueError:
        return {
            "status": "error",
            "message": "日期格式错误，应为 YYYY-MM-DD"
        }
    except Exception as e:
        logger.error(f"启动批量同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/batch/progress/{task_id}")
async def get_batch_sync_progress(task_id: str):
    """查询批量同步进度"""
    if task_id not in _batch_sync_progress:
        return {
            "status": "error",
            "message": "任务不存在或已过期"
        }
    
    progress = _batch_sync_progress[task_id]
    return {
        "status": "success",
        "data": progress
    }


@router.get("/sync/batch/active")
async def get_active_batch_sync():
    """获取当前活跃的批量同步任务"""
    # 1. 先从内存中查找
    active_tasks = []
    for task_id, progress in _batch_sync_progress.items():
        if progress.get('status') == 'running':
            active_tasks.append({
                'task_id': task_id,
                'progress': progress
            })
    
    if active_tasks:
        return {
            "status": "success",
            "data": active_tasks[0]  # 返回第一个活跃任务
        }
    
    # 2. 如果内存中没有，从数据库查询正在同步的记录
    try:
        from app.core.database import DatabaseConnection
        
        with DatabaseConnection() as cursor:
            cursor.execute("""
                SELECT sync_date, status, total_records, success_count, failed_count, 
                       start_time, remarks
                FROM daily_sync_status 
                WHERE status = 'syncing'
                ORDER BY sync_date
                LIMIT 1
            """)
            syncing_record = cursor.fetchone()
            
            if syncing_record:
                # 构造一个虚拟的批量任务进度
                sync_date = syncing_record['sync_date']
                remarks = syncing_record.get('remarks', '')
                
                # 从备注中提取进度信息（格式：同步中: 1500/5377）
                import re
                match = re.search(r'(\d+)/(\d+)', remarks)
                current = int(match.group(1)) if match else syncing_record['success_count']
                total = int(match.group(2)) if match else syncing_record['total_records']
                
                progress_percent = round((current / total * 100), 1) if total > 0 else 0
                
                # 生成一个task_id
                task_id = f"recovered_{sync_date}"
                
                return {
                    "status": "success",
                    "data": {
                        'task_id': task_id,
                        'progress': {
                            'status': 'running',
                            'total': 1,  # 单日同步
                            'current': 1,
                            'success': 0,
                            'failed': 0,
                            'skipped': 0,
                            'current_date': str(sync_date),
                            'message': f'正在同步 {sync_date}... ({progress_percent}%)',
                            'start_time': str(sync_date),
                            'end_time': str(sync_date),
                            'task_start_time': syncing_record['start_time'].isoformat() if syncing_record['start_time'] else None,
                            'estimated_completion': None,
                            'errors': [],
                            'progress_percent': progress_percent
                        }
                    }
                }
    except Exception as e:
        logger.error(f"从数据库查询同步状态失败: {e}")
    
    # 3. 都没有，返回null
    return {
        "status": "success",
        "data": None
    }
