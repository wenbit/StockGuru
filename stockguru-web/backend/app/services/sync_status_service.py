"""
每日同步状态管理服务
用于管理和追踪每日数据同步任务的状态
"""

import os
import logging
import psutil
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, List
from app.core.database import DatabaseConnection

logger = logging.getLogger(__name__)

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class SyncStatusService:
    """同步状态管理服务"""
    
    @staticmethod
    def create_or_update_status(
        sync_date: date,
        status: str,
        total_records: int = 0,
        success_count: int = 0,
        failed_count: int = 0,
        error_message: str = None,
        remarks: str = None,
        process_id: str = None
    ) -> Dict:
        """
        创建或更新同步状态
        
        Args:
            sync_date: 同步日期
            status: 状态 (pending/syncing/success/failed/skipped)
            total_records: 总条数
            success_count: 成功条数
            failed_count: 失败条数
            error_message: 错误信息
            remarks: 备注
            process_id: 进程ID
        """
        try:
            with DatabaseConnection() as cursor:
                # 检查是否存在
                cursor.execute(
                    "SELECT id FROM daily_sync_status WHERE sync_date = %s",
                    (sync_date,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 更新
                    update_fields = []
                    params = []
                    
                    update_fields.append("status = %s")
                    params.append(status)
                    
                    if total_records > 0:
                        update_fields.append("total_records = %s")
                        params.append(total_records)
                    
                    if success_count > 0:
                        update_fields.append("success_count = %s")
                        params.append(success_count)
                    
                    if failed_count > 0:
                        update_fields.append("failed_count = %s")
                        params.append(failed_count)
                    
                    if error_message:
                        update_fields.append("error_message = %s")
                        params.append(error_message)
                    
                    if remarks:
                        update_fields.append("remarks = %s")
                        params.append(remarks)
                    
                    if process_id:
                        update_fields.append("process_id = %s")
                        params.append(process_id)
                    
                    # 根据状态更新时间（使用北京时间，转换为字符串格式）
                    beijing_now = datetime.now(BEIJING_TZ)
                    beijing_now_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
                    if status == 'syncing':
                        update_fields.append("start_time = %s::timestamp")
                        params.append(beijing_now_str)
                    elif status in ['success', 'failed', 'skipped']:
                        update_fields.append("end_time = %s::timestamp")
                        params.append(beijing_now_str)
                        update_fields.append("duration_seconds = EXTRACT(EPOCH FROM (%s::timestamp - start_time))")
                        params.append(beijing_now_str)
                    
                    params.append(sync_date)
                    
                    sql = f"""
                        UPDATE daily_sync_status 
                        SET {', '.join(update_fields)}
                        WHERE sync_date = %s
                        RETURNING *
                    """
                    cursor.execute(sql, params)
                else:
                    # 创建（使用北京时间，转换为字符串格式）
                    beijing_now = datetime.now(BEIJING_TZ)
                    start_time_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S') if status == 'syncing' else None
                    
                    cursor.execute("""
                        INSERT INTO daily_sync_status 
                        (sync_date, status, total_records, success_count, failed_count, 
                         error_message, remarks, process_id, start_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::timestamp)
                        RETURNING *
                    """, (
                        sync_date, status, total_records, success_count, failed_count,
                        error_message, remarks, process_id, start_time_str
                    ))
                
                result = cursor.fetchone()
                logger.info(f"同步状态已更新: {sync_date} -> {status}")
                # 返回记录ID
                return result['id'] if result else None
                
        except Exception as e:
            logger.error(f"更新同步状态失败: {e}", exc_info=True)
            raise
    
    @staticmethod
    def update_status(
        record_id: int,
        status: str = None,
        total_records: int = None,
        success_count: int = None,
        failed_count: int = None,
        duration_seconds: int = None,
        error_message: str = None,
        remarks: str = None
    ) -> bool:
        """
        通过ID更新同步状态记录
        
        Args:
            record_id: 记录ID
            status: 状态
            total_records: 总记录数
            success_count: 成功数
            failed_count: 失败数
            duration_seconds: 耗时（秒）
            error_message: 错误信息
            remarks: 备注
        
        Returns:
            是否更新成功
        """
        try:
            with DatabaseConnection() as cursor:
                update_fields = []
                params = []
                
                if status:
                    update_fields.append("status = %s")
                    params.append(status)
                    
                    # 根据状态更新时间（使用北京时间）
                    beijing_now = datetime.now(BEIJING_TZ)
                    beijing_now_str = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
                    if status == 'syncing' and not update_fields.__contains__("start_time"):
                        update_fields.append("start_time = %s::timestamp")
                        params.append(beijing_now_str)
                    elif status in ['success', 'failed', 'skipped']:
                        update_fields.append("end_time = %s::timestamp")
                        params.append(beijing_now_str)
                
                if total_records is not None:
                    update_fields.append("total_records = %s")
                    params.append(total_records)
                
                if success_count is not None:
                    update_fields.append("success_count = %s")
                    params.append(success_count)
                
                if failed_count is not None:
                    update_fields.append("failed_count = %s")
                    params.append(failed_count)
                
                if duration_seconds is not None:
                    update_fields.append("duration_seconds = %s")
                    params.append(duration_seconds)
                
                if error_message is not None:
                    update_fields.append("error_message = %s")
                    params.append(error_message)
                
                if remarks is not None:
                    update_fields.append("remarks = %s")
                    params.append(remarks)
                
                if not update_fields:
                    logger.warning(f"没有需要更新的字段，记录ID: {record_id}")
                    return False
                
                params.append(record_id)
                
                sql = f"""
                    UPDATE daily_sync_status 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                cursor.execute(sql, params)
                
                logger.debug(f"已更新同步状态记录，ID: {record_id}")
                return True
                
        except Exception as e:
            logger.error(f"更新同步状态记录失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_status(sync_date: date) -> Optional[Dict]:
        """获取指定日期的同步状态"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute(
                    "SELECT * FROM daily_sync_status WHERE sync_date = %s",
                    (sync_date,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"获取同步状态失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_recent_status(days: int = 30) -> List[Dict]:
        """获取最近N天的同步状态"""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    SELECT * FROM daily_sync_status 
                    WHERE sync_date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY sync_date DESC
                """, (days,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取最近同步状态失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def check_need_sync(sync_date: date) -> tuple[bool, str]:
        """
        检查指定日期是否需要同步
        
        Returns:
            (需要同步, 原因)
        """
        try:
            status = SyncStatusService.get_status(sync_date)
            
            if not status:
                return True, "未找到同步记录，需要同步"
            
            current_status = status['status']
            
            # 待同步状态
            if current_status == 'pending':
                return True, "状态为待同步"
            
            # 同步失败状态
            if current_status == 'failed':
                return True, "上次同步失败，需要重新同步"
            
            # 同步中状态 - 检查进程是否还在运行
            if current_status == 'syncing':
                process_id = status.get('process_id')
                if process_id:
                    # 检查进程是否存在
                    if SyncStatusService.is_process_running(process_id):
                        return False, f"同步进程 {process_id} 正在运行中"
                    else:
                        return True, f"同步进程 {process_id} 已停止，需要重新同步"
                else:
                    return True, "同步中但无进程ID，需要重新同步"
            
            # 已成功或跳过
            if current_status in ['success', 'skipped']:
                return False, f"状态为 {current_status}，无需同步"
            
            return True, f"未知状态 {current_status}，建议同步"
            
        except Exception as e:
            logger.error(f"检查同步需求失败: {e}", exc_info=True)
            return True, f"检查失败: {str(e)}"
    
    @staticmethod
    def is_process_running(process_id: str) -> bool:
        """检查进程是否在运行"""
        try:
            pid = int(process_id)
            return psutil.pid_exists(pid)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_pending_dates(days_back: int = 30) -> List[date]:
        """
        获取需要同步的日期列表
        
        Args:
            days_back: 向前查找多少天
            
        Returns:
            需要同步的日期列表
        """
        try:
            pending_dates = []
            today = date.today()
            
            for i in range(days_back):
                check_date = today - timedelta(days=i)
                need_sync, reason = SyncStatusService.check_need_sync(check_date)
                
                if need_sync:
                    pending_dates.append(check_date)
                    logger.info(f"{check_date}: 需要同步 - {reason}")
            
            return pending_dates
            
        except Exception as e:
            logger.error(f"获取待同步日期失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def mark_as_pending(sync_date: date, remarks: str = None):
        """标记为待同步"""
        return SyncStatusService.create_or_update_status(
            sync_date=sync_date,
            status='pending',
            remarks=remarks
        )
    
    @staticmethod
    def mark_as_syncing(sync_date: date, process_id: str = None):
        """标记为同步中"""
        if not process_id:
            process_id = str(os.getpid())
        
        return SyncStatusService.create_or_update_status(
            sync_date=sync_date,
            status='syncing',
            process_id=process_id
        )
    
    @staticmethod
    def mark_as_success(
        sync_date: date,
        total_records: int,
        success_count: int = None,
        remarks: str = None
    ):
        """标记为同步成功"""
        if success_count is None:
            success_count = total_records
        
        return SyncStatusService.create_or_update_status(
            sync_date=sync_date,
            status='success',
            total_records=total_records,
            success_count=success_count,
            remarks=remarks
        )
    
    @staticmethod
    def mark_as_failed(
        sync_date: date,
        error_message: str,
        total_records: int = 0,
        success_count: int = 0,
        failed_count: int = 0
    ):
        """标记为同步失败"""
        return SyncStatusService.create_or_update_status(
            sync_date=sync_date,
            status='failed',
            total_records=total_records,
            success_count=success_count,
            failed_count=failed_count,
            error_message=error_message
        )
    
    @staticmethod
    def mark_as_skipped(sync_date: date, remarks: str):
        """标记为跳过（非交易日等）"""
        return SyncStatusService.create_or_update_status(
            sync_date=sync_date,
            status='skipped',
            remarks=remarks
        )
    
    @staticmethod
    def get_sync_list(
        page: int = 1,
        page_size: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> tuple:
        """
        分页查询同步记录
        
        Returns:
            (records, total, stats): 记录列表、总数和统计信息
        """
        try:
            with DatabaseConnection(dict_cursor=False) as cursor:
                # 构建查询条件
                where_clauses = []
                params = []
                
                if start_date:
                    where_clauses.append("sync_date >= %s")
                    params.append(start_date)
                
                if end_date:
                    where_clauses.append("sync_date <= %s")
                    params.append(end_date)
                
                if status:
                    where_clauses.append("status = %s")
                    params.append(status)
                
                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                # 查询总数和统计
                cursor.execute(
                    f"""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'syncing' THEN 1 ELSE 0 END) as syncing,
                        SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
                    FROM daily_sync_status 
                    WHERE {where_sql}
                    """,
                    params
                )
                stats_row = cursor.fetchone()
                total = stats_row[0]
                stats = {
                    'total': total,
                    'success': stats_row[1] or 0,
                    'failed': stats_row[2] or 0,
                    'syncing': stats_row[3] or 0,
                    'skipped': stats_row[4] or 0
                }
                
                # 查询记录
                offset = (page - 1) * page_size
                cursor.execute(
                    f"""
                    SELECT 
                        id, sync_date, status, total_records, success_count, failed_count,
                        start_time, end_time, duration_seconds, error_message, remarks,
                        process_id, created_at, updated_at
                    FROM daily_sync_status
                    WHERE {where_sql}
                    ORDER BY sync_date DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [page_size, offset]
                )
                
                columns = [desc[0] for desc in cursor.description]
                records = []
                for row in cursor.fetchall():
                    record = dict(zip(columns, row))
                    # 转换日期时间为字符串
                    for key in ['sync_date', 'start_time', 'end_time', 'created_at', 'updated_at']:
                        if record.get(key):
                            record[key] = record[key].isoformat() if hasattr(record[key], 'isoformat') else str(record[key])
                    records.append(record)
                
                return records, total, stats
        except Exception as e:
            logger.error(f"查询同步列表失败: {e}", exc_info=True)
            raise


# 全局实例
_sync_status_service = None

def get_sync_status_service() -> SyncStatusService:
    """获取同步状态服务实例"""
    global _sync_status_service
    if _sync_status_service is None:
        _sync_status_service = SyncStatusService()
    return _sync_status_service
