"""
每日股票数据查询 API
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== 数据模型 ==========

class DailyStockData(BaseModel):
    """每日股票数据"""
    id: int
    stock_code: str
    stock_name: str
    trade_date: date
    open_price: Optional[float]
    close_price: float
    high_price: Optional[float]
    low_price: Optional[float]
    volume: Optional[int]
    amount: Optional[float]
    change_pct: Optional[float]
    change_amount: Optional[float]
    turnover_rate: Optional[float]
    amplitude: Optional[float]


class QueryRequest(BaseModel):
    """查询请求"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    change_pct_min: Optional[float] = Field(None, description="最小涨跌幅（%）")
    change_pct_max: Optional[float] = Field(None, description="最大涨跌幅（%）")
    sort_by: str = Field("change_pct", description="排序字段")
    sort_order: str = Field("desc", description="排序方向: asc/desc")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=1000, description="每页数量")


class QueryResponse(BaseModel):
    """查询响应"""
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[DailyStockData]


class SyncRequest(BaseModel):
    """同步请求"""
    sync_date: Optional[date] = Field(None, description="同步日期，不填则同步今天")
    days: Optional[int] = Field(None, ge=1, le=365, description="同步最近N天，用于初始化")


class SyncResponse(BaseModel):
    """同步响应"""
    status: str
    message: str
    data: dict


# ========== API 端点 ==========

@router.post("/query", response_model=QueryResponse)
async def query_daily_stock_data(request: QueryRequest):
    """
    查询每日股票数据
    
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **change_pct_min**: 最小涨跌幅（%），可为负数
    - **change_pct_max**: 最大涨跌幅（%），可为负数
    - **sort_by**: 排序字段（默认：change_pct）
    - **sort_order**: 排序方向（asc/desc，默认：desc）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（默认50，最大1000）
    """
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        # 构建查询
        query = supabase.table('daily_stock_data').select('*', count='exact')
        
        # 日期范围
        query = query.gte('trade_date', request.start_date.isoformat())
        query = query.lte('trade_date', request.end_date.isoformat())
        
        # 涨跌幅筛选
        if request.change_pct_min is not None:
            query = query.gte('change_pct', request.change_pct_min)
        
        if request.change_pct_max is not None:
            query = query.lte('change_pct', request.change_pct_max)
        
        # 排序
        ascending = request.sort_order.lower() == 'asc'
        query = query.order(request.sort_by, desc=not ascending)
        
        # 分页
        offset = (request.page - 1) * request.page_size
        query = query.range(offset, offset + request.page_size - 1)
        
        # 执行查询
        response = query.execute()
        
        # 计算总页数
        total = response.count if hasattr(response, 'count') else len(response.data)
        total_pages = (total + request.page_size - 1) // request.page_size
        
        return QueryResponse(
            total=total,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            data=response.data
        )
        
    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}", response_model=List[DailyStockData])
async def get_stock_history(
    stock_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(60, ge=1, le=1000, description="返回数量")
):
    """
    获取指定股票的历史数据
    
    - **stock_code**: 股票代码
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    - **limit**: 返回数量（默认60天）
    """
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        query = supabase.table('daily_stock_data')\
            .select('*')\
            .eq('stock_code', stock_code)\
            .order('trade_date', desc=True)\
            .limit(limit)
        
        if start_date:
            query = query.gte('trade_date', start_date.isoformat())
        
        if end_date:
            query = query.lte('trade_date', end_date.isoformat())
        
        response = query.execute()
        
        return response.data
        
    except Exception as e:
        logger.error(f"查询股票历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(request: SyncRequest):
    """
    手动触发数据同步
    
    - **sync_date**: 同步指定日期的数据（可选，不填则同步今天）
    - **days**: 同步最近N天的数据（用于初始化，与sync_date互斥）
    """
    try:
        from app.services.daily_data_sync_service_v2 import get_sync_service_v2
        sync_service = get_sync_service_v2()
        
        if request.days:
            # 同步历史数据
            logger.info(f"开始同步最近 {request.days} 天的数据...")
            result = await sync_service.sync_historical_data(request.days)
            
            return SyncResponse(
                status="success",
                message=f"历史数据同步完成，成功 {result['success_days']}/{result['total_days']} 天",
                data=result
            )
        else:
            # 同步单日数据
            sync_date = request.sync_date or date.today()
            logger.info(f"开始同步 {sync_date} 的数据...")
            result = await sync_service.sync_date_data(sync_date)
            
            return SyncResponse(
                status=result['status'],
                message=f"数据同步完成: {result.get('message', '')}",
                data=result
            )
        
    except Exception as e:
        logger.error(f"同步失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    limit: int = Query(10, ge=1, le=100, description="返回数量")
):
    """
    获取同步状态
    
    - **limit**: 返回最近N条同步记录
    """
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        response = supabase.table('sync_logs')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "status": "success",
            "data": response.data
        }
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_data_stats():
    """
    获取数据统计信息
    """
    try:
        from app.core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        # 总记录数
        total_response = supabase.table('daily_stock_data')\
            .select('*', count='exact')\
            .limit(1)\
            .execute()
        total_records = total_response.count if hasattr(total_response, 'count') else 0
        
        # 最新交易日
        latest_response = supabase.table('daily_stock_data')\
            .select('trade_date')\
            .order('trade_date', desc=True)\
            .limit(1)\
            .execute()
        latest_date = latest_response.data[0]['trade_date'] if latest_response.data else None
        
        # 最早交易日
        earliest_response = supabase.table('daily_stock_data')\
            .select('trade_date')\
            .order('trade_date', desc=False)\
            .limit(1)\
            .execute()
        earliest_date = earliest_response.data[0]['trade_date'] if earliest_response.data else None
        
        # 股票数量
        stocks_response = supabase.table('daily_stock_data')\
            .select('stock_code')\
            .execute()
        unique_stocks = len(set(row['stock_code'] for row in stocks_response.data))
        
        return {
            "status": "success",
            "data": {
                "total_records": total_records,
                "unique_stocks": unique_stocks,
                "latest_date": latest_date,
                "earliest_date": earliest_date
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
