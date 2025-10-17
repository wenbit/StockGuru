#!/usr/bin/env python3
"""
迁移数据从 Supabase 到 Neon
"""

import os
import sys
import psycopg2
from supabase import create_client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Neon 连接信息
NEON_URL = "postgresql://neondb_owner:npg_mezvj6EIcM0a@ep-aged-leaf-a19jn0y0-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Supabase 连接信息
SUPABASE_URL = "https://mislyhozlviaedinpnfa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1pc2x5aG96bHZpYWVkaW5wbmZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA0MzAwNzEsImV4cCI6MjA3NjAwNjA3MX0.okEn31fdzMRV_k0SExYS-5TPdp7DngntKuvnPamV1Us"


def test_neon_connection():
    """测试 Neon 连接"""
    logger.info("测试 Neon 数据库连接...")
    try:
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✅ Neon 连接成功！")
        logger.info(f"PostgreSQL 版本: {version[:50]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Neon 连接失败: {e}")
        return False


def create_table_in_neon():
    """在 Neon 创建表结构"""
    logger.info("在 Neon 创建表结构...")
    
    schema_file = "/Users/van/dev/source/claudecode_src/StockGuru/stockguru-web/database/daily_stock_data_schema.sql"
    
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor()
        cursor.execute(schema_sql)
        conn.commit()
        logger.info("✅ 表结构创建成功")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ 创建表结构失败: {e}")
        return False


def export_data_from_supabase():
    """从 Supabase 导出数据"""
    logger.info("从 Supabase 导出数据...")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 分批导出数据
        all_data = []
        page_size = 1000
        offset = 0
        
        while True:
            response = supabase.table('daily_stock_data')\
                .select('*')\
                .range(offset, offset + page_size - 1)\
                .execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            offset += page_size
            logger.info(f"已导出 {len(all_data)} 条记录...")
            
            if len(response.data) < page_size:
                break
        
        logger.info(f"✅ 共导出 {len(all_data)} 条记录")
        return all_data
    except Exception as e:
        logger.error(f"❌ 导出数据失败: {e}")
        return None


def import_data_to_neon(data):
    """导入数据到 Neon"""
    logger.info(f"开始导入 {len(data)} 条记录到 Neon...")
    
    try:
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor()
        
        # 批量插入
        batch_size = 500
        total = len(data)
        
        for i in range(0, total, batch_size):
            batch = data[i:i + batch_size]
            
            # 构建批量插入语句
            values = []
            for record in batch:
                values.append(f"('{record['stock_code']}', '{record['stock_name']}', '{record['trade_date']}', "
                            f"{record['open_price'] or 'NULL'}, {record['close_price'] or 'NULL'}, "
                            f"{record['high_price'] or 'NULL'}, {record['low_price'] or 'NULL'}, "
                            f"{record['volume'] or 'NULL'}, {record['amount'] or 'NULL'}, "
                            f"{record['change_pct'] or 'NULL'}, {record['change_amount'] or 'NULL'}, "
                            f"{record['turnover_rate'] or 'NULL'}, {record['amplitude'] or 'NULL'})")
            
            sql = f"""
                INSERT INTO daily_stock_data (
                    stock_code, stock_name, trade_date,
                    open_price, close_price, high_price, low_price,
                    volume, amount, change_pct, change_amount,
                    turnover_rate, amplitude
                ) VALUES {','.join(values)}
                ON CONFLICT (stock_code, trade_date) DO NOTHING
            """
            
            cursor.execute(sql)
            conn.commit()
            
            logger.info(f"进度: {min(i + batch_size, total)}/{total}")
        
        logger.info("✅ 数据导入完成")
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
        count = cursor.fetchone()[0]
        logger.info(f"✅ Neon 数据库记录数: {count:,}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ 导入数据失败: {e}")
        return False


def main():
    logger.info("="*60)
    logger.info("开始数据库迁移：Supabase → Neon")
    logger.info("="*60)
    
    # 1. 测试连接
    if not test_neon_connection():
        sys.exit(1)
    
    # 2. 创建表结构
    if not create_table_in_neon():
        sys.exit(1)
    
    # 3. 导出数据
    data = export_data_from_supabase()
    if data is None:
        sys.exit(1)
    
    # 4. 导入数据
    if not import_data_to_neon(data):
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("🎉 数据库迁移完成！")
    logger.info("="*60)


if __name__ == '__main__':
    main()
