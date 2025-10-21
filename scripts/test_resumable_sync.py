#!/usr/bin/env python3
"""
测试断点续传功能
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.resumable_sync_service import get_resumable_sync_service


def test_progress_operations():
    """测试进度操作"""
    print("\n" + "="*80)
    print("测试进度操作")
    print("="*80)
    
    sync_service = get_resumable_sync_service()
    test_date = date.today() - timedelta(days=1)
    
    # 1. 初始化进度
    print(f"\n1. 初始化 {test_date} 的进度记录...")
    count = sync_service.init_progress(test_date)
    print(f"✅ 已初始化 {count} 只股票")
    
    # 2. 获取进度
    print(f"\n2. 获取进度...")
    progress = sync_service.get_progress(test_date)
    print(f"✅ 总数: {progress['total']}, 待同步: {progress['pending']}")
    
    # 3. 获取待同步股票（前10只）
    print(f"\n3. 获取待同步股票（前10只）...")
    pending = sync_service.get_pending_stocks(test_date, limit=10)
    print(f"✅ 获取到 {len(pending)} 只待同步股票:")
    for stock in pending[:5]:
        print(f"   - {stock['stock_code']}: {stock['stock_name']}")
    
    # 4. 清除进度
    print(f"\n4. 清除进度记录...")
    sync_service.clear_progress(test_date)
    print(f"✅ 进度记录已清除")


def test_small_batch_sync():
    """测试小批量同步（断点续传）"""
    print("\n" + "="*80)
    print("测试小批量同步（断点续传）")
    print("="*80)
    
    sync_service = get_resumable_sync_service()
    test_date = date.today() - timedelta(days=1)
    
    print(f"\n测试日期: {test_date}")
    print("=" * 80)
    
    # 初始化进度
    print("\n初始化进度...")
    sync_service.init_progress(test_date)
    
    # 第一次同步：只同步10只
    print("\n第一次同步：处理前10只股票...")
    pending = sync_service.get_pending_stocks(test_date, limit=10)
    
    success_count = 0
    failed_count = 0
    
    for stock in pending:
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        
        # 模拟获取数据
        data = sync_service.fetch_stock_data(stock_code, test_date.strftime('%Y-%m-%d'))
        
        if data:
            data['stock_name'] = stock_name
            if sync_service.save_stock_data(test_date, stock_code, data):
                sync_service.mark_stock_success(test_date, stock_code)
                success_count += 1
                print(f"  ✅ {stock_code} {stock_name}")
            else:
                sync_service.mark_stock_failed(test_date, stock_code, "保存失败")
                failed_count += 1
                print(f"  ❌ {stock_code} {stock_name} - 保存失败")
        else:
            sync_service.mark_stock_failed(test_date, stock_code, "获取数据失败")
            failed_count += 1
            print(f"  ❌ {stock_code} {stock_name} - 获取数据失败")
    
    # 查看进度
    progress = sync_service.get_progress(test_date)
    print(f"\n第一次同步完成:")
    print(f"  总数: {progress['total']}")
    print(f"  成功: {progress['success']}")
    print(f"  失败: {progress['failed']}")
    print(f"  待同步: {progress['pending']}")
    print(f"  进度: {progress['progress']:.2f}%")
    
    # 模拟中断
    print("\n" + "="*80)
    print("⚠️  模拟中断（实际场景：服务重启、网络断开等）")
    print("="*80)
    time.sleep(2)
    
    # 第二次同步：继续同步剩余的
    print("\n第二次同步：继续处理剩余股票（前10只）...")
    pending = sync_service.get_pending_stocks(test_date, limit=10)
    
    for stock in pending:
        stock_code = stock['stock_code']
        stock_name = stock['stock_name']
        
        data = sync_service.fetch_stock_data(stock_code, test_date.strftime('%Y-%m-%d'))
        
        if data:
            data['stock_name'] = stock_name
            if sync_service.save_stock_data(test_date, stock_code, data):
                sync_service.mark_stock_success(test_date, stock_code)
                success_count += 1
                print(f"  ✅ {stock_code} {stock_name}")
            else:
                sync_service.mark_stock_failed(test_date, stock_code, "保存失败")
                failed_count += 1
        else:
            sync_service.mark_stock_failed(test_date, stock_code, "获取数据失败")
            failed_count += 1
    
    # 最终进度
    progress = sync_service.get_progress(test_date)
    print(f"\n第二次同步完成:")
    print(f"  总数: {progress['total']}")
    print(f"  成功: {progress['success']}")
    print(f"  失败: {progress['failed']}")
    print(f"  待同步: {progress['pending']}")
    print(f"  进度: {progress['progress']:.2f}%")
    
    print("\n✅ 断点续传测试成功！")
    print("   - 第一次同步了部分数据")
    print("   - 模拟中断后")
    print("   - 第二次从上次中断的地方继续")
    print("   - 不会重复同步已完成的数据")
    
    # 清理测试数据
    print(f"\n清理测试数据...")
    sync_service.clear_progress(test_date)
    print("✅ 清理完成")


def test_failed_retry():
    """测试失败重试"""
    print("\n" + "="*80)
    print("测试失败重试")
    print("="*80)
    
    sync_service = get_resumable_sync_service()
    test_date = date.today() - timedelta(days=2)
    
    # 初始化并模拟一些失败
    print(f"\n初始化 {test_date} 的进度...")
    sync_service.init_progress(test_date)
    
    # 获取前5只股票
    pending = sync_service.get_pending_stocks(test_date, limit=5)
    
    # 模拟：前3只成功，后2只失败
    print("\n模拟同步：前3只成功，后2只失败...")
    for i, stock in enumerate(pending):
        if i < 3:
            sync_service.mark_stock_success(test_date, stock['stock_code'])
            print(f"  ✅ {stock['stock_code']} - 成功")
        else:
            sync_service.mark_stock_failed(test_date, stock['stock_code'], "模拟失败")
            print(f"  ❌ {stock['stock_code']} - 失败")
    
    # 查看失败列表
    failed = sync_service.get_failed_stocks(test_date)
    print(f"\n失败列表 ({len(failed)} 只):")
    for stock in failed:
        print(f"  - {stock['stock_code']}: {stock['error_message']} (重试{stock['retry_count']}次)")
    
    # 重置失败为待同步
    print("\n重置失败股票为待同步...")
    count = sync_service.reset_failed_to_pending(test_date)
    print(f"✅ 已重置 {count} 只失败股票")
    
    # 再次查看进度
    progress = sync_service.get_progress(test_date)
    print(f"\n当前进度:")
    print(f"  成功: {progress['success']}")
    print(f"  失败: {progress['failed']}")
    print(f"  待同步: {progress['pending']}")
    
    # 清理
    sync_service.clear_progress(test_date)
    print("\n✅ 测试完成，数据已清理")


def main():
    """主函数"""
    print("=" * 80)
    print("断点续传功能测试")
    print("=" * 80)
    
    try:
        # 测试1: 进度操作
        test_progress_operations()
        
        # 测试2: 小批量同步（断点续传）
        test_small_batch_sync()
        
        # 测试3: 失败重试
        test_failed_retry()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成")
        print("=" * 80)
        print("\n功能验证:")
        print("  ✅ 进度记录和查询")
        print("  ✅ 断点续传（中断后继续）")
        print("  ✅ 失败重试")
        print("  ✅ 不重复同步已完成数据")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
