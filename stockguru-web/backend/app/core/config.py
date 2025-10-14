from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # 前端地址
    FRONTEND_URL: str = "http://localhost:3000"
    
    # 筛选参数
    VOLUME_TOP_N: int = 100
    HOT_TOP_N: int = 100
    FINAL_TOP_N: int = 30
    MOMENTUM_DAYS: int = 25
    MOMENTUM_TOP_N: int = 10
    
    # 综合评分权重
    WEIGHT_VOLUME: float = 0.5
    WEIGHT_HOT: float = 0.5
    
    # 过滤规则
    EXCLUDE_ST: bool = True
    
    # 图表配置
    MA_PERIODS: list = [5, 10, 20]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "stockguru.log"
    
    # 数据获取配置
    KLINE_DAYS: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
