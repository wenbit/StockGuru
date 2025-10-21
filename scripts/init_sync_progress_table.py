#!/usr/bin/env python3
"""
初始化同步进度表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 加载环境变量
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')


def init_sync_progress_table():
    """初始化同步进度表"""
    
    # 获取数据库URL
    database_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ 未找到数据库连接URL")
        return False
    
    print(f"📊 连接数据库...")
    
    try:
        # 连接数据库
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 读取SQL文件
        sql_file = project_root / 'stockguru-web' / 'database' / 'sync_progress_schema.sql'
        
        if not sql_file.exists():
            print(f"❌ SQL文件不存在: {sql_file}")
            return False
        
        print(f"📄 读取SQL文件: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 执行SQL
        print("🔧 创建表、索引和视图...")
        cursor.execute(sql)
        conn.commit()
        
        # 检查表是否创建成功
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'sync_progress'
        """)
        result = cursor.fetchone()
        
        if result['count'] > 0:
            print("✅ 表 sync_progress 创建成功")
            
            # 查询表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'sync_progress'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            print("\n📋 表结构:")
            print(f"{'列名':<20} {'类型':<20} {'可空':<10} {'默认值':<30}")
            print("-" * 80)
            for col in columns:
                print(f"{col['column_name']:<20} {col['data_type']:<20} {col['is_nullable']:<10} {str(col['column_default'] or ''):<30}")
            
            # 检查视图
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.views 
                WHERE table_name = 'sync_progress_summary'
            """)
            view_result = cursor.fetchone()
            
            if view_result['count'] > 0:
                print("\n✅ 视图 sync_progress_summary 创建成功")
            
            return True
        else:
            print("❌ 表创建失败")
            return False
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    print("=" * 80)
    print("初始化同步进度表")
    print("=" * 80)
    print()
    
    success = init_sync_progress_table()
    
    print()
    if success:
        print("✅ 初始化完成")
        print("\n下一步:")
        print("1. 测试断点续传: python scripts/test_resumable_sync.py")
        print("2. 查看API文档: http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("❌ 初始化失败")
        sys.exit(1)
