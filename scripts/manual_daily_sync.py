#!/usr/bin/env python3
"""
手动触发每日同步任务（模拟定时任务）
等同于每晚20点执行的自动同步
"""

import sys
import asyncio
from pathlib import Path
from datetime import date

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.daily_data_sync_service import get_sync_service


async def main():
    """执行每日同步任务"""
    print("="*80)
    print("手动触发每日同步任务（等同于20点定时任务）")
    print("="*80)
    print()
    
    try:
        sync_service = get_sync_service()
        
        # 同步今天的数据
        today = date.today()
        print(f"同步日期: {today}")
        print()
        
        result = await sync_service.sync_date_data(today)
        
        print()
        print("="*80)
        print("同步结果")
        print("="*80)
        
        if result['status'] == 'success':
            print(f"✅ 状态: 成功")
            print(f"📊 记录数: {result.get('inserted', 0)}")
            print(f"💾 数据库: 已入库")
        elif result['status'] == 'skipped':
            print(f"⏭️  状态: 跳过")
            print(f"📝 原因: {result.get('message', '非交易日')}")
        else:
            print(f"❌ 状态: 失败")
            print(f"📝 错误: {result.get('message', '未知错误')}")
        
        print()
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
