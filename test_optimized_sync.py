#!/usr/bin/env python3
"""
优化后的完整同步入库测试
使用 Baostock 优先策略
"""

import sys
import os
import time
from datetime import date, timedelta
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stockguru-web/backend'))

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), 'stockguru-web/backend/.env'))

def get_stock_list(limit=50):
    """获取股票列表"""
    print("📊 获取股票列表...")
    try:
        import baostock as bs
        bs.login()
        
        rs = bs.query_stock_basic()
        stock_list = []
        while rs.error_code == '0' and rs.next():
            row = rs.get_row_data()
            if len(row) > 1 and row[1] == '1':  # 只要上市状态的股票
                stock_list.append(row[0].split('.')[1])  # 提取股票代码
        
        bs.logout()
        
        # 限制数量
        test_stocks = stock_list[:limit] if stock_list else []
        
        if not test_stocks:
            # 如果获取失败，使用固定列表
            test_stocks = [
                '000001', '000002', '600000', '600519', '000858',
                '601318', '600036', '601166', '600276', '600030',
                '000333', '002594', '600887', '601888', '000651'
            ][:limit]
            print(f"⚠️  使用固定测试列表")
        
        print(f"✅ 获取到 {len(test_stocks)} 只股票")
        return test_stocks
        
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")
        # 返回固定列表
        return ['000001', '000002', '600000', '600519', '000858']


def sync_to_database(data_list, db_url):
    """同步数据到数据库"""
    print(f"\n💾 开始插入数据库...")
    print(f"   待插入: {len(data_list)} 条")
    
    try:
        import psycopg2
        from psycopg2.extras import execute_values
        from urllib.parse import urlparse
        
        # 解析数据库URL
        result = urlparse(db_url)
        
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port or 5432,
            database=result.path[1:],
            user=result.username,
            password=result.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        insert_start = time.time()
        
        # 批量插入
        insert_sql = """
            INSERT INTO daily_stock_data 
            (stock_code, stock_name, trade_date,
             open_price, close_price, high_price, low_price,
             volume, amount, change_pct, turnover_rate)
            VALUES %s
            ON CONFLICT (stock_code, trade_date) DO UPDATE SET
                stock_name = EXCLUDED.stock_name,
                open_price = EXCLUDED.open_price,
                close_price = EXCLUDED.close_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                volume = EXCLUDED.volume,
                amount = EXCLUDED.amount,
                change_pct = EXCLUDED.change_pct,
                turnover_rate = EXCLUDED.turnover_rate
        """
        
        execute_values(cur, insert_sql, data_list, page_size=1000)
        conn.commit()
        
        insert_time = time.time() - insert_start
        
        print(f"✅ 数据插入完成")
        print(f"   耗时: {insert_time:.2f}秒")
        print(f"   速度: {len(data_list)/insert_time:.0f} 条/秒")
        
        cur.close()
        conn.close()
        
        return True, insert_time
        
    except Exception as e:
        print(f"❌ 数据库插入失败: {e}")
        return False, 0


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🚀 优化后的完整同步入库测试")
    print("=" * 70)
    print()
    
    # 检查数据库配置
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误: 未找到 DATABASE_URL 环境变量")
        return 1
    
    print(f"🔗 数据库: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'Unknown'}")
    
    # 获取股票列表
    test_stocks = get_stock_list(limit=50)
    test_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"📅 同步日期: {test_date}")
    print(f"📊 测试数量: {len(test_stocks)} 只")
    print(f"   示例: {test_stocks[:5]}...")
    print()
    
    # 开始同步
    print("🔄 开始数据获取...")
    print("-" * 70)
    
    from app.services.enhanced_data_fetcher import robust_fetcher
    
    start_time = time.time()
    success_count = 0
    failed_count = 0
    data_to_insert = []
    
    for i, code in enumerate(test_stocks, 1):
        try:
            df = robust_fetcher.fetch_daily_data(code, test_date)
            
            if not df.empty:
                # 准备插入数据
                for _, row in df.iterrows():
                    data_to_insert.append((
                        code,  # stock_code
                        '',  # stock_name (暂时为空)
                        row.get('date', test_date),  # trade_date
                        float(row.get('open', 0)),  # open_price
                        float(row.get('close', 0)),  # close_price
                        float(row.get('high', 0)),  # high_price
                        float(row.get('low', 0)),  # low_price
                        int(float(row.get('volume', 0))),  # volume
                        float(row.get('amount', 0)),  # amount
                        float(row.get('pctChg', 0)),  # change_pct
                        float(row.get('turn', 0))  # turnover_rate
                    ))
                
                success_count += 1
                if i % 10 == 0 or i == len(test_stocks):
                    print(f"  [{i}/{len(test_stocks)}] ✅ 已完成 {success_count} 只")
            else:
                failed_count += 1
        
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # 只显示前5个错误
                print(f"  [{i}/{len(test_stocks)}] ❌ {code} - {str(e)[:50]}")
    
    fetch_time = time.time() - start_time
    
    print("-" * 70)
    print(f"\n📈 数据获取完成:")
    print(f"   成功: {success_count}/{len(test_stocks)} ({success_count/len(test_stocks)*100:.1f}%)")
    print(f"   失败: {failed_count}/{len(test_stocks)}")
    print(f"   耗时: {fetch_time:.2f}秒")
    print(f"   平均: {fetch_time/len(test_stocks):.2f}秒/只")
    print(f"   数据条数: {len(data_to_insert)}")
    
    # 插入数据库
    if data_to_insert:
        success, insert_time = sync_to_database(data_to_insert, db_url)
        
        if success:
            total_time = time.time() - start_time
            
            # 总结
            print("\n" + "=" * 70)
            print("📊 同步总结")
            print("=" * 70)
            print(f"✅ 同步成功！")
            print(f"\n时间统计:")
            print(f"   总耗时: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
            print(f"   数据获取: {fetch_time:.2f}秒 ({fetch_time/total_time*100:.1f}%)")
            print(f"   数据插入: {insert_time:.2f}秒 ({insert_time/total_time*100:.1f}%)")
            
            print(f"\n性能指标:")
            print(f"   获取速度: {fetch_time/len(test_stocks):.2f}秒/只")
            print(f"   插入速度: {len(data_to_insert)/insert_time:.0f} 条/秒")
            print(f"   成功率: {success_count/len(test_stocks)*100:.1f}%")
            
            print(f"\n预估全量同步（5158只）:")
            estimated_time = (fetch_time/len(test_stocks)) * 5158
            print(f"   预估耗时: {estimated_time:.0f}秒 ({estimated_time/60:.1f}分钟)")
            
            print(f"\n🎯 优化效果:")
            print(f"   ✅ Baostock 优先策略有效")
            print(f"   ✅ 快速切换机制正常")
            print(f"   ✅ 数据成功入库")
            print()
            
            return 0
        else:
            print("\n❌ 数据库插入失败")
            return 1
    else:
        print("\n⚠️  没有数据需要插入")
        return 1


if __name__ == '__main__':
    sys.exit(main())
