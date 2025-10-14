"""
筛选服务 - 整合现有的筛选逻辑
"""
import uuid
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# 内存存储（临时方案，替代 Supabase）
_tasks_store = {}
_results_store = {}


class ScreeningService:
    """筛选服务"""
    
    def __init__(self):
        pass
    
    async def create_screening_task(
        self,
        date: str,
        volume_top_n: int = 100,
        hot_top_n: int = 100
    ) -> Dict:
        """创建筛选任务"""
        try:
            # 1. 创建任务记录
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "date": date,
                "status": "pending",
                "params": {
                    "volume_top_n": volume_top_n,
                    "hot_top_n": hot_top_n
                },
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "started_at": None,
                "completed_at": None,
                "result_count": 0,
                "error_message": None
            }
            
            # 保存到内存
            _tasks_store[task_id] = task_data
            
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
        """执行筛选逻辑（模拟版本）"""
        try:
            logger.info(f"开始执行筛选: task_id={task_id}")
            
            # 更新状态为运行中
            _tasks_store[task_id]["status"] = "running"
            _tasks_store[task_id]["started_at"] = datetime.now().isoformat()
            _tasks_store[task_id]["progress"] = 10
            
            # 模拟数据获取过程
            await asyncio.sleep(2)
            _tasks_store[task_id]["progress"] = 30
            logger.info(f"获取成交量数据完成")
            
            await asyncio.sleep(2)
            _tasks_store[task_id]["progress"] = 50
            logger.info(f"获取热度数据完成")
            
            await asyncio.sleep(2)
            _tasks_store[task_id]["progress"] = 70
            logger.info(f"筛选股票完成")
            
            await asyncio.sleep(2)
            _tasks_store[task_id]["progress"] = 90
            logger.info(f"计算动量分数完成")
            
            # 生成模拟结果
            results = self._generate_mock_results(task_id, 30)
            _results_store[task_id] = results
            
            # 更新任务状态为完成
            _tasks_store[task_id]["status"] = "completed"
            _tasks_store[task_id]["progress"] = 100
            _tasks_store[task_id]["result_count"] = len(results)
            _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"筛选完成: {len(results)} 只股票")
            
        except Exception as e:
            logger.error(f"筛选失败: {str(e)}")
            
            # 更新任务状态为失败
            _tasks_store[task_id]["status"] = "failed"
            _tasks_store[task_id]["error_message"] = str(e)
            _tasks_store[task_id]["completed_at"] = datetime.now().isoformat()
    
    def _generate_mock_results(self, task_id: str, count: int) -> List[Dict]:
        """生成模拟结果"""
        stock_names = [
            "贵州茅台", "宁德时代", "比亚迪", "隆基绿能", "中国平安",
            "招商银行", "五粮液", "美的集团", "格力电器", "海天味业",
            "立讯精密", "东方财富", "万科A", "保利发展", "中信证券",
            "兴业银行", "浦发银行", "中国石油", "中国石化", "中国神华",
            "紫金矿业", "海螺水泥", "长江电力", "中国建筑", "中国中车",
            "三一重工", "中联重科", "徐工机械", "潍柴动力", "上汽集团"
        ]
        
        results = []
        for i in range(count):
            stock_code = f"{600000 + i:06d}"
            results.append({
                "task_id": task_id,
                "stock_code": stock_code,
                "stock_name": stock_names[i] if i < len(stock_names) else f"股票{i+1}",
                "momentum_score": round(random.uniform(70, 95), 2),
                "comprehensive_score": round(random.uniform(75, 98), 2),
                "volume_rank": i + 1,
                "hot_rank": random.randint(1, 100),
                "final_rank": i + 1,
                "close_price": round(random.uniform(10, 300), 2),
                "change_pct": round(random.uniform(-5, 10), 2),
                "volume": random.randint(100000000, 1000000000)
            })
        
        return results
    
    async def get_task_result(self, task_id: str) -> Dict:
        """获取任务结果"""
        try:
            # 从内存获取任务信息
            if task_id not in _tasks_store:
                raise ValueError(f"任务不存在: {task_id}")
            
            task = _tasks_store[task_id]
            
            # 如果任务完成，获取结果
            results = []
            if task["status"] == "completed" and task_id in _results_store:
                results = _results_store[task_id]
            
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
            logger.error(f"获取任务结果失败: {str(e)}")
            raise
    
    async def list_tasks(self, limit: int = 10) -> List[Dict]:
        """获取任务列表"""
        try:
            tasks = list(_tasks_store.values())
            # 按创建时间倒序排序
            tasks.sort(key=lambda x: x["created_at"], reverse=True)
            return tasks[:limit]
        except Exception as e:
            logger.error(f"获取任务列表失败: {str(e)}")
            raise
