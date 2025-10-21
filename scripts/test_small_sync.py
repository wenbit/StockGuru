#!/usr/bin/env python3
"""
测试小批量同步（只同步10只股票）
"""

import sys
import os
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.resumable_sync_service import get_resumable_sync_service
from app.core.database import DatabaseConnection


def test_small_sync():
    """测试小批量同步"""
    
    today = date.today()
    
    print("="*80)
    print(f"测试小批量同步: {today}")
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
            """, (today, code, name))
    
    print(f"✅ 已初始化 {len(test_stocks)} 只股票")
    
    # 2. 查看进度
    progress = sync_service.get_progress(today)
    print(f"\n2. 当前进度:")
    print(f"   总数: {progress['total']}")
    print(f"   待同步: {progress['pending']}")
    
    # 3. 开始同步
    print(f"\n3. 开始同步...")
    print()
    
    date_str = today.strftime('%Y-%m-%d')
    success_count = 0
    failed_count = 0
    
    pending = sync_service.get_pending_stocks(today, limit=10)
    
    for i, stock in enumerate(pending, 1):
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        
        print(f"[{i}/{len(pending)}] {stock_code} {stock_name}...", end=' ')
        
        # 获取数据
        data = sync_service.fetch_stock_data(stock_code, date_str)
        
        if data:
            data['stock_name'] = stock_name
            if sync_service.save_stock_data(today, stock_code, data):
                sync_service.mark_stock_success(today, stock_code)
                success_count += 1
                print(f"✅ 成功")
            else:
                sync_service.mark_stock_failed(today, stock_code, "保存失败")
                failed_count += 1
                print(f"❌ 保存失败")
        else:
            sync_service.mark_stock_failed(today, stock_code, "获取数据失败")
            failed_count += 1
            print(f"❌ 获取失败")
    
    # 4. 最终进度
    print()
    progress = sync_service.get_progress(today)
    print(f"4. 同步完成:")
    print(f"   总数: {progress['total']}")
    print(f"   成功: {progress['success']}")
    print(f"   失败: {progress['failed']}")
    print(f"   待同步: {progress['pending']}")
    print(f"   进度: {progress['progress']:.1f}%")
    
    # 5. 清理
    print(f"\n5. 清理测试数据...")
    sync_service.clear_progress(today)
    print("✅ 清理完成")
    
    print("\n" + "="*80)
    if success_count > 0:
        print(f"✅ 测试成功！成功同步 {success_count} 只股票")
    else:
        print("⚠️  所有股票同步失败，请检查baostock连接")
    print("="*80)


if __name__ == '__main__':
    try:
        test_small_sync()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
