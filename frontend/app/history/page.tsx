'use client';

import { useState, useEffect } from 'react';
import { apiClient, TaskResult } from '@/lib/api-client';
import Link from 'next/link';

export default function HistoryPage() {
  const [tasks, setTasks] = useState<TaskResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTask, setSelectedTask] = useState<TaskResult | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  async function fetchHistory() {
    setLoading(true);
    setError('');

    try {
      const result = await apiClient.listScreenings(20);
      setTasks(result);
    } catch (err: any) {
      setError(err.message || '加载历史记录失败');
      console.error('获取历史记录失败:', err);
    } finally {
      setLoading(false);
    }
  }

  function getStatusBadge(status: string) {
    const badges = {
      completed: { text: '已完成', class: 'bg-green-100 text-green-800' },
      failed: { text: '失败', class: 'bg-red-100 text-red-800' },
      running: { text: '运行中', class: 'bg-blue-100 text-blue-800' },
      pending: { text: '等待中', class: 'bg-yellow-100 text-yellow-800' },
    };
    const badge = badges[status as keyof typeof badges] || { text: status, class: 'bg-gray-100 text-gray-800' };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${badge.class}`}>
        {badge.text}
      </span>
    );
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  if (loading) {
    return (
      <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500 text-lg">加载中...</div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto">
        {/* 头部 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                📚 历史记录
              </h1>
              <p className="text-gray-600">
                查看所有筛选任务的历史记录
              </p>
            </div>
            <Link 
              href="/"
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
            >
              ← 返回首页
            </Link>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">❌ {error}</p>
          </div>
        )}

        {/* 任务列表 */}
        {tasks.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">暂无历史记录</h2>
            <p className="text-gray-600 mb-6">开始你的第一次筛选吧！</p>
            <Link 
              href="/"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
            >
              开始筛选
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => (
              <div
                key={task.task_id}
                className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 cursor-pointer border border-gray-100 hover:border-blue-300"
                onClick={() => setSelectedTask(task)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-xl font-bold text-gray-900">
                        任务 #{task.task_id.slice(0, 8)}
                      </h3>
                      {getStatusBadge(task.status)}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">进度</span>
                        <div className="font-semibold text-gray-900">{task.progress}%</div>
                      </div>
                      <div>
                        <span className="text-gray-500">结果数量</span>
                        <div className="font-semibold text-gray-900">
                          {task.result_count !== undefined ? `${task.result_count} 只` : '-'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">创建时间</span>
                        <div className="font-semibold text-gray-900">
                          {task.task_id ? formatDate(task.task_id) : '-'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">状态</span>
                        <div className="font-semibold text-gray-900">
                          {task.status === 'completed' ? '✅ 完成' : 
                           task.status === 'failed' ? '❌ 失败' :
                           task.status === 'running' ? '⏳ 运行中' : '⏸️ 等待'}
                        </div>
                      </div>
                    </div>

                    {task.error_message && (
                      <div className="mt-3 p-3 bg-red-50 rounded-lg">
                        <p className="text-sm text-red-600">错误: {task.error_message}</p>
                      </div>
                    )}
                  </div>

                  <button className="ml-4 text-blue-600 hover:text-blue-800 font-semibold">
                    查看详情 →
                  </button>
                </div>

                {/* 进度条 */}
                {task.status === 'running' && (
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 详情模态框 */}
        {selectedTask && selectedTask.results && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedTask(null)}
          >
            <div 
              className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto p-8"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">任务详情</h2>
                  <p className="text-gray-500 mt-1">任务 ID: {selectedTask.task_id}</p>
                </div>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                {selectedTask.results.map((stock, index) => (
                  <div key={stock.stock_code} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-gray-900">#{index + 1}</span>
                          <span className="text-xl font-bold">{stock.stock_name}</span>
                          <span className="text-gray-500 font-mono">{stock.stock_code}</span>
                        </div>
                        <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">动量分数:</span>
                            <span className="ml-2 font-semibold">{stock.momentum_score.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">综合评分:</span>
                            <span className="ml-2 font-semibold">{stock.comprehensive_score.toFixed(2)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">涨跌幅:</span>
                            <span className={`ml-2 font-semibold ${stock.change_pct > 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {stock.change_pct > 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">¥{stock.close_price.toFixed(2)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
