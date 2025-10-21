#!/usr/bin/env python3
"""
智能同步程序
- 自动判断交易日
- 跳过非交易日
- 支持断点续传
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import subprocess

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

from dotenv import load_dotenv
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

from app.services.sync_status_service import SyncStatusService
import baostock as bs


def is_trading_day(check_date: date) -> tuple[bool, str]:
    """
    判断是否为交易日
    
    Returns:
        (is_trading, reason)
    """
    try:
        bs.login()
        
        date_str = check_date.strftime('%Y-%m-%d')
        rs = bs.query_trade_dates(start_date=date_str, end_date=date_str)
        
        if rs.error_code == '0':
            while rs.next():
                row = rs.get_row_data()
                is_trading = row[1] == '1'
                
                bs.logout()
                
                if is_trading:
                    return True, "交易日"
                else:
                    return False, "非交易日"
        
        bs.logout()
        return False, "无法获取交易日历"
        
    except Exception as e:
        try:
            bs.logout()
        except:
            pass
        return False, f"查询失败: {str(e)}"


def sync_with_trading_day_check(days_back=7):
    """智能同步最近N天的数据"""
    
    print("="*80)
    print("智能同步程序（支持交易日判断）")
    print("="*80)
    print()
    
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(days_back)]
    
    print(f"日期范围: {dates[-1]} 至 {dates[0]}")
    print(f"共 {len(dates)} 天")
    print()
    
    # 第一步：检查交易日
    print("步骤1: 检查交易日...")
    print("-"*80)
    
    trading_days = []
    non_trading_days = []
    
    for check_date in dates:
        is_trading, reason = is_trading_day(check_date)
        
        if is_trading:
            trading_days.append(check_date)
            print(f"✅ {check_date}: {reason}")
        else:
            non_trading_days.append((check_date, reason))
            print(f"❌ {check_date}: {reason}")
            
            # 标记非交易日为skipped
            SyncStatusService.mark_as_skipped(
                sync_date=check_date,
                remarks=f"非交易日（{reason}）"
            )
    
    print()
    print(f"交易日: {len(trading_days)} 天")
    print(f"非交易日: {len(non_trading_days)} 天")
    print()
    
    if not trading_days:
        print("✅ 没有需要同步的交易日")
        return
    
    # 第二步：检查同步状态
    print("步骤2: 检查同步状态...")
    print("-"*80)
    
    need_sync = []
    already_synced = []
    
    for sync_date in trading_days:
        need, reason = SyncStatusService.check_need_sync(sync_date)
        
        if need:
            need_sync.append((sync_date, reason))
            print(f"⏳ {sync_date}: 需要同步 - {reason}")
        else:
            already_synced.append(sync_date)
            print(f"✅ {sync_date}: 已同步")
    
    print()
    print(f"需要同步: {len(need_sync)} 天")
    print(f"已同步: {len(already_synced)} 天")
    print()
    
    if not need_sync:
        print("✅ 所有交易日都已同步完成！")
        return
    
    # 第三步：执行同步
    print("步骤3: 执行同步...")
    print("="*80)
    print()
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, (sync_date, reason) in enumerate(need_sync, 1):
        date_str = sync_date.strftime('%Y-%m-%d')
        
        print(f"[{i}/{len(need_sync)}] 同步 {date_str}...")
        print(f"  原因: {reason}")
        
        script_path = project_root / 'scripts' / 'test_copy_sync.py'
        
        try:
            result = subprocess.run(
                ['python', str(script_path), '--all', '--date', date_str],
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                if '总入库:' in result.stdout:
                    for line in result.stdout.split('\n'):
                        if '总入库:' in line:
                            count_str = line.split(':')[1].strip().split()[0]
                            count = int(count_str)
                            
                            if count > 0:
                                print(f"  ✅ 成功: {count:,} 条记录")
                                success_count += 1
                            else:
                                print(f"  ⏭️  跳过: 数据源暂无数据")
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
    print(f"总计: {len(dates)} 天")
    print(f"  ✅ 交易日: {len(trading_days)} 天")
    print(f"  ❌ 非交易日: {len(non_trading_days)} 天（已标记为跳过）")
    print()
    print(f"同步结果:")
    print(f"  ✅ 成功: {success_count} 天")
    print(f"  ⏭️  跳过: {skipped_count} 天（数据源暂无数据）")
    print(f"  ❌ 失败: {failed_count} 天")
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='智能同步程序')
    parser.add_argument('--days', type=int, default=7, help='同步最近N天（默认7天）')
    args = parser.parse_args()
    
    try:
        sync_with_trading_day_check(days_back=args.days)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
