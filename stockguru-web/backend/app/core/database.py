"""
PostgreSQL 数据库连接管理
使用连接池提高性能
"""

import os
import logging
from typing import Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

_connection_pool: Optional[pool.ThreadedConnectionPool] = None


def init_db_pool():
    """初始化数据库连接池"""
    global _connection_pool
    
    if _connection_pool is not None:
        return
    
    # 获取数据库URL（优先使用NEON_DATABASE_URL）
    database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("未找到数据库连接URL (DATABASE_URL 或 NEON_DATABASE_URL)")
        raise ValueError("数据库连接URL未配置")
    
    try:
        # 先测试单个连接
        logger.info("测试数据库连接...")
        test_conn = psycopg2.connect(database_url, connect_timeout=15)
        test_conn.close()
        logger.info("数据库连接测试成功")
        
        # 创建连接池
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=2,               # 减少最小连接数
            maxconn=20,              # 减少最大连接数
            dsn=database_url,
            # 连接保活参数
            keepalives=1,
            keepalives_idle=30,      # 30秒后开始发送keepalive
            keepalives_interval=10,  # 每10秒发送一次
            keepalives_count=5,      # 5次失败后断开
            # 连接超时（增加到30秒）
            connect_timeout=30,
            # 应用名称（便于数据库监控）
            application_name='stockguru_backend'
        )
        logger.info("数据库连接池初始化成功 (minconn=2, maxconn=20)")
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}")
        raise


def get_db_connection():
    """
    从连接池获取数据库连接，并进行健康检查
    
    Returns:
        psycopg2.connection: 数据库连接
    """
    global _connection_pool
    
    if _connection_pool is None:
        init_db_pool()
    
    try:
        conn = _connection_pool.getconn()
        
        # 健康检查：测试连接是否有效
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # 连接已断开，关闭并重新获取
            logger.warning(f"检测到无效连接，重新获取: {e}")
            try:
                conn.close()
            except:
                pass
            # 从连接池移除坏连接并获取新连接
            conn = _connection_pool.getconn()
            # 再次测试新连接
            with conn.cursor() as cursor:
                cursor.execute('SELECT 1')
        
        return conn
    except Exception as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise


def return_db_connection(conn, close_on_error: bool = False):
    """
    归还数据库连接到连接池
    
    Args:
        conn: 数据库连接
        close_on_error: 如果连接有问题，是否关闭而不是归还
    """
    global _connection_pool
    
    if _connection_pool is not None and conn is not None:
        try:
            # 检查连接是否仍然有效
            if conn.closed:
                logger.warning("连接已关闭，不归还到连接池")
                try:
                    _connection_pool.putconn(conn, close=True)
                except:
                    pass
                return
            
            # 归还连接
            _connection_pool.putconn(conn, close=close_on_error)
        except Exception as e:
            logger.error(f"归还数据库连接失败: {e}")
            try:
                conn.close()
            except:
                pass


def close_db_pool():
    """关闭数据库连接池"""
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            _connection_pool.closeall()
            _connection_pool = None
            logger.info("数据库连接池已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接池失败: {e}")


class DatabaseConnection:
    """数据库连接上下文管理器"""
    
    def __init__(self, dict_cursor: bool = True):
        """
        初始化
        
        Args:
            dict_cursor: 是否使用字典游标（返回字典而不是元组）
        """
        self.conn = None
        self.cursor = None
        self.dict_cursor = dict_cursor
    
    def __enter__(self):
        """进入上下文"""
        self.conn = get_db_connection()
        if self.dict_cursor:
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            self.cursor = self.conn.cursor()
        return self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.cursor:
            try:
                self.cursor.close()
            except:
                pass
        
        close_on_error = False
        
        if exc_type is not None:
            # 发生异常，回滚
            if self.conn:
                try:
                    self.conn.rollback()
                except (psycopg2.OperationalError, psycopg2.InterfaceError):
                    # 连接已断开，标记为需要关闭
                    logger.warning("回滚失败，连接可能已断开")
                    close_on_error = True
        else:
            # 正常结束，提交
            if self.conn:
                try:
                    self.conn.commit()
                except (psycopg2.OperationalError, psycopg2.InterfaceError):
                    # 连接已断开，标记为需要关闭
                    logger.warning("提交失败，连接可能已断开")
                    close_on_error = True
        
        if self.conn:
            return_db_connection(self.conn, close_on_error=close_on_error)
        
        return False  # 不抑制异常


# 便捷函数
def execute_query(sql: str, params: tuple = None, fetch_one: bool = False, dict_cursor: bool = True):
    """
    执行查询并返回结果
    
    Args:
        sql: SQL语句
        params: 参数
        fetch_one: 是否只返回一条记录
        dict_cursor: 是否使用字典游标
    
    Returns:
        查询结果
    """
    with DatabaseConnection(dict_cursor=dict_cursor) as cursor:
        cursor.execute(sql, params)
        if fetch_one:
            return cursor.fetchone()
        else:
            return cursor.fetchall()


def execute_update(sql: str, params: tuple = None):
    """
    执行更新操作
    
    Args:
        sql: SQL语句
        params: 参数
    
    Returns:
        影响的行数
    """
    with DatabaseConnection() as cursor:
        cursor.execute(sql, params)
        return cursor.rowcount
