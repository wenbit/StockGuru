"""
数据压缩服务
使用 Parquet 格式压缩历史数据，节省存储空间
"""

import logging
import os
from pathlib import Path
from datetime import date, datetime
from typing import Optional
import pandas as pd
import psycopg2

logger = logging.getLogger(__name__)


class DataCompressionService:
    """数据压缩服务"""
    
    def __init__(self, database_url: str, archive_path: str = "data/archive"):
        self.database_url = database_url
        self.archive_path = Path(archive_path)
        self.archive_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export_to_parquet(self, start_date: date, end_date: date, 
                          filename: Optional[str] = None) -> str:
        """
        导出数据到 Parquet 文件
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            filename: 文件名（可选）
            
        Returns:
            导出的文件路径
        """
        try:
            # 连接数据库
            conn = psycopg2.connect(self.database_url)
            
            # 查询数据
            query = """
                SELECT 
                    stock_code, stock_name, trade_date,
                    open_price, close_price, high_price, low_price,
                    volume, amount, change_pct, change_amount,
                    turnover_rate, amplitude
                FROM daily_stock_data
                WHERE trade_date BETWEEN %s AND %s
                ORDER BY trade_date, stock_code
            """
            
            self.logger.info(f"导出数据: {start_date} 到 {end_date}")
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            conn.close()
            
            # 生成文件名
            if not filename:
                filename = f"stock_data_{start_date}_{end_date}.parquet"
            
            filepath = self.archive_path / filename
            
            # 导出为 Parquet（使用 snappy 压缩）
            df.to_parquet(
                filepath,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            
            # 统计信息
            original_size = len(df) * 200  # 估算原始大小（每行约200字节）
            compressed_size = filepath.stat().st_size
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            self.logger.info(f"导出完成: {filepath}")
            self.logger.info(f"记录数: {len(df)}")
            self.logger.info(f"原始大小（估算）: {original_size / 1024 / 1024:.2f} MB")
            self.logger.info(f"压缩后大小: {compressed_size / 1024 / 1024:.2f} MB")
            self.logger.info(f"压缩比: {compression_ratio:.2f}x")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"导出失败: {e}")
            raise
    
    def load_from_parquet(self, filepath: str) -> pd.DataFrame:
        """
        从 Parquet 文件加载数据
        
        Args:
            filepath: 文件路径
            
        Returns:
            DataFrame
        """
        try:
            df = pd.read_parquet(filepath)
            self.logger.info(f"加载数据: {filepath}")
            self.logger.info(f"记录数: {len(df)}")
            return df
            
        except Exception as e:
            self.logger.error(f"加载失败: {e}")
            raise
    
    def archive_old_data(self, months_old: int = 6) -> Dict:
        """
        归档旧数据
        
        Args:
            months_old: 归档多少个月前的数据
            
        Returns:
            归档统计信息
        """
        try:
            from datetime import timedelta
            
            # 计算截止日期
            cutoff_date = date.today() - timedelta(days=months_old * 30)
            
            # 导出旧数据
            filepath = self.export_to_parquet(
                date(2020, 1, 1),  # 假设最早日期
                cutoff_date,
                f"archive_{cutoff_date}.parquet"
            )
            
            # 可选：从数据库删除已归档的数据
            # conn = psycopg2.connect(self.database_url)
            # cursor = conn.cursor()
            # cursor.execute(
            #     "DELETE FROM daily_stock_data WHERE trade_date < %s",
            #     (cutoff_date,)
            # )
            # deleted_count = cursor.rowcount
            # conn.commit()
            # conn.close()
            
            return {
                'status': 'success',
                'filepath': filepath,
                'cutoff_date': str(cutoff_date)
            }
            
        except Exception as e:
            self.logger.error(f"归档失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_archive_list(self) -> List[Dict]:
        """
        获取归档文件列表
        
        Returns:
            归档文件列表
        """
        archives = []
        
        for file in self.archive_path.glob("*.parquet"):
            stat = file.stat()
            archives.append({
                'filename': file.name,
                'size': stat.st_size,
                'size_mb': stat.st_size / 1024 / 1024,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
        
        return sorted(archives, key=lambda x: x['modified'], reverse=True)
