"""
筛选 API 路由
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional
import logging
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class ScreeningRequest(BaseModel):
    """筛选请求"""
    date: str
    volume_top_n: Optional[int] = 100
    hot_top_n: Optional[int] = 100


class ScreeningResponse(BaseModel):
    """筛选响应"""
    task_id: str
    status: str
    message: str


@router.post("/screening", response_model=ScreeningResponse)
async def create_screening(request: ScreeningRequest, background_tasks: BackgroundTasks):
    """
    创建筛选任务
    
    - **date**: 筛选日期 (格式: YYYY-MM-DD)
    - **volume_top_n**: 成交量排名前N (默认: 100)
    - **hot_top_n**: 热度排名前N (默认: 100)
    """
    try:
        logger.info(f"创建筛选任务: date={request.date}")
        
        # 延迟导入服务
        from app.services.screening_service import ScreeningService
        screening_service = ScreeningService()
        
        # 创建任务
        result = await screening_service.create_screening_task(
            date=request.date,
            volume_top_n=request.volume_top_n,
            hot_top_n=request.hot_top_n
        )
        
        # 在后台执行筛选
        import asyncio
        
        def run_screening():
            """包装异步函数为同步函数"""
            asyncio.run(screening_service._execute_screening(
                result["task_id"],
                request.date,
                request.volume_top_n,
                request.hot_top_n
            ))
        
        background_tasks.add_task(run_screening)
        
        return result
        
    except Exception as e:
        logger.error(f"创建筛选任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screening/{task_id}")
async def get_screening_result(task_id: str):
    """
    获取筛选结果
    
    - **task_id**: 任务ID
    """
    try:
        logger.info(f"获取筛选结果: task_id={task_id}")
        
        from app.services.screening_service import ScreeningService
        screening_service = ScreeningService()
        
        result = await screening_service.get_task_result(task_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取筛选结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screening")
async def list_screenings(limit: int = 10):
    """
    获取筛选任务列表
    
    - **limit**: 返回数量限制 (默认: 10)
    """
    try:
        logger.info(f"获取筛选任务列表: limit={limit}")
        
        from app.services.screening_service import ScreeningService
        screening_service = ScreeningService()
        
        tasks = await screening_service.list_tasks(limit=limit)
        
        return tasks
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/screening/{task_id}/export", response_class=HTMLResponse)
async def export_report(task_id: str):
    """
    导出筛选报告为 HTML
    
    Args:
        task_id: 任务ID
        
    Returns:
        HTML 格式的报告
    """
    try:
        logger.info(f"导出报告: {task_id}")
        
        # 获取任务结果
        from app.services.screening_service import ScreeningService
        screening_service = ScreeningService()
        result = await screening_service.get_task_result(task_id)
        
        if result.status != 'completed':
            raise HTTPException(status_code=400, detail="任务未完成，无法导出报告")
        
        if not result.results or len(result.results) == 0:
            raise HTTPException(status_code=404, detail="没有筛选结果")
        
        # 准备模板数据
        template_data = {
            'task_id': task_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'result_count': len(result.results),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'results': result.results
        }
        
        # 渲染模板
        template_dir = Path(__file__).parent.parent / 'templates'
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template('report_template.html')
        html_content = template.render(**template_data)
        
        logger.info(f"报告导出成功: {task_id}")
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出报告失败: {str(e)}")
