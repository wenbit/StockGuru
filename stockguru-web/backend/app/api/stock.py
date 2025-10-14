"""
股票数据 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import pandas as pd
import numpy as np

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stock/{code}/kline")
async def get_stock_kline(code: str, days: int = 60):
    """
    获取股票K线数据
    
    - **code**: 股票代码
    - **days**: 获取天数（默认60天）
    """
    try:
        logger.info(f"获取股票K线数据: code={code}, days={days}")
        
        from app.services.modules.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        # 获取K线数据
        kline_df = fetcher.get_stock_daily_data(code, days=days)
        
        if kline_df.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的K线数据")
        
        # 转换为字典列表
        kline_data = kline_df.to_dict('records')
        
        # 计算均线
        from app.services.modules.momentum_calculator import MomentumCalculator
        from app.core.config import settings
        
        momentum_calc = MomentumCalculator(config=settings)
        ma5 = momentum_calc.calculate_ma(kline_df['close'], period=5)
        ma10 = momentum_calc.calculate_ma(kline_df['close'], period=10)
        ma20 = momentum_calc.calculate_ma(kline_df['close'], period=20)
        
        # 添加均线到数据中
        for i, record in enumerate(kline_data):
            record['ma5'] = float(ma5.iloc[i]) if i < len(ma5) and not pd.isna(ma5.iloc[i]) else None
            record['ma10'] = float(ma10.iloc[i]) if i < len(ma10) and not pd.isna(ma10.iloc[i]) else None
            record['ma20'] = float(ma20.iloc[i]) if i < len(ma20) and not pd.isna(ma20.iloc[i]) else None
        
        return {
            "code": code,
            "data": kline_data,
            "count": len(kline_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"获取K线数据失败: {str(e)}\n{error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/info")
async def get_stock_info(code: str):
    """
    获取股票基本信息
    
    - **code**: 股票代码
    """
    try:
        logger.info(f"获取股票信息: code={code}")
        
        from app.services.modules.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        info = fetcher.get_stock_info(code)
        
        return info
        
    except Exception as e:
        logger.error(f"获取股票信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
