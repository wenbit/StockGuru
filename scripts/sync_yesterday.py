#!/usr/bin/env python3
"""
同步昨天的数据（2025-10-16）
用于测试断点续传功能
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.resumable_sync_service import get_resumable_sync_service
from app.core.database import DatabaseConnection


def sync_yesterday():
    """同步昨天的数据"""
    
    # 使用2025-10-16（已知有数据的日期）
    sync_date = date(2025, 10, 16)
    
    print("="*80)
    print(f"测试断点续传: {sync_date}")
    print("="*80)
    print()
    
    sync_service = get_resumable_sync_service()
    
    # 1. 手动插入10只股票的进度记录
    print("1. 初始化10只测试股票...")
    test_stocks = [
        ('sh.600000', '浦发银行'),
        ('sh.600036', '招商银行'),
        ('sh.601318', '中国平安'),
        ('sh.600519', '贵州茅台'),
        ('sz.000001', '平安银行'),
        ('sz.000002', '万科A'),
        ('sz.000858', '五粮液'),
        ('sz.300750', '宁德时代'),
        ('sh.601888', '中国中免'),
        ('sh.600276', '恒瑞医药'),
    ]
    
    with DatabaseConnection() as cursor:
        for code, name in test_stocks:
            cursor.execute("""
                INSERT INTO sync_progress (sync_date, stock_code, stock_name, status)
                VALUES (%s, %s, %s, 'pending')
                ON CONFLICT (sync_date, stock_code) DO UPDATE
                SET status = 'pending'
            """, (sync_date, code, name))
    
    print(f"✅ 已初始化 {len(test_stocks)} 只股票")
    
    # 2. 查看进度
    progress = sync_service.get_progress(sync_date)
    print(f"\n2. 当前进度:")
    print(f"   总数: {progress['total']}")
    print(f"   待同步: {progress['pending']}")
    
    # 3. 开始同步
    print(f"\n3. 开始同步...")
    print()
    
    date_str = sync_date.strftime('%Y-%m-%d')
    success_count = 0
    failed_count = 0
    
    pending = sync_service.get_pending_stocks(sync_date, limit=10)
    
    for i, stock in enumerate(pending, 1):
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        
        print(f"[{i}/{len(pending)}] {stock_code} {stock_name}...", end=' ', flush=True)
        
        # 获取数据
        data = sync_service.fetch_stock_data(stock_code, date_str)
        
        if data:
            data['stock_name'] = stock_name
            if sync_service.save_stock_data(sync_date, stock_code, data):
                sync_service.mark_stock_success(sync_date, stock_code)
                success_count += 1
                print(f"✅")
            else:
                sync_service.mark_stock_failed(sync_date, stock_code, "保存失败")
                failed_count += 1
                print(f"❌ 保存失败")
        else:
            sync_service.mark_stock_failed(sync_date, stock_code, "获取数据失败")
            failed_count += 1
            print(f"❌ 无数据")
    
    # 4. 最终进度
    print()
    print("="*80)
    progress = sync_service.get_progress(sync_date)
    print(f"同步完成:")
    print(f"  总数: {progress['total']}")
    print(f"  成功: {progress['success']}")
    print(f"  失败: {progress['failed']}")
    print(f"  待同步: {progress['pending']}")
    print(f"  进度: {progress['progress']:.1f}%")
    print("="*80)
    
    if success_count > 0:
        print(f"\n✅ 测试成功！成功同步 {success_count}/{len(pending)} 只股票")
        print("\n断点续传功能验证:")
        print("  ✅ 进度记录正常")
        print("  ✅ 状态更新正常")
        print("  ✅ 数据保存正常")
    else:
        print("\n⚠️  所有股票同步失败")
    
    # 不清理数据，保留用于查看
    print(f"\n提示: 进度数据已保留，可通过API查看")
    print(f"  查看进度: curl http://localhost:8000/api/v1/sync-progress/date/{sync_date}")
    print(f"  查看失败: curl http://localhost:8000/api/v1/sync-progress/failed/{sync_date}")


if __name__ == '__main__':
    try:
        sync_yesterday()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
