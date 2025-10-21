#!/usr/bin/env python3
"""
分析 2025-09-08 到 2025-09-10 的同步数据异常
"""

import os
import sys
import psycopg2

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def analyze_sync_issues():
    """分析同步问题"""
    
    db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 错误：未设置 NEON_DATABASE_URL 或 DATABASE_URL 环境变量")
        return
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("=" * 100)
    print("分析 2025-09-08 到 2025-09-10 的同步数据异常")
    print("=" * 100)
    
    # 1. 同步状态记录
    print("\n【1】同步状态记录:")
    print("-" * 100)
    cur.execute("""
        SELECT 
            sync_date,
            status,
            total_records,
            success_count,
            failed_count,
            EXTRACT(EPOCH FROM (end_time - start_time))::int as duration_sec,
            remarks
        FROM daily_sync_status
        WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-11'
        ORDER BY sync_date
    """)
    
    status_records = []
    for row in cur.fetchall():
        sync_date, status, total, success, failed, duration, remarks = row
        status_records.append((sync_date, total, success, failed))
        print(f"\n📅 {sync_date}  |  状态: {status}")
        print(f"   总数: {total}  |  成功: {success}  |  失败: {failed}  |  耗时: {duration}秒")
        print(f"   备注: {remarks}")
    
    # 2. 实际数据库数据量
    print("\n" + "=" * 100)
    print("【2】数据库实际数据量:")
    print("-" * 100)
    cur.execute("""
        SELECT 
            trade_date,
            COUNT(*) as total_records,
            COUNT(DISTINCT stock_code) as unique_stocks
        FROM daily_stock_data
        WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-11'
        GROUP BY trade_date
        ORDER BY trade_date
    """)
    
    db_records = {}
    for row in cur.fetchall():
        trade_date, count, unique = row
        db_records[str(trade_date)] = (count, unique)
        print(f"📊 {trade_date}:  {count:,} 条记录  |  {unique:,} 只股票")
    
    # 3. 对比分析
    print("\n" + "=" * 100)
    print("【3】数据对比分析:")
    print("-" * 100)
    for sync_date, total, success, failed in status_records:
        date_str = str(sync_date)
        if date_str in db_records:
            db_count, db_unique = db_records[date_str]
            print(f"\n📅 {sync_date}:")
            print(f"   同步记录: 总数={total}, 成功={success}, 失败={failed}")
            print(f"   数据库:   实际={db_count}, 股票数={db_unique}")
            
            # 分析差异
            if success != db_count:
                diff = db_count - success
                print(f"   ⚠️  差异: {diff:+d} 条 (数据库比成功数{'多' if diff > 0 else '少'} {abs(diff)} 条)")
            
            if failed > 0:
                fail_rate = failed / total * 100
                print(f"   ❌ 失败率: {fail_rate:.1f}%")
        else:
            print(f"\n📅 {sync_date}: 数据库中无数据")
    
    # 4. 检查数据质量
    print("\n" + "=" * 100)
    print("【4】数据质量检查:")
    print("-" * 100)
    for date in ['2025-09-08', '2025-09-09', '2025-09-10']:
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN close_price IS NULL OR close_price = 0 THEN 1 END) as bad_price,
                COUNT(CASE WHEN volume IS NULL THEN 1 END) as null_volume,
                MIN(close_price) as min_price,
                MAX(close_price) as max_price
            FROM daily_stock_data
            WHERE trade_date = %s
        """, (date,))
        
        result = cur.fetchone()
        if result and result[0] > 0:
            total, bad_price, null_vol, min_p, max_p = result
            print(f"\n📅 {date}:")
            print(f"   总记录: {total:,}")
            print(f"   异常价格: {bad_price} 条")
            print(f"   成交量为空: {null_vol} 条")
            if min_p and max_p:
                print(f"   价格范围: {min_p} ~ {max_p}")
    
    # 5. 检查重复同步
    print("\n" + "=" * 100)
    print("【5】检查是否有重复同步:")
    print("-" * 100)
    cur.execute("""
        SELECT 
            trade_date,
            stock_code,
            COUNT(*) as dup_count
        FROM daily_stock_data
        WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-10'
        GROUP BY trade_date, stock_code
        HAVING COUNT(*) > 1
        LIMIT 20
    """)
    
    duplicates = cur.fetchall()
    if duplicates:
        print(f"⚠️  发现 {len(duplicates)} 条重复数据:")
        for trade_date, stock_code, dup_count in duplicates:
            print(f"   {trade_date} - {stock_code}: {dup_count} 条")
    else:
        print("✅ 没有发现重复数据")
    
    # 6. 分析失败模式
    print("\n" + "=" * 100)
    print("【6】分析失败模式 - 查看同步进度表:")
    print("-" * 100)
    try:
        cur.execute("""
            SELECT 
                sync_date,
                COUNT(*) as total_stocks,
                COUNT(CASE WHEN synced = true THEN 1 END) as synced_count,
                COUNT(CASE WHEN synced = false THEN 1 END) as not_synced_count,
                COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count
            FROM sync_progress
            WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-10'
            GROUP BY sync_date
            ORDER BY sync_date
        """)
        
        progress_data = cur.fetchall()
        if progress_data:
            for row in progress_data:
                sync_date, total, synced, not_synced, errors = row
                print(f"\n📅 {sync_date}:")
                print(f"   总股票数: {total}")
                print(f"   已同步: {synced}")
                print(f"   未同步: {not_synced}")
                print(f"   有错误: {errors}")
                
                # 查看具体错误
                if errors > 0:
                    cur.execute("""
                        SELECT stock_code, error_message
                        FROM sync_progress
                        WHERE sync_date = %s AND error_message IS NOT NULL
                        LIMIT 10
                    """, (sync_date,))
                    
                    error_samples = cur.fetchall()
                    print(f"   错误示例:")
                    for stock_code, error_msg in error_samples:
                        print(f"      {stock_code}: {error_msg[:100]}")
        else:
            print("没有进度记录（可能使用了不同的同步方式）")
    except Exception as e:
        print(f"进度表查询失败: {e}")
    
    # 7. 总结分析
    print("\n" + "=" * 100)
    print("【7】问题总结:")
    print("-" * 100)
    
    issues = []
    for sync_date, total, success, failed in status_records:
        date_str = str(sync_date)
        if date_str in db_records:
            db_count, db_unique = db_records[date_str]
            
            # 检查各种异常情况
            if failed > total * 0.5:  # 失败率超过50%
                issues.append(f"❌ {sync_date}: 失败率过高 ({failed}/{total} = {failed/total*100:.1f}%)")
            
            if success != db_count:
                issues.append(f"⚠️  {sync_date}: 成功数({success})与数据库记录数({db_count})不符")
            
            if db_count < 4000:  # 正常应该有4000+只股票
                issues.append(f"⚠️  {sync_date}: 数据量偏少 ({db_count} < 4000)")
    
    if issues:
        print("\n发现以下问题:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ 未发现明显问题")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 100)
    print("✅ 分析完成")
    print("=" * 100)

if __name__ == '__main__':
    analyze_sync_issues()
