'use client';

import { useState, useEffect } from 'react';
import { apiClient, TaskResult, StockResult } from '@/lib/api-client';
import StockChart from '@/components/StockChart';
import StockCard from '@/components/StockCard';
import Link from 'next/link';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string>('');
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [error, setError] = useState<string>('');
  const [date, setDate] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockResult | null>(null);

  // 在客户端设置默认日期，避免 hydration 错误
  useEffect(() => {
    setDate(new Date().toISOString().split('T')[0]);
  }, []);

  // 轮询任务结果
  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const result = await apiClient.getScreeningResult(taskId);
        setTaskResult(result);

        // 如果任务完成或失败，停止轮询
        if (result.status === 'completed' || result.status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
        }
      } catch (err) {
        console.error('获取结果失败:', err);
      }
    }, 2000); // 每2秒查询一次

    return () => clearInterval(pollInterval);
  }, [taskId]);

  async function handleScreening() {
    setLoading(true);
    setError('');
    setTaskId('');
    setTaskResult(null);
    
    try {
      // 创建筛选任务
      const response = await apiClient.createScreening({
        date: date || new Date().toISOString().split('T')[0],
      });
      
      setTaskId(response.task_id);
    } catch (err: any) {
      setError(err.message || '筛选失败');
      console.error('筛选错误:', err);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-12">
          <div className="flex justify-between items-center mb-4">
            <div></div>
            <h1 className="text-5xl font-bold text-gray-900">
              📈 StockGuru
            </h1>
            <Link 
              href="/history"
              className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-lg shadow transition-colors flex items-center gap-2"
            >
              <span>📚</span>
              <span>历史记录</span>
            </Link>
          </div>
          <p className="text-xl text-gray-600">
            股票短线复盘助手
          </p>
        </div>

        {/* 主要操作区 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6 text-gray-800">
            开始筛选
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                筛选日期
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>

            <button
              onClick={handleScreening}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  筛选中...
                </>
              ) : (
                '🚀 一键筛选'
              )}
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">❌ {error}</p>
            </div>
          )}

          {/* 任务进度 */}
          {taskResult && (
            <div className="mt-6">
              {/* 进度条 */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>进度</span>
                  <span>{taskResult.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${taskResult.progress}%` }}
                  ></div>
                </div>
              </div>

              {/* 状态信息 */}
              <div className={`p-4 rounded-lg border ${
                taskResult.status === 'completed' ? 'bg-green-50 border-green-200' :
                taskResult.status === 'failed' ? 'bg-red-50 border-red-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <p className="font-semibold mb-2">
                  {taskResult.status === 'completed' && '✅ 筛选完成'}
                  {taskResult.status === 'failed' && '❌ 筛选失败'}
                  {taskResult.status === 'running' && '⏳ 正在筛选...'}
                  {taskResult.status === 'pending' && '⏳ 等待处理...'}
                </p>
                {taskResult.result_count !== undefined && (
                  <p className="text-sm text-gray-600">
                    找到 {taskResult.result_count} 只股票
                  </p>
                )}
                {taskResult.error_message && (
                  <p className="text-sm text-red-600 mt-2">
                    错误: {taskResult.error_message}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* 筛选结果 - 卡片式布局 */}
          {taskResult?.results && taskResult.results.length > 0 && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900">
                  筛选结果 
                  <span className="ml-3 text-lg text-gray-500">共 {taskResult.results.length} 只股票</span>
                </h3>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => window.open(`http://localhost:8000/api/v1/screening/${taskId}/export`, '_blank')}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span>📄</span>
                    <span>导出报告</span>
                  </button>
                  <div className="text-sm text-gray-500">
                    按动量分数排序
                  </div>
                </div>
              </div>

              {/* 卡片网格 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {taskResult.results.map((stock: StockResult) => (
                  <StockCard
                    key={stock.stock_code}
                    stock={stock}
                    rank={stock.final_rank}
                    onClick={() => setSelectedStock(stock)}
                  />
                ))}
              </div>
              
              {/* K线图展示 */}
              {selectedStock && (
                <div className="mt-8 bg-white rounded-2xl shadow-xl p-6">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900">K线图分析</h3>
                      <p className="text-gray-500 mt-1">
                        {selectedStock.stock_name} ({selectedStock.stock_code})
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedStock(null)}
                      className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      ✕ 关闭
                    </button>
                  </div>
                  <StockChart
                    stockCode={selectedStock.stock_code}
                    stockName={selectedStock.stock_name}
                    days={60}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* 功能说明 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800">
            功能说明
          </h2>
          <ul className="space-y-2 text-gray-600">
            <li>✅ 自动筛选高动量股票</li>
            <li>✅ 成交量和热度综合评分</li>
            <li>✅ 实时数据分析</li>
            <li>✅ 可视化图表展示</li>
          </ul>
        </div>

        {/* API 状态 */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
        </div>
      </div>
    </main>
  );
}
