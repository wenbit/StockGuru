#!/usr/bin/env python3
"""
同步最近1周的股票数据
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta
import subprocess

project_root = Path(__file__).parent.parent

print("="*80)
print("同步最近1周的股票数据")
print("="*80)
print()

# 计算最近7天的日期
today = date.today()
dates = []
for i in range(7, 0, -1):
    sync_date = today - timedelta(days=i)
    dates.append(sync_date)

print(f"将同步以下日期的数据:")
for i, d in enumerate(dates, 1):
    print(f"  {i}. {d} ({d.strftime('%A')})")

print()
print("开始同步...")
print("="*80)
print()

success_count = 0
failed_dates = []

for i, sync_date in enumerate(dates, 1):
    date_str = sync_date.strftime('%Y-%m-%d')
    print(f"\n[{i}/7] 同步 {date_str}...")
    print("-"*80)
    
    try:
        # 调用同步脚本
        result = subprocess.run(
            ['python3', 'scripts/test_copy_sync.py', '--all', '--date', date_str],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            # 检查输出中是否有成功标记
            if '总入库:' in result.stdout and '条记录' in result.stdout:
                # 提取入库记录数
                for line in result.stdout.split('\n'):
                    if '总入库:' in line:
                        print(f"✅ {date_str} 同步成功")
                        print(f"   {line.strip()}")
                        success_count += 1
                        break
            elif '没有获取到任何数据' in result.stdout:
                print(f"⚠️  {date_str} 无数据（可能是非交易日或数据未更新）")
            else:
                print(f"✅ {date_str} 同步完成")
                success_count += 1
        else:
            print(f"❌ {date_str} 同步失败")
            failed_dates.append(date_str)
            if result.stderr:
                print(f"   错误: {result.stderr[:200]}")
    
    except subprocess.TimeoutExpired:
        print(f"⏱️  {date_str} 同步超时（超过30分钟）")
        failed_dates.append(date_str)
    except Exception as e:
        print(f"❌ {date_str} 同步异常: {e}")
        failed_dates.append(date_str)

print()
print("="*80)
print("同步完成")
print("="*80)
print()
print(f"📊 统计:")
print(f"   总日期数: {len(dates)}")
print(f"   成功: {success_count}")
print(f"   失败: {len(failed_dates)}")

if failed_dates:
    print(f"\n❌ 失败的日期:")
    for d in failed_dates:
        print(f"   - {d}")

print()
