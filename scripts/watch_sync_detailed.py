#!/usr/bin/env python3
"""
实时监控后端数据同步进度（详细版）
包含 API 进度和数据库实际数据
"""

import os
import sys
import time
import requests
import psycopg2
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
project_root = Path(__file__).parent.parent
load_dotenv(project_root / 'stockguru-web' / 'backend' / '.env')

def get_api_progress():
    """获取 API 进度"""
    try:
        response = requests.get('http://localhost:8000/api/v1/sync-status/sync/batch/active', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success' and data.get('data'):
                return data['data'].get('progress', {})
        return None
    except:
        return None

def get_db_stats(sync_date):
    """获取数据库统计"""
    try:
        db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
        if not db_url:
            return None
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 获取数据量
        cur.execute("""
            SELECT COUNT(*) 
            FROM daily_stock_data 
            WHERE trade_date = %s
        """, (sync_date,))
        count = cur.fetchone()[0]
        
        # 获取同步状态
        cur.execute("""
            SELECT status, success_count, failed_count
            FROM daily_sync_status
            WHERE sync_date = %s
        """, (sync_date,))
        
        status_row = cur.fetchone()
        cur.close()
        conn.close()
        
        return {
            'db_count': count,
            'status': status_row[0] if status_row else 'unknown',
            'success': status_row[1] if status_row else 0,
            'failed': status_row[2] if status_row else 0
        }
    except:
        return None

def draw_progress_bar(percent, width=40):
    """绘制进度条"""
    filled = int(width * percent / 100)
    bar = '█' * filled + '░' * (width - filled)
    return bar

def main():
    """主函数"""
    print("🔍 实时监控后端数据同步进度（详细版）")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            # 清屏
            os.system('clear' if os.name != 'nt' else 'cls')
            
            current_time = datetime.now().strftime('%H:%M:%S')
            
            print("╔" + "═" * 78 + "╗")
            print("║" + " " * 20 + "🔄 后端数据同步实时进度" + " " * 35 + "║")
            print("╠" + "═" * 78 + "╣")
            print(f"║ ⏰ 时间: {current_time}" + " " * 65 + "║")
            
            # 获取 API 进度
            progress = get_api_progress()
            
            if progress:
                status = progress.get('status', '-')
                current = progress.get('current', 0)
                total = progress.get('total', 0)
                success = progress.get('success', 0)
                failed = progress.get('failed', 0)
                skipped = progress.get('skipped', 0)
                current_date = progress.get('current_date', '-')
                progress_pct = progress.get('progress_percent', 0)
                message = progress.get('message', '-')
                start_time = progress.get('start_time', '-')
                end_time = progress.get('end_time', '-')
                
                print(f"║ 📊 状态: {status:10s}" + " " * 57 + "║")
                print(f"║ 📅 当前日期: {current_date}" + " " * 60 + "║")
                print(f"║ 📆 范围: {start_time} ~ {end_time}" + " " * 45 + "║")
                print("╠" + "═" * 78 + "╣")
                
                # 进度条
                bar = draw_progress_bar(progress_pct)
                print(f"║ 进度: [{bar}] {progress_pct:.1f}%" + " " * (32 - len(f"{progress_pct:.1f}")) + "║")
                print("║" + " " * 78 + "║")
                
                # 统计信息
                print(f"║ 📈 总数: {total:3d} 天" + " " * 63 + "║")
                print(f"║ 🔵 当前: {current:3d}/{total:3d}" + " " * 63 + "║")
                print(f"║ ✅ 成功: {success:3d}" + " " * 66 + "║")
                print(f"║ ❌ 失败: {failed:3d}" + " " * 66 + "║")
                print(f"║ ⏭️  跳过: {skipped:3d}" + " " * 66 + "║")
                
                # 获取数据库统计
                db_stats = get_db_stats(current_date)
                if db_stats:
                    print("╠" + "═" * 78 + "╣")
                    print("║ 💾 数据库实际数据:" + " " * 59 + "║")
                    print(f"║    记录数: {db_stats['db_count']:5d} 条" + " " * 60 + "║")
                    print(f"║    状态: {db_stats['status']:10s}" + " " * 59 + "║")
                    print(f"║    成功: {db_stats['success']:5d}" + " " * 63 + "║")
                    print(f"║    失败: {db_stats['failed']:5d}" + " " * 63 + "║")
                
                print("╠" + "═" * 78 + "╣")
                print(f"║ 💬 {message[:74]}" + " " * (74 - len(message[:74])) + "║")
                print("╚" + "═" * 78 + "╝")
                
                # 检查是否完成
                if status == 'completed' or progress_pct >= 100.0:
                    print("\n✅ 同步已完成！")
                    break
                    
            else:
                print("║" + " " * 78 + "║")
                print("║ 📭 当前没有活动的同步任务" + " " * 50 + "║")
                print("║" + " " * 78 + "║")
                print("╚" + "═" * 78 + "╝")
            
            # 等待 2 秒
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  监控已停止")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")

if __name__ == '__main__':
    main()
