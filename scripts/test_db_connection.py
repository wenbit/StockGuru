#!/usr/bin/env python3
"""
测试 Supabase PostgreSQL 直连
验证连接配置是否正确

使用方法:
    export SUPABASE_DB_PASSWORD='your_password'
    python scripts/test_db_connection.py
"""

import os
import sys
import psycopg2

def test_connection():
    """测试数据库连接"""
    
    # 从环境变量获取配置
    db_host = os.getenv('SUPABASE_DB_HOST', 'db.mislyhozlviaedinpnfa.supabase.co')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    db_port = int(os.getenv('SUPABASE_DB_PORT', '6543'))
    
    if not db_password:
        print("❌ 错误: 未设置 SUPABASE_DB_PASSWORD 环境变量")
        print("\n请运行:")
        print("export SUPABASE_DB_PASSWORD='your_password'")
        sys.exit(1)
    
    print("🔌 测试数据库连接...")
    print(f"Host: {db_host}")
    print(f"Port: {db_port}")
    print(f"Database: postgres")
    print(f"User: postgres")
    print("")
    
    try:
        # 尝试连接（尝试多种用户名格式）
        user_formats = [
            'postgres.mislyhozlviaedinpnfa',  # 新格式：postgres.[project-ref]
            'postgres',  # 旧格式
        ]
        
        conn = None
        last_error = None
        
        for user in user_formats:
            try:
                print(f"尝试用户名: {user}")
                conn = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    database='postgres',
                    user=user,
                    password=db_password,
                    sslmode='require',
                    connect_timeout=10
                )
                print(f"✅ 使用 {user} 连接成功！")
                break
            except Exception as e:
                last_error = e
                print(f"  失败: {e}")
                continue
        
        if conn is None:
            raise last_error
        
        print("✅ 连接成功！")
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n📊 PostgreSQL 版本:")
        print(version)
        
        # 检查表是否存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'daily_stock_data'
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("\n✅ daily_stock_data 表存在")
            
            # 查询记录数
            cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
            count = cursor.fetchone()[0]
            print(f"📈 当前记录数: {count:,} 条")
            
            # 查询最新日期
            cursor.execute("""
                SELECT MAX(trade_date) 
                FROM daily_stock_data
            """)
            latest_date = cursor.fetchone()[0]
            print(f"📅 最新数据日期: {latest_date}")
        else:
            print("\n⚠️  daily_stock_data 表不存在")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 所有测试通过！可以开始使用 PostgreSQL 直连方案。")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n请检查:")
        print("1. 数据库密码是否正确")
        print("2. 网络连接是否正常")
        print("3. Supabase 项目是否处于活跃状态")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
