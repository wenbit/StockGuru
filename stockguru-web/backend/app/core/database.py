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
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=database_url
        )
        logger.info("数据库连接池初始化成功")
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}")
        raise


def get_db_connection():
    """
    从连接池获取数据库连接
    
    Returns:
        psycopg2.connection: 数据库连接
    """
    global _connection_pool
    
    if _connection_pool is None:
        init_db_pool()
    
    try:
        conn = _connection_pool.getconn()
        return conn
    except Exception as e:
        logger.error(f"获取数据库连接失败: {e}")
        raise


def return_db_connection(conn):
    """
    归还数据库连接到连接池
    
    Args:
        conn: 数据库连接
    """
    global _connection_pool
    
    if _connection_pool is not None and conn is not None:
        try:
            _connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"归还数据库连接失败: {e}")


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
            self.cursor.close()
        
        if exc_type is not None:
            # 发生异常，回滚
            if self.conn:
                self.conn.rollback()
        else:
            # 正常结束，提交
            if self.conn:
                self.conn.commit()
        
        if self.conn:
            return_db_connection(self.conn)
        
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
