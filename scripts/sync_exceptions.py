#!/usr/bin/env python3
"""
数据同步自定义异常
用于区分不同类型的错误，实现针对性的错误处理
"""


class SyncException(Exception):
    """同步异常基类"""
    def __init__(self, message, details=None, retryable=True):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.retryable = retryable
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ==================== 数据库相关异常 ====================

class DatabaseException(SyncException):
    """数据库异常基类"""
    pass


class DatabaseConnectionError(DatabaseException):
    """数据库连接错误 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class DatabaseTimeoutError(DatabaseException):
    """数据库超时错误 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class DatabaseQueryError(DatabaseException):
    """数据库查询错误 - 不可重试（SQL语法错误等）"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class DatabaseIntegrityError(DatabaseException):
    """数据库完整性错误 - 不可重试（唯一约束冲突等）"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


# ==================== 网络相关异常 ====================

class NetworkException(SyncException):
    """网络异常基类"""
    pass


class NetworkConnectionError(NetworkException):
    """网络连接错误 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class NetworkTimeoutError(NetworkException):
    """网络超时错误 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


# ==================== 数据源相关异常 ====================

class DataSourceException(SyncException):
    """数据源异常基类"""
    pass


class BaostockLoginError(DataSourceException):
    """Baostock登录失败 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class BaostockQueryError(DataSourceException):
    """Baostock查询失败 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class DataNotFoundError(DataSourceException):
    """数据未找到 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class DataFormatError(DataSourceException):
    """数据格式错误 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


# ==================== 业务逻辑异常 ====================

class BusinessException(SyncException):
    """业务逻辑异常基类"""
    pass


class InvalidDateError(BusinessException):
    """无效日期 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class NonTradingDayError(BusinessException):
    """非交易日 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class AlreadySyncedError(BusinessException):
    """已同步 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class DataIncompleteError(BusinessException):
    """数据不完整 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


# ==================== 系统相关异常 ====================

class SystemException(SyncException):
    """系统异常基类"""
    pass


class ProcessTimeoutError(SystemException):
    """进程超时 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class ProcessCrashedError(SystemException):
    """进程崩溃 - 可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=True)


class ConfigurationError(SystemException):
    """配置错误 - 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


class ResourceExhaustedError(SystemException):
    """资源耗尽（内存、磁盘等）- 不可重试"""
    def __init__(self, message, details=None):
        super().__init__(message, details, retryable=False)


# ==================== 工具函数 ====================

def classify_exception(exc: Exception) -> SyncException:
    """
    将标准异常分类为自定义异常
    
    Args:
        exc: 原始异常
    
    Returns:
        分类后的自定义异常
    """
    import psycopg2
    import socket
    import subprocess
    
    exc_str = str(exc).lower()
    
    # 数据库异常
    if isinstance(exc, psycopg2.OperationalError):
        if 'connection' in exc_str or 'closed' in exc_str:
            return DatabaseConnectionError(str(exc), {'original_type': type(exc).__name__})
        elif 'timeout' in exc_str:
            return DatabaseTimeoutError(str(exc), {'original_type': type(exc).__name__})
        else:
            return DatabaseException(str(exc), {'original_type': type(exc).__name__})
    
    elif isinstance(exc, psycopg2.IntegrityError):
        return DatabaseIntegrityError(str(exc), {'original_type': type(exc).__name__})
    
    elif isinstance(exc, psycopg2.ProgrammingError):
        return DatabaseQueryError(str(exc), {'original_type': type(exc).__name__})
    
    # 网络异常
    elif isinstance(exc, (socket.timeout, TimeoutError)):
        return NetworkTimeoutError(str(exc), {'original_type': type(exc).__name__})
    
    elif isinstance(exc, (socket.error, ConnectionError)):
        return NetworkConnectionError(str(exc), {'original_type': type(exc).__name__})
    
    # 进程异常
    elif isinstance(exc, subprocess.TimeoutExpired):
        return ProcessTimeoutError(str(exc), {'original_type': type(exc).__name__})
    
    # 值错误
    elif isinstance(exc, ValueError):
        if 'date' in exc_str:
            return InvalidDateError(str(exc), {'original_type': type(exc).__name__})
        else:
            return DataFormatError(str(exc), {'original_type': type(exc).__name__})
    
    # 默认返回通用异常
    return SyncException(str(exc), {'original_type': type(exc).__name__}, retryable=True)


def should_retry(exc: Exception) -> bool:
    """
    判断异常是否应该重试
    
    Args:
        exc: 异常对象
    
    Returns:
        是否应该重试
    """
    if isinstance(exc, SyncException):
        return exc.retryable
    
    # 对于未分类的异常，默认可重试
    return True


def get_retry_delay(exc: Exception, attempt: int, base_delay: int = 5) -> int:
    """
    根据异常类型和尝试次数计算重试延迟
    
    Args:
        exc: 异常对象
        attempt: 当前尝试次数（从1开始）
        base_delay: 基础延迟（秒）
    
    Returns:
        延迟秒数
    """
    # 网络和连接错误使用指数退避
    if isinstance(exc, (NetworkException, DatabaseConnectionError)):
        return min(base_delay * (2 ** (attempt - 1)), 60)  # 最多60秒
    
    # 超时错误使用线性增长
    elif isinstance(exc, (NetworkTimeoutError, DatabaseTimeoutError, ProcessTimeoutError)):
        return base_delay + (attempt - 1) * 5  # 每次增加5秒
    
    # 其他错误使用固定延迟
    else:
        return base_delay
