"""
Redis 缓存服务
实现多级缓存，提升查询性能
"""

import json
import logging
from typing import Any, Optional, List
from datetime import timedelta
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis 未安装，缓存功能将被禁用")

logger = logging.getLogger(__name__)


class RedisCacheService:
    """Redis 缓存服务"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None):
        """
        初始化 Redis 连接
        
        Args:
            host: Redis 主机
            port: Redis 端口
            db: 数据库编号
            password: 密码（可选）
        """
        self.logger = logging.getLogger(__name__)
        self.enabled = REDIS_AVAILABLE
        
        if not self.enabled:
            self.logger.warning("Redis 缓存已禁用")
            self.client = None
            return
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self.client.ping()
            self.logger.info(f"Redis 连接成功: {host}:{port}")
        except Exception as e:
            self.logger.error(f"Redis 连接失败: {e}")
            self.enabled = False
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在返回 None
        """
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"获取缓存失败 {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认1小时
            
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            self.logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            self.logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的所有键
        
        Args:
            pattern: 键模式（如 'stock:*'）
            
        Returns:
            删除的键数量
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            self.logger.error(f"删除模式缓存失败 {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if not self.enabled:
            return False
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            self.logger.error(f"检查缓存失败 {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余秒数，-1表示永不过期，-2表示不存在
        """
        if not self.enabled:
            return -2
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            self.logger.error(f"获取TTL失败 {key}: {e}")
            return -2
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增计数器
        
        Args:
            key: 缓存键
            amount: 递增量
            
        Returns:
            递增后的值
        """
        if not self.enabled:
            return None
        
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"递增失败 {key}: {e}")
            return None
    
    def get_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.client.info('stats')
            return {
                'enabled': True,
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': self.client.info('memory').get('used_memory_human', 'N/A')
            }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {'enabled': True, 'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round(hits / total * 100, 2)
    
    def flush_all(self) -> bool:
        """
        清空所有缓存（谨慎使用）
        
        Returns:
            是否成功
        """
        if not self.enabled:
            return False
        
        try:
            self.client.flushdb()
            self.logger.warning("已清空所有缓存")
            return True
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")
            return False


def cached(ttl: int = 3600, key_prefix: str = ''):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 键前缀
        
    Example:
        @cached(ttl=300, key_prefix='stock')
        def get_stock_data(stock_code):
            return fetch_from_db(stock_code)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cache = RedisCacheService()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value
            
            # 缓存未命中，执行函数
            result = func(*args, **kwargs)
            
            # 保存到缓存
            cache.set(cache_key, result, ttl)
            logger.debug(f"缓存保存: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


# 全局缓存实例
_cache_instance = None

def get_cache() -> RedisCacheService:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCacheService()
    return _cache_instance
