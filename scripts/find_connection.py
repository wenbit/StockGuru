#!/usr/bin/env python3
"""
尝试找到正确的 PostgreSQL 连接配置
"""

import psycopg2

# 项目信息
project_ref = "mislyhozlviaedinpnfa"
password = "sg2025GO"

# 可能的连接配置
configs = [
    # 直接连接
    {
        "name": "Direct Connection (IPv6)",
        "host": f"db.{project_ref}.supabase.co",
        "port": 5432,
        "user": "postgres",
    },
    # Transaction pooler
    {
        "name": "Transaction Pooler",
        "host": f"db.{project_ref}.supabase.co",
        "port": 6543,
        "user": "postgres",
    },
    # Session pooler  
    {
        "name": "Session Pooler",
        "host": f"db.{project_ref}.supabase.co",
        "port": 5432,
        "user": "postgres",
    },
    # 新格式用户名
    {
        "name": "Direct with project user",
        "host": f"db.{project_ref}.supabase.co",
        "port": 5432,
        "user": f"postgres.{project_ref}",
    },
    # Pooler with project user
    {
        "name": "Pooler with project user",
        "host": f"db.{project_ref}.supabase.co",
        "port": 6543,
        "user": f"postgres.{project_ref}",
    },
]

print("🔍 尝试不同的连接配置...\n")

for config in configs:
    print(f"测试: {config['name']}")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  User: {config['user']}")
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database='postgres',
            user=config['user'],
            password=password,
            sslmode='require',
            connect_timeout=5
        )
        
        print(f"  ✅ 连接成功！\n")
        print("="*60)
        print("🎉 找到可用配置:")
        print(f"  Host: {config['host']}")
        print(f"  Port: {config['port']}")
        print(f"  User: {config['user']}")
        print("="*60)
        
        # 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\nPostgreSQL 版本: {version[:50]}...")
        
        cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
        count = cursor.fetchone()[0]
        print(f"daily_stock_data 记录数: {count:,}")
        
        conn.close()
        break
        
    except Exception as e:
        error_msg = str(e).split('\n')[0][:80]
        print(f"  ❌ 失败: {error_msg}\n")
        continue
else:
    print("\n❌ 所有配置都失败了")
    print("\n可能的原因:")
    print("1. 密码不正确")
    print("2. Supabase 项目已暂停（Free tier 7天无活动会暂停）")
    print("3. 需要从 Supabase Dashboard 重新获取连接信息")
