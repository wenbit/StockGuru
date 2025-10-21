# 数据同步问题修复计划

## 🎯 执行步骤

### 第一步：停止当前同步任务 ✋

当前有一个正在运行的批量同步任务（2025-09-08 到 2025-09-24），需要先停止：

```bash
# 方法1：重启后端服务
cd /Users/van/dev/source/claudecode_src/StockGuru
./scripts/start/stop-all.sh
# 等待几秒
./scripts/start/start-all.sh

# 方法2：如果有 PID 文件
kill $(cat logs/.backend.pid)
```

### 第二步：分析问题根源 🔍

已完成分析，核心问题：

1. **计数逻辑错误**
   - `success_count` 包含了已存在的数据
   - `failed_count` 可能重复计数
   - `total_records` 与实际插入数不符

2. **09-09 灾难性失败**
   - 99.7% 失败率（5354/5372）
   - 只有 18 条数据成功
   - 可能原因：网络问题、baostock 问题、代码bug

3. **09-10 部分失败**
   - 41.7% 失败率（2238/5373）
   - 数据量不足（3032 < 4000）

### 第三步：清理错误数据 🧹

```sql
-- 连接数据库
psql $NEON_DATABASE_URL

-- 1. 查看当前状态
SELECT sync_date, status, total_records, success_count, failed_count
FROM daily_sync_status
WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-11'
ORDER BY sync_date;

-- 2. 删除 09-09 和 09-10 的数据（准备重新同步）
DELETE FROM daily_stock_data 
WHERE trade_date IN ('2025-09-09', '2025-09-10');

-- 3. 重置同步状态
UPDATE daily_sync_status 
SET status = 'pending',
    total_records = 0,
    success_count = 0,
    failed_count = 0,
    start_time = NULL,
    end_time = NULL,
    duration_seconds = NULL,
    remarks = '待重新同步（已修复计数逻辑）',
    updated_at = NOW()
WHERE sync_date IN ('2025-09-09', '2025-09-10');

-- 4. 验证清理结果
SELECT trade_date, COUNT(*) 
FROM daily_stock_data 
WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-11'
GROUP BY trade_date;
```

### 第四步：修复代码 🔧

#### 关键修复点

**1. 修复计数逻辑**

需要区分：
- `fetch_success`: 成功从 baostock 获取数据的数量
- `fetch_failed`: 获取失败的数量  
- `insert_new`: 实际新插入数据库的数量
- `insert_skip`: 已存在跳过的数量

**2. 改进错误处理**

- 添加重试机制（最多 3 次）
- 详细记录每个失败的股票和原因
- 避免连锁失败

**3. 添加数据验证**

- 同步后验证数据量
- 检查失败率
- 自动告警异常情况

#### 代码修改建议

创建新的同步脚本 `scripts/fixed_sync.py`：

