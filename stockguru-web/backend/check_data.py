#!/usr/bin/env python3
"""检查数据库中的数据"""

import asyncio
from app.core.supabase import get_supabase_client

async def main():
    try:
        supabase = get_supabase_client()
        
        # 检查总记录数
        response = supabase.table('daily_stock_data').select('*', count='exact').limit(1).execute()
        total = response.count if hasattr(response, 'count') else 0
        
        print(f"✅ 数据库连接成功")
        print(f"📊 总记录数: {total}")
        
        if total > 0:
            # 获取最新的10条记录
            latest = supabase.table('daily_stock_data')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(10)\
                .execute()
            
            print(f"\n📝 最新10条记录:")
            for item in latest.data:
                print(f"  - {item['trade_date']} {item['stock_code']} {item['stock_name']} 涨跌幅: {item['change_pct']}%")
        else:
            print("\n⚠️  数据库中暂无数据")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
