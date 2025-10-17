#!/usr/bin/env python3
"""
实测全量同步
使用最新的 Neon 同步接口
"""

import sys
import os
from datetime import date, timedelta

# 设置环境变量
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_mezvj6EIcM0a@ep-aged-leaf-a19jn0y0-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

def main():
    print("\n" + "=" * 70)
    print("🚀 全量同步实测")
    print("=" * 70)
    print()
    
    try:
        from app.services.daily_data_sync_service_neon import DailyDataSyncServiceNeon
        
        # 初始化服务
        print("初始化同步服务...")
        service = DailyDataSyncServiceNeon()
        print("✅ 初始化成功")
        print()
        
        # 选择同步日期
        print("选择同步日期:")
        print("  1. 昨天 (2025-10-16)")
        print("  2. 前天 (2025-10-15)")
        print("  3. 大前天 (2025-10-14)")
        print()
        
        choice = input("请选择 (1-3，默认2): ").strip() or "2"
        
        if choice == "1":
            sync_date = date.today() - timedelta(days=1)
        elif choice == "3":
            sync_date = date.today() - timedelta(days=3)
        else:
            sync_date = date.today() - timedelta(days=2)
        
        print(f"\n同步日期: {sync_date.strftime('%Y-%m-%d')}")
        print("开始全量同步...")
        print()
        print("=" * 70)
        print("🔄 开始同步...")
        print("=" * 70)
        print()
        
        # 执行同步
        result = service.sync_daily_data(sync_date)
        
        print()
        print("=" * 70)
        print("📊 同步结果")
        print("=" * 70)
        print()
        
        if result.get('success'):
            print(f"✅ 同步成功")
            print()
            print(f"统计信息:")
            print(f"  同步日期: {result.get('date', sync_date)}")
            print(f"  成功数量: {result.get('success_count', 0)}")
            print(f"  失败数量: {result.get('failed_count', 0)}")
            print(f"  总耗时: {result.get('elapsed_time', 0):.2f}秒 ({result.get('elapsed_time', 0)/60:.2f}分钟)")
            
            if result.get('success_count', 0) > 0:
                speed = result.get('success_count', 0) / result.get('elapsed_time', 1)
                print(f"  平均速度: {speed:.2f} 股/秒")
            
            print()
            
            # 性能评价
            elapsed_min = result.get('elapsed_time', 0) / 60
            
            print("性能评价:")
            if elapsed_min < 10:
                print("  ✅ 优秀 (<10分钟)")
            elif elapsed_min < 15:
                print("  ✅ 良好 (10-15分钟)")
            elif elapsed_min < 20:
                print("  ⚠️  一般 (15-20分钟)")
            else:
                print("  ❌ 较慢 (>20分钟)")
            
            print()
            
            # 对比预估
            print("对比预估:")
            print(f"  预估时间: 12.8分钟")
            print(f"  实际时间: {elapsed_min:.1f}分钟")
            diff = abs(12.8 - elapsed_min)
            print(f"  差异: {diff:.1f}分钟 ({diff/12.8*100:.1f}%)")
            print()
            
        else:
            print(f"❌ 同步失败")
            print(f"   错误: {result.get('error', '未知错误')}")
            print()
        
        return 0
    
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
