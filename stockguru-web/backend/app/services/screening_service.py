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
            # 检查缓存（对于历史日期）
            from app.services.cache_service import get_cache_service
            cache_service = get_cache_service()
            
            cache_params = {
                'date': date,
                'volume_top_n': volume_top_n,
                'hot_top_n': hot_top_n
            }
            cached_result = cache_service.get('screening', cache_params)
            
            if cached_result:
                logger.info(f"使用缓存的筛选结果: {date}")
                task_id = cached_result['task_id']
                
                # 恢复到内存
                _tasks_store[task_id] = cached_result['task']
                _results_store[task_id] = cached_result['results']
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "message": "使用缓存结果"
                }
            
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
            from app.core.config import settings
            
            data_fetcher = DataFetcher()
            stock_filter = StockFilter(config=settings)
            momentum_calculator = MomentumCalculator(config=settings)
            
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
            filtered_df = stock_filter.calculate_comprehensive_score(volume_df, hot_df)
            _tasks_store[task_id]["progress"] = 70
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 70}).eq("id", task_id).execute()
                except: pass
            
            # 4. 计算动量
            logger.info("计算动量分数...")
            
            # 并发获取K线数据
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            import time
            
            def fetch_kline_with_timeout(code, days=25, timeout=5):
                """带超时的K线数据获取"""
                try:
                    start_time = time.time()
                    kline_df = data_fetcher.get_stock_daily_data(code, days=days)
                    elapsed = time.time() - start_time
                    
                    if elapsed > timeout:
                        logger.warning(f"股票 {code} K线数据获取超时 ({elapsed:.2f}s)")
                        return code, None
                    
                    if not kline_df.empty:
                        return code, kline_df
                    return code, None
                except Exception as e:
                    logger.warning(f"获取股票 {code} K线数据失败: {e}")
                    return code, None
            
            # 使用线程池并发获取（最多10个并发）
            stock_codes = [str(row['code']) for _, row in filtered_df.iterrows()]
            stock_data_dict = {}
            
            logger.info(f"开始并发获取 {len(stock_codes)} 只股票的K线数据...")
            _tasks_store[task_id]["progress"] = 75
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(fetch_kline_with_timeout, code) for code in stock_codes]
                completed = 0
                for future in futures:
                    try:
                        code, kline_df = future.result(timeout=10)
                        if kline_df is not None:
                            stock_data_dict[code] = kline_df
                        completed += 1
                        
                        # 更新进度 (75% -> 85%)
                        progress = 75 + int((completed / len(stock_codes)) * 10)
                        _tasks_store[task_id]["progress"] = progress
                    except Exception as e:
                        logger.warning(f"处理K线数据失败: {e}")
                        completed += 1
            
            logger.info(f"成功获取 {len(stock_data_dict)}/{len(stock_codes)} 只股票的K线数据")
            _tasks_store[task_id]["progress"] = 85
            
            # 批量计算动量
            if stock_data_dict:
                filtered_df = momentum_calculator.batch_calculate(filtered_df, stock_data_dict)
            else:
                # 如果没有K线数据，使用综合评分作为备选
                logger.warning("未获取到K线数据，使用综合评分作为动量分数")
                filtered_df['momentum_score'] = filtered_df['comprehensive_score'] * 100
            
            # 按动量分数排序
            filtered_df = filtered_df.sort_values('momentum_score', ascending=False)
            
            # 将 DataFrame 转换为字典列表
            stocks_with_momentum = filtered_df.to_dict('records')
            _tasks_store[task_id]["progress"] = 90
            
            if supabase:
                try:
                    supabase.table("tasks").update({"progress": 90}).eq("id", task_id).execute()
                except: pass
            
            # 5. 保存结果
            logger.info("保存结果...")
            results = []
            for idx, stock in enumerate(stocks_with_momentum[:30], 1):
                # 尝试多个可能的字段名
                close_price = (
                    stock.get("最新价", 0) or 
                    stock.get("close", 0) or 
                    stock.get("收盘价", 0) or 
                    0
                )
                change_pct = (
                    stock.get("最新涨跌幅", 0) or 
                    stock.get("change_pct", 0) or 
                    stock.get("涨跌幅", 0) or 
                    0
                )
                
                # 动态查找成交量字段（可能包含日期）
                volume = 0
                for key in stock.keys():
                    if key == "成交量" or key == "volume":
                        volume = stock.get(key, 0)
                        break
                    elif "成交量[" in str(key):  # 匹配 成交量[YYYYMMDD] 格式
                        volume = stock.get(key, 0)
                        break
                
                result_data = {
                    "task_id": task_id,
                    "stock_code": str(stock.get("code", "")),
                    "stock_name": str(stock.get("name", "")),
                    "momentum_score": float(stock.get("momentum_score", 0)),
                    "comprehensive_score": float(stock.get("comprehensive_score", 0)),
                    "volume_rank": idx,  # 使用排名作为 volume_rank
                    "hot_rank": idx,  # 使用排名作为 hot_rank
                    "final_rank": idx,
                    "close_price": float(close_price),
                    "change_pct": float(change_pct),
                    "volume": float(volume)
                }
                results.append(result_data)
                
                # 打印第一条数据用于调试
                if idx == 1:
                    logger.info(f"示例数据字段: {list(stock.keys())}")
                    logger.info(f"收盘价: {close_price}, 涨跌幅: {change_pct}, 成交量: {volume}")
            
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
            
            # 7. 保存到缓存（对于历史日期）
            from app.services.cache_service import get_cache_service
            cache_service = get_cache_service()
            cache_params = {
                'date': date,
                'volume_top_n': volume_top_n,
                'hot_top_n': hot_top_n
            }
            cache_data = {
                'task_id': task_id,
                'task': _tasks_store[task_id],
                'results': results
            }
            cache_service.set('screening', cache_params, cache_data)
            logger.info(f"筛选结果已缓存: {date}")
            
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
        
        # 先检查缓存（对于历史日期）
        from app.services.cache_service import get_cache_service
        cache_service = get_cache_service()
        
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
