"""
StockGuru FastAPI 主程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import screening, stock, daily_stock
from app.core.config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

app = FastAPI(
    title="StockGuru API",
    version="2.0.0",
    description="股票短线复盘助手 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（生产环境建议指定具体域名）
    allow_credentials=False,  # 允许所有来源时必须设为 False
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(screening.router, prefix="/api/v1", tags=["Screening"])
app.include_router(stock.router, prefix="/api/v1", tags=["Stock"])
app.include_router(daily_stock.router, prefix="/api/v1/daily", tags=["Daily Stock Data"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger = logging.getLogger(__name__)
    logger.info("StockGuru API 启动中...")
    
    # 启动定时任务调度器
    try:
        from app.services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("定时任务调度器已启动")
    except Exception as e:
        logger.error(f"启动定时任务调度器失败: {e}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger = logging.getLogger(__name__)
    logger.info("StockGuru API 关闭中...")
    
    # 关闭定时任务调度器
    try:
        from app.services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭定时任务调度器失败: {e}")

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "StockGuru API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
