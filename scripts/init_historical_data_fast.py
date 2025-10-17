#!/usr/bin/env python3
"""
快速历史数据初始化脚本
优化策略：
1. 单会话复用（避免重复登录）
2. 智能批处理
3. 断点续传
4. 自动重试
"""

import os
import sys
import logging
from datetime import date, timedelta
import json
from pathlib import Path
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend'))

from app.services.daily_data_sync_service_neon import DailyDataSyncServiceNeon

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class FastHistoricalSync:
    """快速历史数据同步"""
    
    def __init__(self, checkpoint_file='sync_checkpoint.json'):
        self.sync_service = DailyDataSyncServiceNeon()
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint = self.load_checkpoint()
        self.start_time = None
        
        logger.info("✅ 使用进阶优化版本:")
        logger.info("  - COPY 命令批量插入 (快 2-3倍)")
        logger.info("  - 数据库参数优化")
        logger.info("  - 股票列表缓存")
    
    def load_checkpoint(self):
        """加载检查点"""
        if self.checkpoint_file.exists():
            return json.loads(self.checkpoint_file.read_text())
        return {
            'completed_dates': [],
            'failed_dates': [],
            'total_success': 0,
            'total_records': 0,
            'start_time': None
        }
    
    def save_checkpoint(self):
        """保存检查点"""
        self.checkpoint_file.write_text(
            json.dumps(self.checkpoint, indent=2, ensure_ascii=False)
        )
    
    def get_trading_days(self, days: int = 365):
        """
        获取交易日列表
        简化版：假设周一到周五都是交易日
        """
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        trading_days = []
        current = start_date
        
        while current <= end_date:
            # 简单判断：周一到周五
            if current.weekday() < 5:
                trading_days.append(current.isoformat())
            current += timedelta(days=1)
        
        return trading_days
    
    def sync_batch(self, dates: list):
        """
        批量同步多个日期
        使用单个 baostock 会话
        """
        total = len(dates)
        success_count = 0
        failed_count = 0
        
        for idx, date_str in enumerate(dates, 1):
            try:
                logger.info(f"[{idx}/{total}] 同步 {date_str}")
                
                result = self.sync_service.sync_daily_data(
                    date.fromisoformat(date_str)
                )
                
                if result['status'] == 'success':
                    self.checkpoint['completed_dates'].append(date_str)
                    self.checkpoint['total_success'] += result['success']
                    self.checkpoint['total_records'] += result.get('inserted', 0)
                    success_count += 1
                    
                    logger.info(
                        f"✅ {date_str} 完成: "
                        f"成功 {result['success']}, 失败 {result['failed']}, "
                        f"入库 {result.get('inserted', 0)}"
                    )
                elif result['status'] == 'skipped':
                    self.checkpoint['completed_dates'].append(date_str)
                    success_count += 1
                    logger.info(f"⏭️  {date_str} 跳过: {result['message']}")
                else:
                    self.checkpoint['failed_dates'].append(date_str)
                    failed_count += 1
                    logger.warning(f"⚠️ {date_str} 失败: {result.get('message', 'Unknown')}")
                
                # 每5个日期保存一次检查点
                if idx % 5 == 0:
                    self.save_checkpoint()
                    self.print_progress(idx, total, success_count, failed_count)
                
            except Exception as e:
                logger.error(f"❌ {date_str} 异常: {e}")
                self.checkpoint['failed_dates'].append(date_str)
                failed_count += 1
        
        return success_count, failed_count
    
    def print_progress(self, current, total, success, failed):
        """打印进度统计"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        elapsed_hours = elapsed / 3600
        
        if current > 0:
            avg_time_per_date = elapsed / current
            remaining = total - current
            eta_seconds = remaining * avg_time_per_date
            eta_hours = eta_seconds / 3600
            
            logger.info("="*60)
            logger.info(f"📊 进度统计")
            logger.info(f"已完成: {current}/{total} ({current/total*100:.1f}%)")
            logger.info(f"成功: {success}, 失败: {failed}")
            logger.info(f"已用时: {elapsed_hours:.1f} 小时")
            logger.info(f"预计剩余: {eta_hours:.1f} 小时")
            logger.info(f"总记录数: {self.checkpoint['total_records']:,}")
            logger.info(f"平均速度: {current/elapsed_hours:.1f} 日/小时")
            logger.info("="*60)
    
    def sync_historical(self, days: int = 365):
        """同步历史数据"""
        logger.info("="*60)
        logger.info(f"开始同步历史数据（最近 {days} 天）")
        logger.info("="*60)
        
        # 记录开始时间
        if not self.checkpoint.get('start_time'):
            self.checkpoint['start_time'] = time.time()
        self.start_time = self.checkpoint['start_time']
        
        # 获取交易日
        trading_days = self.get_trading_days(days)
        logger.info(f"预计交易日: {len(trading_days)} 天")
        
        # 过滤已完成的日期
        completed = set(self.checkpoint['completed_dates'])
        remaining = [d for d in trading_days if d not in completed]
        
        if completed:
            logger.info(f"已完成: {len(completed)} 天")
        logger.info(f"剩余: {len(remaining)} 天")
        
        if not remaining:
            logger.info("✅ 所有日期已同步完成！")
            return
        
        # 批量同步
        success, failed = self.sync_batch(remaining)
        
        # 最终保存
        self.save_checkpoint()
        
        # 最终统计
        total_elapsed = time.time() - self.start_time
        logger.info("="*60)
        logger.info("🎉 同步完成！")
        logger.info(f"成功: {success}")
        logger.info(f"失败: {failed}")
        logger.info(f"总记录数: {self.checkpoint['total_records']:,}")
        logger.info(f"总耗时: {total_elapsed/3600:.1f} 小时")
        logger.info("="*60)
        
        # 重试失败的日期
        if self.checkpoint['failed_dates']:
            logger.info(f"\n发现 {len(self.checkpoint['failed_dates'])} 个失败日期")
            logger.info(f"失败日期: {', '.join(self.checkpoint['failed_dates'][:10])}")
            if len(self.checkpoint['failed_dates']) > 10:
                logger.info(f"... 还有 {len(self.checkpoint['failed_dates']) - 10} 个")
            
            retry = input("\n是否重试失败的日期? (y/n): ")
            if retry.lower() == 'y':
                self.retry_failed_dates()
    
    def retry_failed_dates(self):
        """重试失败的日期"""
        failed = self.checkpoint['failed_dates'].copy()
        self.checkpoint['failed_dates'] = []
        
        logger.info(f"\n重试 {len(failed)} 个失败日期...")
        success, still_failed = self.sync_batch(failed)
        
        self.save_checkpoint()
        logger.info(f"重试完成: 成功 {success}, 仍失败 {still_failed}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='快速历史数据同步')
    parser.add_argument('--days', type=int, default=365, help='同步天数（默认365）')
    parser.add_argument('--checkpoint', type=str, default='sync_checkpoint.json', help='检查点文件')
    
    args = parser.parse_args()
    
    syncer = FastHistoricalSync(checkpoint_file=args.checkpoint)
    syncer.sync_historical(days=args.days)


if __name__ == '__main__':
    main()
