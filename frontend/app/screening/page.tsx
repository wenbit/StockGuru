'use client';

import { useState, useEffect } from 'react';
import { apiClient, TaskResult, StockResult } from '@/lib/api-client';
import StockChart from '@/components/StockChart';
import StockCard from '@/components/StockCard';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string>('');
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [error, setError] = useState<string>('');
  const [date, setDate] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockResult | null>(null);
  const [clearingCache, setClearingCache] = useState(false);
  const [cacheMessage, setCacheMessage] = useState('');
  const [maxDate, setMaxDate] = useState('');

  // 在客户端设置默认日期，避免 hydration 错误
  useEffect(() => {
    // 设置最大日期为今天
    const today = new Date();
    setMaxDate(today.toISOString().split('T')[0]);
    
    // 从 localStorage 恢复日期，如果没有则使用前一天
    const savedDate = localStorage.getItem('lastScreeningDate');
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const defaultDate = yesterday.toISOString().split('T')[0];
    
    setDate(savedDate || defaultDate);
    
    // 从 localStorage 恢复筛选结果
    const savedTaskId = localStorage.getItem('lastTaskId');
    const savedTaskResult = localStorage.getItem('lastTaskResult');
    
    if (savedTaskId && savedTaskResult) {
      try {
        setTaskId(savedTaskId);
        setTaskResult(JSON.parse(savedTaskResult));
      } catch (e) {
        console.error('恢复筛选结果失败:', e);
      }
    }
  }, []);

  // 轮询任务结果
  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const result = await apiClient.getScreeningResult(taskId);
        setTaskResult(result);

        // 保存到 localStorage
        if (result.status === 'completed') {
          localStorage.setItem('lastTaskId', taskId);
          localStorage.setItem('lastTaskResult', JSON.stringify(result));
        }

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
      const screeningDate = date || new Date().toISOString().split('T')[0];
      
      // 保存选择的日期到 localStorage
      localStorage.setItem('lastScreeningDate', screeningDate);
      
      // 创建筛选任务
      const response = await apiClient.createScreening({
        date: screeningDate,
      });
      
      setTaskId(response.task_id);
    } catch (err: any) {
      setError(err.message || '筛选失败');
      console.error('筛选错误:', err);
      setLoading(false);
    }
  }
  
  // 当用户更改日期时保存到 localStorage
  function handleDateChange(newDate: string) {
    setDate(newDate);
    localStorage.setItem('lastScreeningDate', newDate);
  }

  // 清空所有缓存
  async function handleClearAllCache() {
    setClearingCache(true);
    setCacheMessage('');
    
    try {
      const result = await apiClient.clearAllCache();
      setCacheMessage(`✅ ${result.message}，共清除 ${result.count} 个缓存文件`);
      
      // 3秒后清除消息
      setTimeout(() => setCacheMessage(''), 3000);
    } catch (err: any) {
      setCacheMessage(`❌ 清除缓存失败: ${err.message}`);
    } finally {
      setClearingCache(false);
    }
  }

  // 清空当前日期的缓存
  async function handleClearDateCache() {
    if (!date) {
      setCacheMessage('❌ 请先选择日期');
      return;
    }
    
    setClearingCache(true);
    setCacheMessage('');
    
    try {
      const result = await apiClient.clearCacheByDate(date);
      setCacheMessage(`✅ ${result.message}，共清除 ${result.count} 个缓存文件`);
      
      // 3秒后清除消息
      setTimeout(() => setCacheMessage(''), 3000);
    } catch (err: any) {
      setCacheMessage(`❌ 清除缓存失败: ${err.message}`);
    } finally {
      setClearingCache(false);
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            📈 StockGuru
          </h1>
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
                max={maxDate}
                onChange={(e) => handleDateChange(e.target.value)}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              <p className="mt-1 text-xs text-gray-500">
                💡 只能选择今天及之前的日期
              </p>
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

            {/* 缓存管理按钮 */}
            <div className="flex gap-3 mt-2">
              <button
                onClick={handleClearDateCache}
                disabled={clearingCache || !date}
                className="flex-1 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
              >
                {clearingCache ? '清除中...' : '🗑️ 清除当前日期缓存'}
              </button>
              <button
                onClick={handleClearAllCache}
                disabled={clearingCache}
                className="flex-1 bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 text-sm"
              >
                {clearingCache ? '清除中...' : '🗑️ 清除所有缓存'}
              </button>
            </div>
          </div>

          {/* 缓存操作消息 */}
          {cacheMessage && (
            <div className={`mt-4 p-3 rounded-lg ${cacheMessage.includes('✅') ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className={cacheMessage.includes('✅') ? 'text-green-800 text-sm' : 'text-red-800 text-sm'}>{cacheMessage}</p>
            </div>
          )}

          {/* 错误提示 */}
          {error && (
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start">
                <span className="text-2xl mr-3">⚠️</span>
                <div className="flex-1">
                  <p className="text-amber-900 font-medium mb-1">筛选提示</p>
                  <p className="text-amber-800 text-sm">{error}</p>
                  {error.includes('非交易日') || error.includes('未来日期') ? (
                    <p className="text-amber-700 text-xs mt-2">
                      💡 建议：选择最近的交易日（工作日）进行筛选
                    </p>
                  ) : null}
                </div>
              </div>
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
                {/* 日期提示 */}
                {taskResult.actual_date && taskResult.query_date && taskResult.actual_date !== taskResult.query_date && (
                  <div className="mb-2 p-2 bg-amber-100 border border-amber-300 rounded text-sm">
                    <p className="text-amber-800">
                      📅 <strong>注意：</strong>查询日期 {taskResult.query_date} 为非交易日，显示的是 <strong>{taskResult.actual_date}</strong> 的数据
                    </p>
                  </div>
                )}
                {/* 无数据提示 */}
                {taskResult.no_data_reason && taskResult.result_count === 0 && (
                  <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-blue-800 text-sm">
                      ℹ️ {taskResult.no_data_reason}
                    </p>
                  </div>
                )}
                {/* 正常结果计数 */}
                {taskResult.result_count !== undefined && !taskResult.no_data_reason && (
                  <p className="text-sm text-gray-600">
                    找到 {taskResult.result_count} 只股票
                  </p>
                )}
                {/* 错误信息（真正的错误） */}
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
                    onClick={() => {
                      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                      window.open(`${apiUrl}/api/v1/screening/${taskId}/export/excel`, '_blank');
                    }}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
                  >
                    <span>📊</span>
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

        {/* 筛选规则说明 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
            📋 筛选规则说明
          </h2>
          
          <div className="space-y-6">
            {/* 动量分数 */}
            <div className="bg-blue-50 rounded-lg p-5">
              <h3 className="text-lg font-bold text-blue-900 mb-3">📈 动量分数计算</h3>
              <div className="space-y-2 text-gray-700">
                <p className="font-semibold">计算公式：</p>
                <div className="bg-white rounded p-3 font-mono text-sm">
                  动量分数 = 斜率 × R² × 10000
                </div>
                <ul className="list-disc list-inside space-y-1 text-sm ml-2">
                  <li><strong>斜率 (Slope)</strong>: 通过线性回归计算过去25天的价格趋势，衡量上涨速度</li>
                  <li><strong>R² (决定系数)</strong>: 0-1之间，衡量趋势的稳定性，越接近1越稳定</li>
                  <li><strong>放大系数 10000</strong>: 便于比较和排序</li>
                </ul>
                <p className="text-sm mt-2 text-blue-800">
                  💡 <strong>解读</strong>: 分数越高表示股票上涨趋势越强且越稳定
                </p>
              </div>
            </div>

            {/* 综合评分 */}
            <div className="bg-green-50 rounded-lg p-5">
              <h3 className="text-lg font-bold text-green-900 mb-3">⚖️ 综合评分计算</h3>
              <div className="space-y-2 text-gray-700">
                <p className="font-semibold">计算步骤：</p>
                <ol className="list-decimal list-inside space-y-2 text-sm ml-2">
                  <li>
                    <strong>获取数据</strong>: 成交额Top100 ∩ 热度Top100 (取交集)
                  </li>
                  <li>
                    <strong>Min-Max标准化</strong>:
                    <div className="bg-white rounded p-2 mt-1 font-mono text-xs">
                      标准化值 = (原始值 - 最小值) / (最大值 - 最小值)
                    </div>
                  </li>
                  <li>
                    <strong>加权计算</strong>:
                    <div className="bg-white rounded p-2 mt-1 font-mono text-xs">
                      综合评分 = 0.5 × 标准化成交额 + 0.5 × 标准化热度
                    </div>
                  </li>
                  <li>
                    <strong>初选</strong>: 按综合评分排序，取前30名
                  </li>
                  <li>
                    <strong>终选</strong>: 计算动量分数，按动量排序，取前10名
                  </li>
                </ol>
                <p className="text-sm mt-2 text-green-800">
                  💡 <strong>解读</strong>: 综合评分兼顾"资金"和"人气"，筛选出市场关注度高的股票
                </p>
              </div>
            </div>

            {/* 筛选条件 */}
            <div className="bg-amber-50 rounded-lg p-5">
              <h3 className="text-lg font-bold text-amber-900 mb-3">🔍 筛选条件</h3>
              <div className="space-y-2 text-gray-700">
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start">
                    <span className="text-red-600 mr-2">❌</span>
                    <span><strong>排除ST股票</strong>: 自动过滤ST、*ST等特别处理股票</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-red-600 mr-2">❌</span>
                    <span><strong>排除次新股</strong>: 过滤上市不足60天的股票</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-600 mr-2">✅</span>
                    <span><strong>成交额要求</strong>: 必须在当日成交额Top100内</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-600 mr-2">✅</span>
                    <span><strong>热度要求</strong>: 必须在当日热度Top100内</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-green-600 mr-2">✅</span>
                    <span><strong>动量要求</strong>: K线数据充足（至少20天）</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* 排序规则 */}
            <div className="bg-purple-50 rounded-lg p-5">
              <h3 className="text-lg font-bold text-purple-900 mb-3">🏆 排序规则</h3>
              <div className="space-y-2 text-gray-700">
                <p className="text-sm mb-3">最终结果按<strong>动量分数</strong>从高到低排序：</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">🥇</span>
                      <strong className="text-yellow-800">金牌股票</strong>
                    </div>
                    <p className="text-xs text-gray-600">排名: 第1-3名</p>
                  </div>
                  <div className="bg-gray-100 border-2 border-gray-400 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">🥈</span>
                      <strong className="text-gray-800">银牌股票</strong>
                    </div>
                    <p className="text-xs text-gray-600">排名: 第4-10名</p>
                  </div>
                </div>
                <p className="text-sm mt-3 text-purple-800">
                  💡 <strong>建议</strong>: 重点关注前3名金牌股票，它们具有最强的短期动量
                </p>
              </div>
            </div>

            {/* 免责声明 */}
            <div className="bg-red-50 border-l-4 border-red-500 rounded p-4">
              <p className="text-sm text-red-800">
                <strong>⚠️ 免责声明：</strong>
                本工具仅供学习和复盘参考使用，不构成任何投资建议。筛选结果基于历史数据计算，
                技术分析有滞后性，需结合基本面和消息面综合判断。市场有风险，投资需谨慎。
              </p>
            </div>
          </div>
        </div>

        {/* API 状态 */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
        </div>
      </div>
    </main>
  );
}
