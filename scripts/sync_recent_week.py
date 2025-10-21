#!/usr/bin/env python3
"""
同步最近一周的数据
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import subprocess

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.sync_status_service import SyncStatusService


def sync_recent_week():
    """同步最近一周的数据"""
    
    print("="*80)
    print("同步最近一周数据")
    print("="*80)
    print()
    
    # 获取最近7天的日期
    today = date.today()
    dates = []
    
    for i in range(7):
        sync_date = today - timedelta(days=i)
        dates.append(sync_date)
    
    print(f"日期范围: {dates[-1]} 至 {dates[0]}")
    print(f"共 {len(dates)} 天")
    print()
    
    # 检查每天的状态
    print("检查同步状态...")
    print("-"*80)
    
    need_sync = []
    already_synced = []
    
    for sync_date in dates:
        need, reason = SyncStatusService.check_need_sync(sync_date)
        
        if need:
            need_sync.append((sync_date, reason))
            print(f"⏳ {sync_date}: 需要同步 - {reason}")
        else:
            already_synced.append(sync_date)
            print(f"✅ {sync_date}: 已同步")
    
    print()
    print("="*80)
    print(f"统计: 需要同步 {len(need_sync)} 天, 已同步 {len(already_synced)} 天")
    print("="*80)
    print()
    
    if not need_sync:
        print("✅ 所有日期都已同步完成！")
        return
    
    # 开始同步
    print(f"开始同步 {len(need_sync)} 个日期...")
    print()
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, (sync_date, reason) in enumerate(need_sync, 1):
        date_str = sync_date.strftime('%Y-%m-%d')
        
        print(f"[{i}/{len(need_sync)}] 同步 {date_str}...")
        print(f"  原因: {reason}")
        
        # 使用test_copy_sync.py脚本同步
        script_path = project_root / 'scripts' / 'test_copy_sync.py'
        
        try:
            result = subprocess.run(
                ['python', str(script_path), '--all', '--date', date_str],
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0:
                # 检查输出判断是否成功
                if '总入库:' in result.stdout:
                    # 提取入库数量
                    for line in result.stdout.split('\n'):
                        if '总入库:' in line:
                            count = line.split(':')[1].strip().split()[0]
                            if int(count) > 0:
                                print(f"  ✅ 成功: {count} 条记录")
                                success_count += 1
                            else:
                                print(f"  ⏭️  跳过: 数据源暂无数据")
                                # 标记为待同步
                                SyncStatusService.mark_as_pending(
                                    sync_date=sync_date,
                                    remarks='数据源暂无数据，等待后续同步'
                                )
                                skipped_count += 1
                            break
                else:
                    print(f"  ⏭️  跳过: 数据源暂无数据")
                    SyncStatusService.mark_as_pending(
                        sync_date=sync_date,
                        remarks='数据源暂无数据，等待后续同步'
                    )
                    skipped_count += 1
            else:
                print(f"  ❌ 失败")
                SyncStatusService.mark_as_failed(
                    sync_date=sync_date,
                    error_message='同步脚本执行失败'
                )
                failed_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ 超时")
            SyncStatusService.mark_as_failed(
                sync_date=sync_date,
                error_message='同步超时'
            )
            failed_count += 1
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            SyncStatusService.mark_as_failed(
                sync_date=sync_date,
                error_message=str(e)
            )
            failed_count += 1
        
        print()
    
    # 最终统计
    print("="*80)
    print("同步完成")
    print("="*80)
    print()
    print(f"总计: {len(need_sync)} 个日期")
    print(f"  ✅ 成功: {success_count}")
    print(f"  ⏭️  跳过: {skipped_count} (数据源暂无数据)")
    print(f"  ❌ 失败: {failed_count}")
    print()
    
    if success_count > 0:
        print("✅ 部分数据同步成功")
    if skipped_count > 0:
        print("⏳ 部分日期待同步（数据源暂无数据）")
    if failed_count > 0:
        print("⚠️  部分日期同步失败，请检查日志")


if __name__ == '__main__':
    try:
        sync_recent_week()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
