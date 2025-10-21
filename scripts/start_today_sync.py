#!/usr/bin/env python3
"""
启动今日数据同步（支持断点续传）
"""

import sys
import os
from pathlib import Path
from datetime import date
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.resumable_sync_service import get_resumable_sync_service
from app.services.sync_status_service import SyncStatusService


def start_sync():
    """启动今日同步"""
    
    today = date.today()
    
    print("="*80)
    print(f"启动今日数据同步: {today}")
    print("="*80)
    print()
    
    sync_service = get_resumable_sync_service()
    
    # 1. 检查当前进度
    print("1. 检查当前进度...")
    progress = sync_service.get_progress(today)
    
    if progress['total'] == 0:
        print("   首次同步，需要初始化进度记录")
    else:
        print(f"   已有进度记录:")
        print(f"   - 总数: {progress['total']:,}")
        print(f"   - 成功: {progress['success']:,}")
        print(f"   - 失败: {progress['failed']:,}")
        print(f"   - 待同步: {progress['pending']:,}")
        print(f"   - 进度: {progress['progress']:.1f}%")
    
    # 2. 确认是否继续
    if progress['pending'] == 0 and progress['total'] > 0:
        print("\n   ✅ 所有股票已同步完成！")
        return
    
    print(f"\n2. 标记为同步中...")
    SyncStatusService.mark_as_syncing(today)
    print("   ✅ 已标记")
    
    # 3. 开始同步
    print(f"\n3. 开始同步...")
    print(f"   批次大小: 50")
    print(f"   最大重试: 3")
    print()
    
    start_time = time.time()
    
    try:
        result = sync_service.sync_with_resume(
            sync_date=today,
            batch_size=50,
            max_retries=3
        )
        
        end_time = time.time()
        duration = int(end_time - start_time)
        
        # 4. 显示结果
        print("\n" + "="*80)
        print("同步完成")
        print("="*80)
        
        if result['status'] == 'success':
            print(f"\n✅ 状态: 成功")
            print(f"\n统计:")
            print(f"  总数: {result['total']:,}")
            print(f"  成功: {result['success']:,}")
            print(f"  失败: {result['failed']:,}")
            print(f"  待同步: {result['pending']:,}")
            print(f"  进度: {result['progress']:.1f}%")
            print(f"\n耗时: {duration}秒 ({duration//60}分{duration%60}秒)")
            print(f"速度: {result['success']/duration:.1f} 股/秒")
            
            # 更新同步状态
            SyncStatusService.mark_as_success(
                sync_date=today,
                total_records=result['success'],
                success_count=result['success'],
                remarks=result.get('message', '')
            )
            
        elif result['status'] == 'partial':
            print(f"\n⚠️  状态: 部分完成")
            print(f"\n统计:")
            print(f"  总数: {result['total']:,}")
            print(f"  成功: {result['success']:,}")
            print(f"  失败: {result['failed']:,}")
            print(f"  待同步: {result['pending']:,}")
            print(f"\n建议: 可重新运行此脚本继续同步剩余股票")
            
            # 更新为部分失败
            SyncStatusService.mark_as_failed(
                sync_date=today,
                error_message=f"部分失败: {result['failed']} 只",
                total_records=result['total'],
                success_count=result['success'],
                failed_count=result['failed']
            )
            
        else:
            print(f"\n❌ 状态: 失败")
            print(f"错误: {result.get('error', '未知错误')}")
            
            SyncStatusService.mark_as_failed(
                sync_date=today,
                error_message=result.get('error', '同步失败')
            )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断同步")
        print("进度已保存，下次运行将继续同步")
        
        # 查看当前进度
        progress = sync_service.get_progress(today)
        print(f"\n当前进度:")
        print(f"  成功: {progress['success']:,}")
        print(f"  失败: {progress['failed']:,}")
        print(f"  待同步: {progress['pending']:,}")
        print(f"  完成度: {progress['progress']:.1f}%")
        
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        
        SyncStatusService.mark_as_failed(today, str(e))
        sys.exit(1)


if __name__ == '__main__':
    start_sync()
