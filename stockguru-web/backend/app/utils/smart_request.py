"""
智能HTTP请求封装
借鉴 AKShare 的指数退避重试机制
"""

import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from app.exceptions import (
    DataSourceError,
    RateLimitError,
    DataValidationError,
    NetworkError
)

logger = logging.getLogger(__name__)


class SmartRequest:
    """智能HTTP请求封装（借鉴 AKShare）"""
    
    @staticmethod
    def get_json(
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        proxies: Optional[Dict] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 15,
        source_name: str = "Unknown"
    ) -> Any:
        """
        发送 GET 请求并返回 JSON（支持指数退避重试）
        
        Args:
            url: 请求URL
            params: 查询参数
            headers: 请求头
            proxies: 代理配置
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            timeout: 超时时间
            source_name: 数据源名称
        
        Returns:
            JSON 数据
        
        Raises:
            DataSourceError: 数据源错误
            RateLimitError: 频率限制
            DataValidationError: 数据验证失败
            NetworkError: 网络错误
        """
        current_delay = retry_delay
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"[{source_name}] Request attempt {attempt + 1}/{max_retries}: {url}")
                
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout
                )
                
                # 成功
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if not data:
                            raise DataValidationError(
                                "Empty response data",
                                field_name="response"
                            )
                        logger.debug(f"[{source_name}] Request successful")
                        return data
                    except ValueError as e:
                        raise DataValidationError(
                            f"Failed to parse JSON: {e}",
                            field_name="json"
                        )
                
                # 频率限制
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        source_name=source_name
                    )
                
                # 其他错误
                else:
                    raise DataSourceError(
                        f"Request failed",
                        source_name=source_name,
                        status_code=response.status_code
                    )
            
            except Timeout:
                logger.warning(f"[{source_name}] Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise NetworkError(
                        "Request timeout",
                        attempts=max_retries
                    )
            
            except ConnectionError as e:
                logger.warning(f"[{source_name}] Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise NetworkError(
                        f"Connection failed: {e}",
                        attempts=max_retries
                    )
            
            except (RateLimitError, DataValidationError, DataSourceError) as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"[{source_name}] Error (attempt {attempt + 1}/{max_retries}): {e}")
            
            except RequestException as e:
                logger.error(f"[{source_name}] Request exception (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise NetworkError(
                        f"Request failed: {e}",
                        attempts=max_retries
                    )
            
            # 指数退避：1s -> 2s -> 4s
            if attempt < max_retries - 1:
                logger.info(f"[{source_name}] Retrying in {current_delay}s...")
                time.sleep(current_delay)
                current_delay *= 2  # 指数增长
        
        raise NetworkError(
            "Failed after all retries",
            attempts=max_retries
        )
    
    @staticmethod
    def get_text(
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        proxies: Optional[Dict] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 15,
        source_name: str = "Unknown"
    ) -> str:
        """
        发送 GET 请求并返回文本
        
        Args:
            同 get_json
        
        Returns:
            文本数据
        """
        current_delay = retry_delay
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    text = response.text
                    if not text:
                        raise DataValidationError(
                            "Empty response text",
                            field_name="response"
                        )
                    return text
                
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                        source_name=source_name
                    )
                
                else:
                    raise DataSourceError(
                        f"Request failed",
                        source_name=source_name,
                        status_code=response.status_code
                    )
            
            except (Timeout, ConnectionError, RequestException) as e:
                if attempt == max_retries - 1:
                    raise NetworkError(
                        f"Request failed: {e}",
                        attempts=max_retries
                    )
            
            # 指数退避
            if attempt < max_retries - 1:
                time.sleep(current_delay)
                current_delay *= 2
        
        raise NetworkError(
            "Failed after all retries",
            attempts=max_retries
        )


# 全局实例
smart_request = SmartRequest()
