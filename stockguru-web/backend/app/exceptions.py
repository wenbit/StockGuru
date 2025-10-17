"""
StockGuru 异常处理模块
借鉴 AKShare 的分层异常处理设计
"""


class StockGuruException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DataSourceError(StockGuruException):
    """数据源错误"""
    
    def __init__(self, message: str, source_name: str = None, status_code: int = None):
        self.source_name = source_name
        self.status_code = status_code
        prefix = f"[{source_name}]" if source_name else "[DataSource]"
        suffix = f" (Status: {status_code})" if status_code else ""
        super().__init__(f"{prefix} {message}{suffix}")


class DataValidationError(StockGuruException):
    """数据验证错误"""
    
    def __init__(self, message: str, field_name: str = None):
        self.field_name = field_name
        prefix = f"[{field_name}]" if field_name else "[Validation]"
        super().__init__(f"{prefix} {message}")


class RateLimitError(StockGuruException):
    """频率限制错误"""
    
    def __init__(self, message: str, retry_after: int = None, source_name: str = None):
        self.retry_after = retry_after
        self.source_name = source_name
        prefix = f"[{source_name}]" if source_name else "[RateLimit]"
        suffix = f" (Retry after {retry_after}s)" if retry_after else ""
        super().__init__(f"{prefix} {message}{suffix}")


class NetworkError(StockGuruException):
    """网络相关错误"""
    
    def __init__(self, message: str, attempts: int = None):
        self.attempts = attempts
        suffix = f" (Failed after {attempts} attempts)" if attempts else ""
        super().__init__(f"[Network] {message}{suffix}")


class DatabaseError(StockGuruException):
    """数据库错误"""
    
    def __init__(self, message: str, operation: str = None):
        self.operation = operation
        prefix = f"[DB:{operation}]" if operation else "[Database]"
        super().__init__(f"{prefix} {message}")


class CacheError(StockGuruException):
    """缓存错误"""
    
    def __init__(self, message: str, cache_type: str = None):
        self.cache_type = cache_type
        prefix = f"[Cache:{cache_type}]" if cache_type else "[Cache]"
        super().__init__(f"{prefix} {message}")


class InvalidParameterError(StockGuruException):
    """无效参数错误"""
    
    def __init__(self, message: str, param_name: str = None, param_value: any = None):
        self.param_name = param_name
        self.param_value = param_value
        details = f" (param: {param_name}={param_value})" if param_name else ""
        super().__init__(f"[InvalidParameter] {message}{details}")


class ConfigurationError(StockGuruException):
    """配置错误"""
    
    def __init__(self, message: str, config_key: str = None):
        self.config_key = config_key
        prefix = f"[Config:{config_key}]" if config_key else "[Configuration]"
        super().__init__(f"{prefix} {message}")
