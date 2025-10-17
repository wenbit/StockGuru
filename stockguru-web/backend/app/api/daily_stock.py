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
    start_date: Optional[date] = Field(None, description="开始日期（不填则查询最新交易日）")
    end_date: Optional[date] = Field(None, description="结束日期（不填则查询最新交易日）")
    stock_code: Optional[str] = Field(None, description="股票代码（可选）")
    change_pct_min: Optional[float] = Field(None, description="最小涨跌幅（%）")
    change_pct_max: Optional[float] = Field(None, description="最大涨跌幅（%）")
    volume_min: Optional[int] = Field(None, description="最小成交量")
    sort_by: str = Field("change_pct", description="排序字段")
    sort_order: str = Field("desc", description="排序方向: asc/desc")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=1000, description="每页数量（默认20）")


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
    
    - **start_date**: 开始日期（不填则查询最新交易日）
    - **end_date**: 结束日期（不填则查询最新交易日）
    - **stock_code**: 股票代码（可选）
    - **change_pct_min**: 最小涨跌幅（%），可为负数
    - **change_pct_max**: 最大涨跌幅（%），可为负数
    - **volume_min**: 最小成交量（可选）
    - **sort_by**: 排序字段（默认：change_pct）
    - **sort_order**: 排序方向（asc/desc，默认：desc）
    - **page**: 页码（从1开始）
    - **page_size**: 每页数量（默认20，最大1000）
    """
    try:
        from app.core.database import DatabaseConnection
        
        # 如果没有指定日期，查询最新交易日
        if not request.start_date or not request.end_date:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    SELECT trade_date 
                    FROM daily_stock_data 
                    ORDER BY trade_date DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                
                if not result:
                    return QueryResponse(
                        total=0,
                        page=request.page,
                        page_size=request.page_size,
                        total_pages=0,
                        data=[]
                    )
                
                latest_date = result['trade_date']
                if not request.start_date:
                    request.start_date = latest_date
                if not request.end_date:
                    request.end_date = latest_date
        
        # 构建SQL查询
        with DatabaseConnection() as cursor:
            # 构建WHERE条件
            where_clauses = []
            params = []
            
            # 日期范围
            where_clauses.append("trade_date >= %s")
            params.append(request.start_date)
            where_clauses.append("trade_date <= %s")
            params.append(request.end_date)
            
            # 过滤掉涨跌幅为 null 的记录
            where_clauses.append("change_pct IS NOT NULL")
            
            # 股票代码筛选
            if request.stock_code:
                where_clauses.append("stock_code = %s")
                params.append(request.stock_code)
            
            # 涨跌幅筛选
            if request.change_pct_min is not None:
                where_clauses.append("change_pct >= %s")
                params.append(request.change_pct_min)
            
            if request.change_pct_max is not None:
                where_clauses.append("change_pct <= %s")
                params.append(request.change_pct_max)
            
            # 成交量筛选
            if request.volume_min is not None:
                where_clauses.append("volume >= %s")
                params.append(request.volume_min)
            
            where_sql = " AND ".join(where_clauses)
            
            # 计算总数
            count_sql = f"SELECT COUNT(*) as total FROM daily_stock_data WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 查询数据
            sort_order = "ASC" if request.sort_order.lower() == 'asc' else "DESC"
            offset = (request.page - 1) * request.page_size
            
            data_sql = f"""
                SELECT * FROM daily_stock_data 
                WHERE {where_sql}
                ORDER BY {request.sort_by} {sort_order}
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params + [request.page_size, offset])
            rows = cursor.fetchall()
            
            # 计算总页数
            total_pages = (total + request.page_size - 1) // request.page_size if total > 0 else 0
            
            # 转换为DailyStockData对象
            data = [DailyStockData(**row) for row in rows]
            
            return QueryResponse(
                total=total,
                page=request.page,
                page_size=request.page_size,
                total_pages=total_pages,
                data=data
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
        from app.core.database import DatabaseConnection
        
        with DatabaseConnection() as cursor:
            where_clauses = ["stock_code = %s"]
            params = [stock_code]
            
            if start_date:
                where_clauses.append("trade_date >= %s")
                params.append(start_date)
            
            if end_date:
                where_clauses.append("trade_date <= %s")
                params.append(end_date)
            
            where_sql = " AND ".join(where_clauses)
            
            sql = f"""
                SELECT * FROM daily_stock_data
                WHERE {where_sql}
                ORDER BY trade_date DESC
                LIMIT %s
            """
            cursor.execute(sql, params + [limit])
            rows = cursor.fetchall()
            
            return [DailyStockData(**row) for row in rows]
        
    except Exception as e:
        logger.error(f"查询股票历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(request: SyncRequest):
    """
    手动触发数据同步（使用 Neon 高性能服务）
    
    - **sync_date**: 同步指定日期的数据（可选，不填则同步今天）
    - **days**: 同步最近N天的数据（用于初始化，与sync_date互斥）
    """
    try:
        from app.services.daily_data_sync_service_neon import DailyDataSyncServiceNeon
        sync_service = DailyDataSyncServiceNeon()
        
        # 同步单日数据（Neon 服务暂不支持批量同步）
        sync_date = request.sync_date or date.today()
        logger.info(f"开始同步 {sync_date} 的数据...")
        result = sync_service.sync_daily_data(sync_date)
        
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
        from app.core.database import DatabaseConnection
        
        with DatabaseConnection() as cursor:
            # 注意: sync_logs表可能不存在，这里返回基本信息
            cursor.execute("""
                SELECT trade_date, COUNT(*) as count
                FROM daily_stock_data
                GROUP BY trade_date
                ORDER BY trade_date DESC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            
            return {
                "status": "success",
                "data": rows
            }
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-db")
async def test_database():
    """测试数据库连接"""
    try:
        from app.core.database import DatabaseConnection
        import os
        
        db_url = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
        
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT current_database(), current_user, version()")
            db_info = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) as total FROM daily_stock_data")
            total = cursor.fetchone()['total']
            
            return {
                "database_url": db_url[:50] + "..." if db_url else None,
                "database": db_info,
                "total_records": total
            }
    except Exception as e:
        return {"error": str(e)}


@router.get("/stats")
async def get_data_stats():
    """
    获取数据统计信息
    """
    try:
        from app.core.database import DatabaseConnection
        
        with DatabaseConnection() as cursor:
            # 调试：检查连接信息
            cursor.execute("SELECT current_database(), current_user")
            db_info = cursor.fetchone()
            logger.info(f"数据库: {db_info}")
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) as total FROM daily_stock_data")
            total_records = cursor.fetchone()['total']
            logger.info(f"查询到总记录数: {total_records}")
            
            # 最新交易日
            cursor.execute("""
                SELECT trade_date FROM daily_stock_data 
                ORDER BY trade_date DESC LIMIT 1
            """)
            result = cursor.fetchone()
            latest_date = result['trade_date'] if result else None
            
            # 最早交易日
            cursor.execute("""
                SELECT trade_date FROM daily_stock_data 
                ORDER BY trade_date ASC LIMIT 1
            """)
            result = cursor.fetchone()
            earliest_date = result['trade_date'] if result else None
            
            # 股票数量
            cursor.execute("SELECT COUNT(DISTINCT stock_code) as count FROM daily_stock_data")
            unique_stocks = cursor.fetchone()['count']
            
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