```python
#!/usr/bin/env python3
"""
修复后的数据同步脚本
- 准确的计数逻辑
- 完善的错误处理
- 详细的日志记录
"""

import os
import sys
import time
import logging
import baostock as bs
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta

# 配置日志
def setup_logging(sync_date):
    log_file = f'logs/sync_{sync_date}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class AccurateSyncService:
    """准确计数的同步服务"""
    
    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None
        self.logger = None
        
    def connect_db(self):
        """连接数据库"""
        self.conn = psycopg2.connect(self.db_url)
        
    def get_all_stocks(self):
        """获取所有A股代码"""
        lg = bs.login()
        rs = bs.query_stock_basic()
        stocks = []
        while rs.next():
            code = rs.get_row_data()[0]
            if code.startswith(('sh.6', 'sz.0', 'sz.3')):
                stocks.append(code)
        bs.logout()
        return stocks
    
    def fetch_stock_data(self, stock_code, sync_date, max_retries=3):
        """获取单只股票数据（带重试）"""
        for attempt in range(max_retries):
            try:
                rs = bs.query_history_k_data_plus(
                    stock_code,
                    "date,code,open,high,low,close,preclose,volume,amount,"
                    "adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                    start_date=sync_date,
                    end_date=sync_date,
                    frequency="d",
                    adjustflag="3"
                )
                
                if rs.error_code == '0':
                    data_list = []
                    while rs.next():
                        data_list.append(rs.get_row_data())
                    return data_list if data_list else None
                else:
                    self.logger.warning(
                        f"{stock_code}: baostock error {rs.error_code} "
                        f"(attempt {attempt+1}/{max_retries})"
                    )
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    self.logger.error(f"{stock_code}: {str(e)}")
                    return None
        
        return None
    
    def insert_data(self, data_list, sync_date):
        """插入数据并返回实际插入的数量"""
        if not data_list:
            return 0
        
        cur = self.conn.cursor()
        
        # 准备数据
        values = []
        for row in data_list:
            # 解析数据
            trade_date = row[0]
            stock_code = row[1].replace('sh.', '').replace('sz.', '')
            
            # 转换数值
            def safe_float(val):
                try:
                    return float(val) if val else None
                except:
                    return None
            
            values.append((
                stock_code,
                '',  # stock_name 稍后更新
                trade_date,
                safe_float(row[2]),  # open
                safe_float(row[4]),  # close
                safe_float(row[3]),  # high
                safe_float(row[4]),  # low
                safe_float(row[6]),  # volume
                safe_float(row[7]),  # amount
                safe_float(row[11]), # change_pct
                None,  # change_amount
                safe_float(row[9]),  # turnover_rate
                None   # amplitude
            ))
        
        # 插入数据
        insert_sql = """
            INSERT INTO daily_stock_data (
                stock_code, stock_name, trade_date,
                open_price, close_price, high_price, low_price,
                volume, amount, change_pct, change_amount,
                turnover_rate, amplitude
            ) VALUES %s
            ON CONFLICT (stock_code, trade_date) DO NOTHING
        """
        
        # 执行插入
        execute_values(cur, insert_sql, values)
        inserted = cur.rowcount
        self.conn.commit()
        
        return inserted
    
    def sync_date(self, sync_date):
        """同步指定日期的数据"""
        self.logger = setup_logging(sync_date)
        self.logger.info(f"=" * 80)
        self.logger.info(f"开始同步 {sync_date}")
        self.logger.info(f"=" * 80)
        
        # 连接数据库
        self.connect_db()
        bs.login()
        
        # 初始化统计
        stats = {
            'total_stocks': 0,
            'fetch_success': 0,
            'fetch_failed': 0,
            'insert_new': 0,
            'insert_skip': 0,
            'errors': []
        }
        
        # 获取所有股票
        stocks = self.get_all_stocks()
        stats['total_stocks'] = len(stocks)
        self.logger.info(f"总股票数: {stats['total_stocks']}")
        
        # 更新同步状态为 syncing
        self.update_sync_status(
            sync_date, 'syncing', stats['total_stocks'], 0, 0,
            f'开始同步: 总计{stats['total_stocks']}只股票'
        )
        
        start_time = time.time()
        
        # 逐个同步
        for i, stock in enumerate(stocks, 1):
            try:
                # 获取数据
                data = self.fetch_stock_data(stock, sync_date)
                
                if data is None:
                    stats['fetch_failed'] += 1
                    stats['errors'].append((stock, '无数据'))
                    continue
                
                stats['fetch_success'] += 1
                
                # 插入数据
                inserted = self.insert_data(data, sync_date)
                
                if inserted > 0:
                    stats['insert_new'] += inserted
                else:
                    stats['insert_skip'] += 1
                
                # 每100只股票显示一次进度
                if i % 100 == 0:
                    progress = i / stats['total_stocks'] * 100
                    elapsed = time.time() - start_time
                    speed = i / elapsed
                    eta = (stats['total_stocks'] - i) / speed if speed > 0 else 0
                    
                    self.logger.info(
                        f"进度: {i}/{stats['total_stocks']} ({progress:.1f}%) | "
                        f"成功: {stats['fetch_success']} | "
                        f"失败: {stats['fetch_failed']} | "
                        f"速度: {speed:.1f}股/秒 | "
                        f"预计剩余: {eta/60:.1f}分钟"
                    )
                    
                    # 更新同步状态
                    self.update_sync_status(
                        sync_date, 'syncing', 
                        stats['total_stocks'],
                        stats['insert_new'],
                        stats['fetch_failed'],
                        f"同步中: {i}/{stats['total_stocks']}, "
                        f"成功{stats['insert_new']}, 失败{stats['fetch_failed']}"
                    )
                
            except Exception as e:
                stats['fetch_failed'] += 1
                stats['errors'].append((stock, str(e)))
                self.logger.error(f"{stock}: {str(e)}")
        
        # 同步完成
        duration = time.time() - start_time
        
        # 验证数据
        actual_count = self.get_db_count(sync_date)
        
        # 判断最终状态
        final_status = 'success' if stats['fetch_failed'] == 0 else 'failed'
        
        # 更新最终状态
        self.update_sync_status(
            sync_date,
            final_status,
            stats['total_stocks'],
            stats['insert_new'],  # 使用实际插入数
            stats['fetch_failed'],
            f"同步完成: 获取成功{stats['fetch_success']}, 失败{stats['fetch_failed']}, "
            f"新插入{stats['insert_new']}, 已存在{stats['insert_skip']}, "
            f"数据库实际{actual_count}条, 耗时{duration/60:.1f}分钟"
        )
        
        # 记录详细统计
        self.logger.info(f"\n" + "=" * 80)
        self.logger.info(f"同步完成统计:")
        self.logger.info(f"  总股票数: {stats['total_stocks']}")
        self.logger.info(f"  获取成功: {stats['fetch_success']}")
        self.logger.info(f"  获取失败: {stats['fetch_failed']}")
        self.logger.info(f"  新插入: {stats['insert_new']}")
        self.logger.info(f"  已存在: {stats['insert_skip']}")
        self.logger.info(f"  数据库实际: {actual_count}")
        self.logger.info(f"  耗时: {duration/60:.1f} 分钟")
        self.logger.info(f"=" * 80)
        
        # 记录失败的股票
        if stats['errors']:
            self.logger.warning(f"\n失败的股票 ({len(stats['errors'])} 只):")
            for stock, error in stats['errors'][:20]:  # 只显示前20个
                self.logger.warning(f"  {stock}: {error}")
        
        bs.logout()
        self.conn.close()
        
        return stats
    
    def get_db_count(self, sync_date):
        """获取数据库中实际的记录数"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM daily_stock_data WHERE trade_date = %s",
            (sync_date,)
        )
        return cur.fetchone()[0]
    
    def update_sync_status(self, sync_date, status, total, success, failed, remarks):
        """更新同步状态"""
        cur = self.conn.cursor()
        
        if status == 'syncing':
            # 更新进行中的状态
            cur.execute("""
                UPDATE daily_sync_status
                SET status = %s,
                    total_records = %s,
                    success_count = %s,
                    failed_count = %s,
                    remarks = %s,
                    updated_at = NOW()
                WHERE sync_date = %s
            """, (status, total, success, failed, remarks, sync_date))
        else:
            # 更新最终状态
            cur.execute("""
                UPDATE daily_sync_status
                SET status = %s,
                    total_records = %s,
                    success_count = %s,
                    failed_count = %s,
                    end_time = NOW(),
                    duration_seconds = EXTRACT(EPOCH FROM (NOW() - start_time))::int,
                    remarks = %s,
                    updated_at = NOW()
                WHERE sync_date = %s
            """, (status, total, success, failed, remarks, sync_date))
        
        self.conn.commit()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python fixed_sync.py <日期>")
        print("示例: python fixed_sync.py 2025-09-09")
        sys.exit(1)
    
    sync_date = sys.argv[1]
    db_url = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
    
    if not db_url:
        print("错误：未设置数据库连接URL")
        sys.exit(1)
    
    service = AccurateSyncService(db_url)
    stats = service.sync_date(sync_date)
    
    print(f"\n✅ 同步完成！")
    print(f"   成功: {stats['insert_new']}")
    print(f"   失败: {stats['fetch_failed']}")
```

