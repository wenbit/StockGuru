#!/usr/bin/env python3
"""
优化的历史数据初始化脚本
使用多日期并发 + PostgreSQL COPY
预计性能提升: 3-5倍
"""

import os
import sys
import logging
from datetime import date, timedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stockguru-web', 'backend'))

from app.services.daily_data_sync_service_neon import DailyDataSyncServiceNeon

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedHistoricalSync:
    """优化的历史数据同步"""
    
    def __init__(self, checkpoint_file='sync_checkpoint.json'):
        self.sync_service = DailyDataSyncServiceNeon()
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint = self.load_checkpoint()
    
    def load_checkpoint(self):
        """加载检查点"""
        if self.checkpoint_file.exists():
            return json.loads(self.checkpoint_file.read_text())
        return {
            'completed_dates': [],
            'failed_dates': [],
            'total_success': 0,
            'total_failed': 0
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
    
    def sync_single_date(self, date_str: str):
        """同步单个日期"""
        try:
            logger.info(f"开始同步 {date_str}")
            result = self.sync_service.sync_daily_data(
                date.fromisoformat(date_str)
            )
            
            if result['status'] == 'success':
                logger.info(
                    f"✅ {date_str} 完成: "
                    f"成功 {result['success']}, 失败 {result['failed']}"
                )
                return {
                    'date': date_str,
                    'status': 'success',
                    'success': result['success'],
                    'failed': result['failed']
                }
            else:
                logger.warning(f"⚠️ {date_str} {result['message']}")
                return {
                    'date': date_str,
                    'status': result['status'],
                    'message': result['message']
                }
        except Exception as e:
            logger.error(f"❌ {date_str} 失败: {e}")
            return {
                'date': date_str,
                'status': 'error',
                'error': str(e)
            }
    
    def sync_with_concurrency(
        self,
        days: int = 365,
        max_workers: int = 3
    ):
        """
        并发同步历史数据
        
        Args:
            days: 同步天数
            max_workers: 最大并发数（建议 2-4）
        """
        logger.info("="*60)
        logger.info(f"开始并发同步历史数据（最近 {days} 天）")
        logger.info(f"并发数: {max_workers}")
        logger.info("="*60)
        
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
            logger.info("所有日期已同步完成！")
            return
        
        # 并发同步
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures = {
                executor.submit(self.sync_single_date, date_str): date_str
                for date_str in remaining
            }
            
            # 处理结果
            completed_count = 0
            failed_count = 0
            
            for future in as_completed(futures):
                date_str = futures[future]
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        self.checkpoint['completed_dates'].append(date_str)
                        self.checkpoint['total_success'] += result.get('success', 0)
                        completed_count += 1
                    elif result['status'] == 'skipped':
                        self.checkpoint['completed_dates'].append(date_str)
                        completed_count += 1
                    else:
                        self.checkpoint['failed_dates'].append(date_str)
                        failed_count += 1
                    
                    # 定期保存检查点
                    if (completed_count + failed_count) % 5 == 0:
                        self.save_checkpoint()
                    
                    # 进度报告
                    total_processed = completed_count + failed_count
                    progress = total_processed / len(remaining) * 100
                    logger.info(
                        f"进度: {total_processed}/{len(remaining)} ({progress:.1f}%), "
                        f"成功: {completed_count}, 失败: {failed_count}"
                    )
                    
                except Exception as e:
                    logger.error(f"{date_str} 处理异常: {e}")
                    self.checkpoint['failed_dates'].append(date_str)
                    failed_count += 1
            
            # 最终保存
            self.save_checkpoint()
        
        # 统计
        logger.info("="*60)
        logger.info("同步完成！")
        logger.info(f"成功: {completed_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"总记录数: {self.checkpoint['total_success']}")
        logger.info("="*60)
        
        # 重试失败的日期
        if self.checkpoint['failed_dates']:
            logger.info(f"\n发现 {len(self.checkpoint['failed_dates'])} 个失败日期")
            retry = input("是否重试失败的日期? (y/n): ")
            if retry.lower() == 'y':
                self.retry_failed_dates()
    
    def retry_failed_dates(self):
        """重试失败的日期"""
        failed = self.checkpoint['failed_dates'].copy()
        self.checkpoint['failed_dates'] = []
        
        logger.info(f"重试 {len(failed)} 个失败日期...")
        
        for date_str in failed:
            result = self.sync_single_date(date_str)
            
            if result['status'] == 'success':
                self.checkpoint['completed_dates'].append(date_str)
                self.checkpoint['total_success'] += result.get('success', 0)
            else:
                self.checkpoint['failed_dates'].append(date_str)
        
        self.save_checkpoint()
        logger.info(f"重试完成，剩余失败: {len(self.checkpoint['failed_dates'])}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='优化的历史数据同步')
    parser.add_argument('--days', type=int, default=365, help='同步天数（默认365）')
    parser.add_argument('--workers', type=int, default=3, help='并发数（默认3）')
    parser.add_argument('--checkpoint', type=str, default='sync_checkpoint.json', help='检查点文件')
    
    args = parser.parse_args()
    
    syncer = OptimizedHistoricalSync(checkpoint_file=args.checkpoint)
    syncer.sync_with_concurrency(
        days=args.days,
        max_workers=args.workers
    )


if __name__ == '__main__':
    main()
