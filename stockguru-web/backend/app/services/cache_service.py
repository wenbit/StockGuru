"""
数据缓存服务 - 确保历史数据查询结果一致性
"""
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """数据缓存服务"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """初始化缓存服务"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"缓存目录: {self.cache_dir}")
    
    def _get_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 将参数转换为字符串并排序，确保一致性
        params_str = json.dumps(params, sort_keys=True)
        hash_str = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}_{hash_str}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_historical_date(self, date_str: str) -> bool:
        """判断是否为历史日期（不是今天）"""
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            return query_date < today
        except:
            return False
    
    def get(self, prefix: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            prefix: 缓存前缀（如 'screening', 'volume', 'hot'）
            params: 查询参数
            
        Returns:
            缓存的数据，如果不存在返回 None
        """
        try:
            cache_key = self._get_cache_key(prefix, params)
            cache_path = self._get_cache_path(cache_key)
            
            if not cache_path.exists():
                logger.debug(f"缓存未命中: {cache_key}")
                return None
            
            # 读取缓存
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期（只对今天的数据设置过期时间）
            date_str = params.get('date', '')
            if not self._is_historical_date(date_str):
                # 今天的数据，设置1小时过期
                cached_at = datetime.fromisoformat(cache_data['cached_at'])
                if datetime.now() - cached_at > timedelta(hours=1):
                    logger.info(f"缓存已过期: {cache_key}")
                    return None
            
            logger.info(f"缓存命中: {cache_key}")
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None
    
    def set(self, prefix: str, params: Dict[str, Any], data: Any) -> bool:
        """
        设置缓存数据
        
        Args:
            prefix: 缓存前缀
            params: 查询参数
            data: 要缓存的数据
            
        Returns:
            是否成功
        """
        try:
            cache_key = self._get_cache_key(prefix, params)
            cache_path = self._get_cache_path(cache_key)
            
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'params': params,
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"缓存已保存: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    def clear_old_cache(self, days: int = 30):
        """
        清理旧缓存
        
        Args:
            days: 保留最近N天的缓存
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            count = 0
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cached_at = datetime.fromisoformat(cache_data['cached_at'])
                    if cached_at < cutoff_time:
                        cache_file.unlink()
                        count += 1
                except:
                    pass
            
            logger.info(f"清理了 {count} 个旧缓存文件")
            return count
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
            return 0


# 全局缓存实例
_cache_service = None

def get_cache_service() -> CacheService:
    """获取缓存服务实例"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
