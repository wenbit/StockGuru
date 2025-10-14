"""
股票相关 API
"""
from fastapi import APIRouter, HTTPException
import logging
import pandas as pd
import numpy as np
from app.services.modules.technical_indicators import TechnicalIndicators

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


@router.get("/stock/{code}/indicators")
async def get_stock_indicators(code: str, days: int = 60):
    """
    获取股票技术指标
    
    Args:
        code: 股票代码
        days: 天数 (默认60天)
        
    Returns:
        包含所有技术指标的数据
    """
    try:
        logger.info(f"获取股票技术指标: code={code}, days={days}")
        
        from app.services.modules.data_fetcher import DataFetcher
        fetcher = DataFetcher()
        
        # 获取K线数据
        df = fetcher.get_stock_daily_data(code, days=days)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的数据")
        
        # 计算所有技术指标
        df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)
        
        # 生成交易信号
        signals = TechnicalIndicators.get_indicator_signals(df_with_indicators)
        
        # 转换为JSON格式
        data = []
        for _, row in df_with_indicators.iterrows():
            item = {
                'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                'open': float(row['open']) if not pd.isna(row['open']) else None,
                'high': float(row['high']) if not pd.isna(row['high']) else None,
                'low': float(row['low']) if not pd.isna(row['low']) else None,
                'close': float(row['close']) if not pd.isna(row['close']) else None,
                'volume': float(row['volume']) if not pd.isna(row['volume']) else None,
                
                # MACD
                'macd_dif': float(row['macd_dif']) if not pd.isna(row.get('macd_dif')) else None,
                'macd_dea': float(row['macd_dea']) if not pd.isna(row.get('macd_dea')) else None,
                'macd': float(row['macd']) if not pd.isna(row.get('macd')) else None,
                
                # RSI
                'rsi': float(row['rsi']) if not pd.isna(row.get('rsi')) else None,
                
                # BOLL
                'boll_upper': float(row['boll_upper']) if not pd.isna(row.get('boll_upper')) else None,
                'boll_middle': float(row['boll_middle']) if not pd.isna(row.get('boll_middle')) else None,
                'boll_lower': float(row['boll_lower']) if not pd.isna(row.get('boll_lower')) else None,
                
                # KDJ
                'kdj_k': float(row['kdj_k']) if not pd.isna(row.get('kdj_k')) else None,
                'kdj_d': float(row['kdj_d']) if not pd.isna(row.get('kdj_d')) else None,
                'kdj_j': float(row['kdj_j']) if not pd.isna(row.get('kdj_j')) else None,
                
                # 成交量MA
                'volume_ma5': float(row['volume_ma5']) if not pd.isna(row.get('volume_ma5')) else None,
                'volume_ma10': float(row['volume_ma10']) if not pd.isna(row.get('volume_ma10')) else None,
                'volume_ma20': float(row['volume_ma20']) if not pd.isna(row.get('volume_ma20')) else None,
            }
            data.append(item)
        
        # 获取最新数据的统计信息
        latest = df_with_indicators.iloc[-1]
        stats = {
            'latest_close': float(latest['close']) if not pd.isna(latest['close']) else None,
            'latest_rsi': float(latest['rsi']) if not pd.isna(latest.get('rsi')) else None,
            'latest_macd': float(latest['macd']) if not pd.isna(latest.get('macd')) else None,
        }
        
        logger.info(f"成功获取技术指标: {len(data)} 条数据")
        
        return {
            'code': code,
            'data': data,
            'signals': signals,
            'stats': stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技术指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")