### 第五步：重新同步 🔄

```bash
# 1. 设置环境变量
source stockguru-web/backend/.env

# 2. 同步 09-09
python scripts/fixed_sync.py 2025-09-09

# 3. 同步 09-10
python scripts/fixed_sync.py 2025-09-10

# 4. 验证结果
python scripts/analyze_sync_issue.py
```

### 第六步：验证结果 ✅

```sql
-- 1. 检查数据量
SELECT 
    trade_date,
    COUNT(*) as records,
    COUNT(DISTINCT stock_code) as stocks
FROM daily_stock_data
WHERE trade_date BETWEEN '2025-09-08' AND '2025-09-10'
GROUP BY trade_date
ORDER BY trade_date;

-- 预期结果：
-- 2025-09-08: ~5200 条
-- 2025-09-09: ~5200 条
-- 2025-09-10: ~5200 条

-- 2. 检查同步状态
SELECT 
    sync_date,
    status,
    total_records,
    success_count,
    failed_count,
    remarks
FROM daily_sync_status
WHERE sync_date BETWEEN '2025-09-08' AND '2025-09-10'
ORDER BY sync_date;

-- 预期：
-- 状态都是 success
-- success_count 与数据库记录数一致
-- failed_count < 100
```

## 📊 成功标准

- ✅ 每天数据量 > 4000 条
- ✅ 失败率 < 5%
- ✅ success_count 与数据库记录数一致（误差 < 10）
- ✅ 没有重复数据
- ✅ 数据质量正常（无异常价格）

## 🚨 注意事项

1. **备份数据**：在清理前备份重要数据
2. **逐步执行**：不要一次性同步太多天
3. **监控日志**：密切关注同步日志
4. **验证结果**：每次同步后都要验证

## 📝 后续改进

1. **添加自动告警**：失败率超过阈值时发送通知
2. **改进重试策略**：指数退避重试
3. **优化性能**：并发获取数据
4. **完善监控**：实时监控同步健康度
