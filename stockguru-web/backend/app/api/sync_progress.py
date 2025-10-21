"""
同步进度管理API
提供进度查询、断点续传、失败重试等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import date
from typing import Optional
import logging

from app.services.resumable_sync_service import get_resumable_sync_service
from app.services.sync_status_service import SyncStatusService

router = APIRouter(prefix="/api/v1/sync-progress", tags=["同步进度"])
logger = logging.getLogger(__name__)


@router.get("/date/{sync_date}")
async def get_progress(sync_date: str):
    """获取指定日期的同步进度"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        progress = sync_service.get_progress(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "data": progress
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"获取进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending/{sync_date}")
async def get_pending_stocks(sync_date: str, limit: Optional[int] = None):
    """获取待同步的股票列表"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        stocks = sync_service.get_pending_stocks(target_date, limit)
        
        return {
            "status": "success",
            "date": sync_date,
            "total": len(stocks),
            "data": stocks
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"获取待同步股票失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed/{sync_date}")
async def get_failed_stocks(sync_date: str):
    """获取失败的股票列表"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        stocks = sync_service.get_failed_stocks(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "total": len(stocks),
            "data": stocks
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"获取失败股票失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/init/{sync_date}")
async def init_progress(sync_date: str):
    """初始化同步进度"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        count = sync_service.init_progress(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "message": f"已初始化 {count} 只股票的进度记录"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"初始化进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-failed/{sync_date}")
async def reset_failed(sync_date: str):
    """将失败的股票重置为待同步"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        count = sync_service.reset_failed_to_pending(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "message": f"已重置 {count} 只失败股票为待同步状态"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"重置失败股票失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{sync_date}")
async def clear_progress(sync_date: str):
    """清除进度记录"""
    try:
        target_date = date.fromisoformat(sync_date)
        sync_service = get_resumable_sync_service()
        sync_service.clear_progress(target_date)
        
        return {
            "status": "success",
            "date": sync_date,
            "message": "进度记录已清除"
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"清除进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{sync_date}")
async def sync_with_resume(
    sync_date: str,
    background_tasks: BackgroundTasks,
    batch_size: int = 50,
    max_retries: int = 3
):
    """
    执行断点续传同步（后台任务）
    
    Args:
        sync_date: 同步日期
        batch_size: 每批处理数量
        max_retries: 最大重试次数
    """
    try:
        target_date = date.fromisoformat(sync_date)
        
        # 标记为同步中
        SyncStatusService.mark_as_syncing(target_date)
        
        # 在后台执行同步
        def sync_task():
            sync_service = get_resumable_sync_service()
            result = sync_service.sync_with_resume(target_date, batch_size, max_retries)
            
            # 更新同步状态
            if result['status'] == 'success':
                SyncStatusService.mark_as_success(
                    sync_date=target_date,
                    total_records=result['success'],
                    success_count=result['success'],
                    remarks=result.get('message', '')
                )
            elif result['status'] == 'partial':
                SyncStatusService.mark_as_failed(
                    sync_date=target_date,
                    error_message=f"部分失败: {result['failed']} 只",
                    total_records=result['total'],
                    success_count=result['success'],
                    failed_count=result['failed']
                )
            else:
                SyncStatusService.mark_as_failed(
                    sync_date=target_date,
                    error_message=result.get('error', '同步失败')
                )
        
        background_tasks.add_task(sync_task)
        
        return {
            "status": "success",
            "date": sync_date,
            "message": "同步任务已启动，将在后台执行"
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"启动同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-now/{sync_date}")
async def sync_now(
    sync_date: str,
    batch_size: int = 50,
    max_retries: int = 3
):
    """
    立即执行断点续传同步（同步执行，会阻塞）
    
    Args:
        sync_date: 同步日期
        batch_size: 每批处理数量
        max_retries: 最大重试次数
    """
    try:
        target_date = date.fromisoformat(sync_date)
        
        # 标记为同步中
        SyncStatusService.mark_as_syncing(target_date)
        
        # 执行同步
        sync_service = get_resumable_sync_service()
        result = sync_service.sync_with_resume(target_date, batch_size, max_retries)
        
        # 更新同步状态
        if result['status'] == 'success':
            SyncStatusService.mark_as_success(
                sync_date=target_date,
                total_records=result['success'],
                success_count=result['success'],
                remarks=result.get('message', '')
            )
        elif result['status'] == 'partial':
            SyncStatusService.mark_as_failed(
                sync_date=target_date,
                error_message=f"部分失败: {result['failed']} 只",
                total_records=result['total'],
                success_count=result['success'],
                failed_count=result['failed']
            )
        else:
            SyncStatusService.mark_as_failed(
                sync_date=target_date,
                error_message=result.get('error', '同步失败')
            )
        
        return {
            "status": "success",
            "data": result
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        logger.error(f"同步失败: {e}", exc_info=True)
        
        # 标记为失败
        try:
            target_date = date.fromisoformat(sync_date)
            SyncStatusService.mark_as_failed(target_date, str(e))
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))
