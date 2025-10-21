#!/usr/bin/env python3
"""
测试同步状态管理功能
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.sync_status_service import SyncStatusService


def test_basic_operations():
    """测试基本操作"""
    print("\n" + "="*80)
    print("测试基本操作")
    print("="*80)
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 1. 创建待同步记录
    print("\n1. 创建待同步记录...")
    result = SyncStatusService.mark_as_pending(
        sync_date=today,
        remarks="测试创建"
    )
    print(f"✅ 创建成功: {result['sync_date']} - {result['status']}")
    
    # 2. 标记为同步中
    print("\n2. 标记为同步中...")
    result = SyncStatusService.mark_as_syncing(
        sync_date=today,
        process_id=str(os.getpid())
    )
    print(f"✅ 更新成功: {result['sync_date']} - {result['status']} (进程: {result['process_id']})")
    
    # 3. 标记为成功
    print("\n3. 标记为成功...")
    result = SyncStatusService.mark_as_success(
        sync_date=today,
        total_records=5000,
        success_count=5000,
        remarks="测试成功"
    )
    print(f"✅ 更新成功: {result['sync_date']} - {result['status']} ({result['total_records']} 条)")
    
    # 4. 创建失败记录
    print("\n4. 创建失败记录...")
    result = SyncStatusService.mark_as_failed(
        sync_date=yesterday,
        error_message="测试失败",
        total_records=5000,
        success_count=3000,
        failed_count=2000
    )
    print(f"✅ 创建成功: {result['sync_date']} - {result['status']}")
    print(f"   成功: {result['success_count']}, 失败: {result['failed_count']}")


def test_check_need_sync():
    """测试同步需求检查"""
    print("\n" + "="*80)
    print("测试同步需求检查")
    print("="*80)
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 检查今天（应该是success，无需同步）
    print(f"\n检查 {today}:")
    need_sync, reason = SyncStatusService.check_need_sync(today)
    print(f"  需要同步: {need_sync}")
    print(f"  原因: {reason}")
    
    # 检查昨天（应该是failed，需要同步）
    print(f"\n检查 {yesterday}:")
    need_sync, reason = SyncStatusService.check_need_sync(yesterday)
    print(f"  需要同步: {need_sync}")
    print(f"  原因: {reason}")
    
    # 检查一个不存在的日期
    test_date = today - timedelta(days=7)
    print(f"\n检查 {test_date}:")
    need_sync, reason = SyncStatusService.check_need_sync(test_date)
    print(f"  需要同步: {need_sync}")
    print(f"  原因: {reason}")


def test_get_pending_dates():
    """测试获取待同步日期"""
    print("\n" + "="*80)
    print("测试获取待同步日期")
    print("="*80)
    
    pending_dates = SyncStatusService.get_pending_dates(days_back=30)
    
    print(f"\n发现 {len(pending_dates)} 个待同步日期:")
    for sync_date in pending_dates[:10]:  # 只显示前10个
        need_sync, reason = SyncStatusService.check_need_sync(sync_date)
        print(f"  - {sync_date}: {reason}")


def test_get_recent_status():
    """测试获取最近状态"""
    print("\n" + "="*80)
    print("测试获取最近状态")
    print("="*80)
    
    recent_status = SyncStatusService.get_recent_status(days=7)
    
    print(f"\n最近7天的同步状态 (共 {len(recent_status)} 条):")
    print(f"{'日期':<12} {'状态':<10} {'总数':<8} {'成功':<8} {'失败':<8} {'耗时(秒)':<10}")
    print("-" * 70)
    
    for record in recent_status[:10]:
        print(f"{record['sync_date']!s:<12} "
              f"{record['status']:<10} "
              f"{record['total_records'] or 0:<8} "
              f"{record['success_count'] or 0:<8} "
              f"{record['failed_count'] or 0:<8} "
              f"{record['duration_seconds'] or 0:<10}")


def test_process_detection():
    """测试进程检测"""
    print("\n" + "="*80)
    print("测试进程检测")
    print("="*80)
    
    # 当前进程（应该存在）
    current_pid = str(os.getpid())
    print(f"\n当前进程 PID: {current_pid}")
    is_running = SyncStatusService.is_process_running(current_pid)
    print(f"  进程是否运行: {is_running} {'✅' if is_running else '❌'}")
    
    # 不存在的进程
    fake_pid = "999999"
    print(f"\n假进程 PID: {fake_pid}")
    is_running = SyncStatusService.is_process_running(fake_pid)
    print(f"  进程是否运行: {is_running} {'✅' if is_running else '❌'}")


def main():
    """主函数"""
    print("="*80)
    print("同步状态管理功能测试")
    print("="*80)
    
    try:
        # 运行所有测试
        test_basic_operations()
        test_check_need_sync()
        test_get_pending_dates()
        test_get_recent_status()
        test_process_detection()
        
        print("\n" + "="*80)
        print("✅ 所有测试完成")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
