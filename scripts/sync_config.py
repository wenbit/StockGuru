#!/usr/bin/env python3
"""
数据同步配置文件
集中管理所有同步相关的配置参数
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
project_root = Path(__file__).parent.parent
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')


class SyncConfig:
    """同步配置类"""
    
    # ==================== 数据库配置 ====================
    DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('NEON_DATABASE_URL')
    
    # 连接池配置
    DB_POOL_MIN_CONN = int(os.getenv('DB_POOL_MIN_CONN', '2'))
    DB_POOL_MAX_CONN = int(os.getenv('DB_POOL_MAX_CONN', '10'))
    
    # 连接超时配置
    DB_CONNECT_TIMEOUT = int(os.getenv('DB_CONNECT_TIMEOUT', '30'))
    DB_QUERY_TIMEOUT = int(os.getenv('DB_QUERY_TIMEOUT', '300'))
    
    # 重连配置
    RECONNECT_INTERVAL = int(os.getenv('RECONNECT_INTERVAL', '300'))  # 5分钟
    RECONNECT_MAX_RETRIES = int(os.getenv('RECONNECT_MAX_RETRIES', '3'))
    
    # ==================== 同步配置 ====================
    # 批量大小
    BATCH_SIZE = int(os.getenv('SYNC_BATCH_SIZE', '500'))
    
    # 重试配置
    MAX_RETRIES_PER_DATE = int(os.getenv('MAX_RETRIES_PER_DATE', '3'))
    RETRY_WAIT_SECONDS = int(os.getenv('RETRY_WAIT_SECONDS', '5'))
    
    # 错误检测配置
    MAX_ERROR_COUNT = int(os.getenv('MAX_ERROR_COUNT', '10'))
    ERROR_WINDOW_SECONDS = int(os.getenv('ERROR_WINDOW_SECONDS', '30'))
    
    # 超时配置
    SYNC_TIMEOUT_SECONDS = int(os.getenv('SYNC_TIMEOUT_SECONDS', '1800'))  # 30分钟
    
    # 日期间隔
    DATE_INTERVAL_SECONDS = int(os.getenv('DATE_INTERVAL_SECONDS', '2'))
    
    # ==================== 日志配置 ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/sync.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ==================== 监控配置 ====================
    # 是否启用性能监控
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    
    # 是否启用健康检查
    ENABLE_HEALTH_CHECK = os.getenv('ENABLE_HEALTH_CHECK', 'true').lower() == 'true'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
    
    # ==================== 告警配置 ====================
    # 是否启用告警
    ENABLE_ALERT = os.getenv('ENABLE_ALERT', 'false').lower() == 'true'
    ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')
    
    # 告警阈值
    ALERT_FAILURE_THRESHOLD = int(os.getenv('ALERT_FAILURE_THRESHOLD', '3'))
    ALERT_SLOW_THRESHOLD = int(os.getenv('ALERT_SLOW_THRESHOLD', '1200'))  # 20分钟
    
    # ==================== 交易日配置 ====================
    # 交易日判断方式: 'simple' / 'calendar' / 'database'
    TRADING_DAY_METHOD = os.getenv('TRADING_DAY_METHOD', 'simple')
    
    # ==================== Baostock配置 ====================
    BAOSTOCK_RETRY = int(os.getenv('BAOSTOCK_RETRY', '3'))
    BAOSTOCK_TIMEOUT = int(os.getenv('BAOSTOCK_TIMEOUT', '30'))
    
    # ==================== 调试配置 ====================
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        
        # 验证必需配置
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL 未设置")
        
        # 验证数值范围
        if cls.BATCH_SIZE < 1 or cls.BATCH_SIZE > 1000:
            errors.append(f"BATCH_SIZE 超出范围: {cls.BATCH_SIZE}")
        
        if cls.MAX_RETRIES_PER_DATE < 1 or cls.MAX_RETRIES_PER_DATE > 10:
            errors.append(f"MAX_RETRIES_PER_DATE 超出范围: {cls.MAX_RETRIES_PER_DATE}")
        
        if cls.SYNC_TIMEOUT_SECONDS < 60:
            errors.append(f"SYNC_TIMEOUT_SECONDS 过小: {cls.SYNC_TIMEOUT_SECONDS}")
        
        # 验证日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if cls.LOG_LEVEL.upper() not in valid_levels:
            errors.append(f"LOG_LEVEL 无效: {cls.LOG_LEVEL}")
        
        # 验证交易日判断方式
        valid_methods = ['simple', 'calendar', 'database']
        if cls.TRADING_DAY_METHOD not in valid_methods:
            errors.append(f"TRADING_DAY_METHOD 无效: {cls.TRADING_DAY_METHOD}")
        
        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        print("=" * 80)
        print("当前同步配置")
        print("=" * 80)
        print(f"数据库: {cls.DATABASE_URL[:50]}...")
        print(f"批量大小: {cls.BATCH_SIZE}")
        print(f"重试次数: {cls.MAX_RETRIES_PER_DATE}")
        print(f"错误阈值: {cls.MAX_ERROR_COUNT}")
        print(f"同步超时: {cls.SYNC_TIMEOUT_SECONDS}秒")
        print(f"重连间隔: {cls.RECONNECT_INTERVAL}秒")
        print(f"日志级别: {cls.LOG_LEVEL}")
        print(f"交易日判断: {cls.TRADING_DAY_METHOD}")
        print(f"性能监控: {'启用' if cls.ENABLE_METRICS else '禁用'}")
        print(f"健康检查: {'启用' if cls.ENABLE_HEALTH_CHECK else '禁用'}")
        print(f"告警功能: {'启用' if cls.ENABLE_ALERT else '禁用'}")
        print(f"调试模式: {'启用' if cls.DEBUG_MODE else '禁用'}")
        print("=" * 80)


# 导出配置实例
config = SyncConfig()

# 验证配置
try:
    config.validate()
except ValueError as e:
    print(f"配置错误: {e}")
    raise


if __name__ == '__main__':
    # 打印配置
    config.print_config()
