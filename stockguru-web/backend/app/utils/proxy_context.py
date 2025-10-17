"""
代理上下文管理器
借鉴 AKShare 的上下文管理器设计
"""

from contextlib import contextmanager
from typing import Optional, Dict
import logging
import threading

logger = logging.getLogger(__name__)


class GlobalConfig:
    """全局配置（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.proxies = None
                    cls._instance.timeout = 15
                    cls._instance.max_retries = 3
        return cls._instance
    
    @classmethod
    def set_proxies(cls, proxies: Optional[Dict]):
        """设置全局代理"""
        cls().proxies = proxies
        if proxies:
            logger.info(f"Global proxies set: {proxies}")
        else:
            logger.info("Global proxies cleared")
    
    @classmethod
    def get_proxies(cls) -> Optional[Dict]:
        """获取全局代理"""
        return cls().proxies
    
    @classmethod
    def set_timeout(cls, timeout: int):
        """设置全局超时"""
        cls().timeout = timeout
        logger.info(f"Global timeout set: {timeout}s")
    
    @classmethod
    def get_timeout(cls) -> int:
        """获取全局超时"""
        return cls().timeout
    
    @classmethod
    def set_max_retries(cls, max_retries: int):
        """设置全局最大重试次数"""
        cls().max_retries = max_retries
        logger.info(f"Global max_retries set: {max_retries}")
    
    @classmethod
    def get_max_retries(cls) -> int:
        """获取全局最大重试次数"""
        return cls().max_retries


@contextmanager
def use_proxy(proxies: Dict):
    """
    临时使用代理的上下文管理器
    
    Usage:
        with use_proxy({'http': 'http://proxy:8080', 'https': 'http://proxy:8080'}):
            data = fetch_data()  # 使用代理
        # 自动恢复原配置
    
    Args:
        proxies: 代理配置字典
    """
    config = GlobalConfig()
    old_proxies = config.get_proxies()
    
    try:
        config.set_proxies(proxies)
        logger.debug(f"Proxy context entered: {proxies}")
        yield
    finally:
        config.set_proxies(old_proxies)
        logger.debug(f"Proxy context exited, restored: {old_proxies}")


@contextmanager
def use_timeout(timeout: int):
    """
    临时设置超时的上下文管理器
    
    Usage:
        with use_timeout(30):
            data = fetch_data()  # 使用30秒超时
        # 自动恢复原配置
    
    Args:
        timeout: 超时时间（秒）
    """
    config = GlobalConfig()
    old_timeout = config.get_timeout()
    
    try:
        config.set_timeout(timeout)
        logger.debug(f"Timeout context entered: {timeout}s")
        yield
    finally:
        config.set_timeout(old_timeout)
        logger.debug(f"Timeout context exited, restored: {old_timeout}s")


@contextmanager
def use_config(proxies: Optional[Dict] = None, timeout: Optional[int] = None, max_retries: Optional[int] = None):
    """
    临时设置多个配置的上下文管理器
    
    Usage:
        with use_config(proxies={'http': 'proxy:8080'}, timeout=30, max_retries=5):
            data = fetch_data()  # 使用临时配置
        # 自动恢复所有配置
    
    Args:
        proxies: 代理配置
        timeout: 超时时间
        max_retries: 最大重试次数
    """
    config = GlobalConfig()
    
    # 保存原配置
    old_proxies = config.get_proxies()
    old_timeout = config.get_timeout()
    old_max_retries = config.get_max_retries()
    
    try:
        # 设置新配置
        if proxies is not None:
            config.set_proxies(proxies)
        if timeout is not None:
            config.set_timeout(timeout)
        if max_retries is not None:
            config.set_max_retries(max_retries)
        
        logger.debug(f"Config context entered: proxies={proxies}, timeout={timeout}, max_retries={max_retries}")
        yield
    
    finally:
        # 恢复原配置
        config.set_proxies(old_proxies)
        config.set_timeout(old_timeout)
        config.set_max_retries(old_max_retries)
        logger.debug("Config context exited, all settings restored")


# 全局配置实例
global_config = GlobalConfig()


# 便捷函数
def set_global_proxy(proxies: Dict):
    """设置全局代理"""
    global_config.set_proxies(proxies)


def clear_global_proxy():
    """清除全局代理"""
    global_config.set_proxies(None)


def get_global_proxy() -> Optional[Dict]:
    """获取全局代理"""
    return global_config.get_proxies()


def set_global_timeout(timeout: int):
    """设置全局超时"""
    global_config.set_timeout(timeout)


def get_global_timeout() -> int:
    """获取全局超时"""
    return global_config.get_timeout()
