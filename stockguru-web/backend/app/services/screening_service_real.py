"""
筛选服务 - 使用真实数据
"""
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# 内存存储（临时方案）
_tasks_store = {}
_results_store = {}


class ScreeningService:
    """筛选服务 - 真实数据版本"""
    
    def __init__(self):
        self.use_real_data = True  # 标记使用真实数据
    
    def _get_supabase(self):
        """延迟获取 Supabase 客户端"""
        try:
            from app.core.supabase import get_supabase_client
            return get_supabase_client()
        except Exception as e:
            logger.warning(f"Supabase 连接失败: {e}")
            return None
    
    async def create_screening_task(
        self,
        date: str,
        volume_top_n: int = 100,
        hot_top_n: int = 100
    ) -> Dict:
        """创建筛选任务"""
        try:
            task_id = str(uuid.uuid4())
            
            # 尝试保存到 Supabase
            supabase = self._get_supabase()
            if supabase:
                task_data = {
                    "id": task_id,
                    "date": date,
                    "status": "pending",
                    "params": {
                        "volume_top_n": volume_top_n,
                        "hot_top_n": hot_top_n
                    },
                    "progress": 0,
                    "created_at": datetime.now().isoformat()
                }
                try:
                    supabase.table("tasks").insert(task_data).execute()
                    logger.info(f"任务已保存到 Supabase: {task_id}")
                except Exception as e:
                    logger.warning(f"保存到 Supabase 失败: {e}")
            
            # 同时保存到内存
            _tasks_store[task_id] = {
                "id": task_id,
                "date": date,
                "status": "pending",
                "params": {"volume_top_n": volume_top_n, "hot_top_n": hot_top_n},
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "result_count": 0,
                "error_message": None
            }
            
            logger.info(f"任务创建成功: {task_id}")
            
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "任务已创建，正在后台处理"
            }
            
        except Exception as e:
            logger.error(f"创建任务失败: {str(e)}")
            raise
    
    async def _execute_screening(
        self,
        task_id: str,
        date: str,
        volume_top_n: int,
        hot_top_n: int
    ):
        """执行筛选逻辑 - 使用真实数据"""
        supabase = self._get_supabase()
        
        try:
            logger.info(f"开始执行真实数据筛选: task_id={task_id}, date={date}")
            
            # 更新状态
            _tasks_store[task_id]["status"] = "running"
            _tasks_store[task_id]["started_at"] = datetime.now().isoformat()
            _tasks_store[task_id]["progress"] = 10
            
            if supabase:
                try:
                    supabase.table("tasks").update({
                        "status": "running",
                        "progress": 10
                    }).eq("id", task_id).execute()
                except Exception as e:
                    logger.warning(f"更新 Supabase 失败: {e}")
            
            # 导入筛选模块
            from app.services.modules.data_fetcher import DataFetcher
            from app.services.modules.stock_filter import StockFilter
            from app.services.modules.momentum_calculator import MomentumCalculator
            
            data_fetcher = DataFetcher()
            stock_filter = StockFilter()
            momentum_calculator = MomentumCalculator()
            
            # 1. 获取成交额数据
            logger.info(f"获取成交额数据: {date}, top_n={volume_top_n}")
            volume_df = data_fetcher.get_volume_top_stocks(date, volume_top_n)
            _tasks_store[task_id]["progress"] = 30
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 30}).eq("id", task_id).execute()
                except: pass
            
            # 2. 获取热度数据
            logger.info(f"获取热度数据: {date}, top_n={hot_top_n}")
            hot_df = data_fetcher.get_hot_top_stocks(date, hot_top_n)
            _tasks_store[task_id]["progress"] = 50
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 50}).eq("id", task_id).execute()
                except: pass
            
            # 3. 筛选股票
            logger.info("筛选股票...")
            filtered_stocks = stock_filter.filter_and_rank_stocks(volume_df, hot_df, top_n=30)
            _tasks_store[task_id]["progress"] = 70
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 70}).eq("id", task_id).execute()
                except: pass
            
            # 4. 计算动量
            logger.info("计算动量分数...")
            stocks_with_momentum = momentum_calculator.calculate_momentum_scores(
                filtered_stocks,
                date,
                momentum_days=25
            )
            _tasks_store[task_id]["progress"] = 90
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 90}).eq("id", task_id).execute()
                except: pass
            
            # 5. 保存结果
            logger.info("保存结果...")
            results = []
            for idx, stock in enumerate(stocks_with_momentum[:30], 1):
                result_data = {
                    "task_id": task_id,
                    "stock_code": stock.get("code", ""),
                    "stock_name": stock.get("name", ""),
                    "momentum_score": float(stock.get("momentum_score", 0)),
                    "comprehensive_score": float(stock.get("comprehensive_score", 0)),
                    "volume_rank": int(stock.get("volume_rank", 0)),
                    "hot_rank": int(stock.get("hot_rank", 0)),
                    "final_rank": idx,
                    "close_price": float(stock.get("close", 0)),
                    "change_pct": float(stock.get("change_pct", 0)),
                    "volume": float(stock.get("volume", 0))
                }
                results.append(result_data)
            
            # 保存到内存
            _results_store[task_id] = results
            
            # 保存到 Supabase
            if supabase and results:
                try:
                    supabase.table("results").insert(results).execute()
                    logger.info(f"结果已保存到 Supabase: {len(results)} 条")
                except Exception as e:
                    logger.warning(f"保存结果到 Supabase 失败: {e}")
            
            # 6. 更新任务状态
            _tasks_store[task_id]["status"] = "completed"
            _tasks_store[task_id]["progress"] = 100
            _tasks_store[task_id]["result_count"] = len(results)
            _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
            
            if supabase:
                try:
                    supabase.table("tasks").update({
                        "status": "completed",
                        "progress": 100,
                        "result_count": len(results),
                        "completed_at": datetime.now().isoformat()
                    }).eq("id", task_id).execute()
                except: pass
            
            logger.info(f"筛选完成: {len(results)} 只股票")
            
        except Exception as e:
            logger.error(f"筛选失败: {str(e)}", exc_info=True)
            
            # 更新失败状态
            _tasks_store[task_id]["status"] = "failed"
            _tasks_store[task_id]["error_message"] = str(e)
            _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
            
            if supabase:
                try:
                    supabase.table("tasks").update({
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.now().isoformat()
                    }).eq("id", task_id).execute()
                except: pass
            
            raise
    
    async def get_task_result(self, task_id: str) -> Dict:
        """获取任务结果"""
        supabase = self._get_supabase()
        
        # 先从内存获取
        if task_id in _tasks_store:
            task = _tasks_store[task_id]
            results = _results_store.get(task_id, [])
            
            return {
                "task_id": task_id,
                "status": task["status"],
                "progress": task["progress"],
                "result_count": task.get("result_count"),
                "results": results,
                "error_message": task.get("error_message"),
                "created_at": task["created_at"],
                "completed_at": task.get("completed_at")
            }
        
        # 如果内存没有，尝试从 Supabase 获取
        if supabase:
            try:
                task_response = supabase.table("tasks").select("*").eq("id", task_id).execute()
                
                if task_response.data:
                    task = task_response.data[0]
                    results = []
                    
                    if task["status"] == "completed":
                        results_response = supabase.table("results").select("*").eq("task_id", task_id).order("final_rank").execute()
                        results = results_response.data
                    
                    return {
                        "task_id": task_id,
                        "status": task["status"],
                        "progress": task["progress"],
                        "result_count": task.get("result_count"),
                        "results": results,
                        "error_message": task.get("error_message"),
                        "created_at": task["created_at"],
                        "completed_at": task.get("completed_at")
                    }
            except Exception as e:
                logger.error(f"从 Supabase 获取任务失败: {e}")
        
        raise ValueError(f"任务不存在: {task_id}")
    
    async def list_tasks(self, limit: int = 10) -> List[Dict]:
        """获取任务列表"""
        supabase = self._get_supabase()
        
        # 先尝试从 Supabase 获取
        if supabase:
            try:
                response = supabase.table("tasks").select("*").order("created_at", desc=True).limit(limit).execute()
                return response.data
            except Exception as e:
                logger.error(f"从 Supabase 获取任务列表失败: {e}")
        
        # 否则从内存获取
        tasks = list(_tasks_store.values())
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return tasks[:limit]
