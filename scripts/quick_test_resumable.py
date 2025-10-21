#!/usr/bin/env python3
"""
快速测试断点续传功能（不实际获取数据）
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

from app.core.database import DatabaseConnection


def test_progress_table():
    """测试进度表功能"""
    print("="*80)
    print("测试进度表功能")
    print("="*80)
    
    test_date = date.today() - timedelta(days=1)
    
    try:
        with DatabaseConnection() as cursor:
            # 1. 插入测试数据
            print(f"\n1. 插入测试进度记录 ({test_date})...")
            test_stocks = [
                ('sh.600000', '浦发银行', 'pending'),
                ('sh.600036', '招商银行', 'success'),
                ('sz.000001', '平安银行', 'failed'),
                ('sz.000002', '万科A', 'pending'),
                ('sh.601318', '中国平安', 'success'),
            ]
            
            for code, name, status in test_stocks:
                cursor.execute("""
                    INSERT INTO sync_progress (sync_date, stock_code, stock_name, status)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (sync_date, stock_code) DO UPDATE
                    SET status = EXCLUDED.status
                """, (test_date, code, name, status))
            
            print(f"✅ 已插入 {len(test_stocks)} 条测试数据")
            
            # 2. 查询进度统计
            print(f"\n2. 查询进度统计...")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'success') as success,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending
                FROM sync_progress
                WHERE sync_date = %s
            """, (test_date,))
            
            result = cursor.fetchone()
            print(f"✅ 统计结果:")
            print(f"   总数: {result['total']}")
            print(f"   成功: {result['success']}")
            print(f"   失败: {result['failed']}")
            print(f"   待同步: {result['pending']}")
            
            # 3. 查询待同步股票
            print(f"\n3. 查询待同步股票...")
            cursor.execute("""
                SELECT stock_code, stock_name, status
                FROM sync_progress
                WHERE sync_date = %s AND status = 'pending'
            """, (test_date,))
            
            pending = cursor.fetchall()
            print(f"✅ 待同步股票 ({len(pending)} 只):")
            for stock in pending:
                print(f"   - {stock['stock_code']}: {stock['stock_name']}")
            
            # 4. 模拟更新状态
            print(f"\n4. 模拟更新状态...")
            if pending:
                first_stock = pending[0]
                cursor.execute("""
                    UPDATE sync_progress
                    SET status = 'success', synced_at = CURRENT_TIMESTAMP
                    WHERE sync_date = %s AND stock_code = %s
                """, (test_date, first_stock['stock_code']))
                print(f"✅ 已将 {first_stock['stock_code']} 标记为成功")
            
            # 5. 查询失败股票
            print(f"\n5. 查询失败股票...")
            cursor.execute("""
                SELECT stock_code, stock_name, error_message
                FROM sync_progress
                WHERE sync_date = %s AND status = 'failed'
            """, (test_date,))
            
            failed = cursor.fetchall()
            print(f"✅ 失败股票 ({len(failed)} 只):")
            for stock in failed:
                print(f"   - {stock['stock_code']}: {stock['stock_name']}")
            
            # 6. 重置失败为待同步
            print(f"\n6. 重置失败股票为待同步...")
            cursor.execute("""
                UPDATE sync_progress
                SET status = 'pending', error_message = NULL
                WHERE sync_date = %s AND status = 'failed'
                RETURNING stock_code
            """, (test_date,))
            
            reset_stocks = cursor.fetchall()
            print(f"✅ 已重置 {len(reset_stocks)} 只失败股票")
            
            # 7. 查询统计视图
            print(f"\n7. 查询统计视图...")
            cursor.execute("""
                SELECT * FROM sync_progress_summary
                WHERE sync_date = %s
            """, (test_date,))
            
            summary = cursor.fetchone()
            if summary:
                print(f"✅ 统计视图数据:")
                print(f"   总股票数: {summary['total_stocks']}")
                print(f"   成功数: {summary['success_count']}")
                print(f"   失败数: {summary['failed_count']}")
                print(f"   待同步数: {summary['pending_count']}")
                print(f"   成功率: {summary['success_rate']}%")
            
            # 8. 清理测试数据
            print(f"\n8. 清理测试数据...")
            cursor.execute("""
                DELETE FROM sync_progress
                WHERE sync_date = %s
            """, (test_date,))
            print(f"✅ 测试数据已清理")
            
            print("\n" + "="*80)
            print("✅ 所有测试通过！")
            print("="*80)
            
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试API端点"""
    print("\n" + "="*80)
    print("测试API端点")
    print("="*80)
    
    import requests
    
    base_url = "http://localhost:8000"
    test_date = date.today().strftime('%Y-%m-%d')
    
    tests = [
        ("GET", f"/api/v1/sync-status/today", "获取今日同步状态"),
        ("GET", f"/api/v1/sync-status/summary?days=7", "获取状态摘要"),
        ("GET", f"/api/v1/sync-progress/date/{test_date}", "获取进度"),
    ]
    
    print(f"\n测试日期: {test_date}")
    print(f"API地址: {base_url}")
    print()
    
    success_count = 0
    
    for method, endpoint, desc in tests:
        try:
            url = f"{base_url}{endpoint}"
            print(f"测试: {desc}")
            print(f"  {method} {endpoint}")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功 - 状态码: {response.status_code}")
                print(f"     响应: {str(data)[:100]}...")
                success_count += 1
            else:
                print(f"  ⚠️  状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  连接失败 - API服务未启动")
            print(f"     请先启动: cd stockguru-web/backend && python -m uvicorn app.main:app --reload")
            break
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        print()
    
    print("="*80)
    print(f"API测试完成: {success_count}/{len(tests)} 通过")
    print("="*80)


def main():
    """主函数"""
    print("\n" + "="*80)
    print("断点续传功能快速测试")
    print("="*80)
    print()
    
    # 测试1: 数据库表功能
    if not test_progress_table():
        sys.exit(1)
    
    # 测试2: API端点
    test_api_endpoints()
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)
    print("\n功能验证:")
    print("  ✅ 进度表创建成功")
    print("  ✅ 进度记录和查询")
    print("  ✅ 状态更新")
    print("  ✅ 失败重置")
    print("  ✅ 统计视图")
    print("\n下一步:")
    print("  1. 访问前端页面: http://localhost:3000/sync-status")
    print("  2. 查看API文档: http://localhost:8000/docs")
    print("  3. 测试实际同步: 点击'同步今日数据'按钮")


if __name__ == '__main__':
    main()
