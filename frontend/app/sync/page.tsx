'use client';

import { useState, useEffect } from 'react';

interface SyncLog {
  id: number;
  sync_date: string;
  sync_type: string;
  status: string;
  total_stocks: number;
  success_count: number;
  failed_count: number;
  error_message: string;
  started_at: string;
  completed_at: string;
  created_at: string;
}

export default function SyncPage() {
  const [logs, setLogs] = useState<SyncLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  async function fetchLogs() {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/sync/status?limit=20`);
      const result = await response.json();
      if (result.status === 'success') {
        setLogs(result.data);
      }
    } catch (err) {
      console.error('获取同步日志失败:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSyncToday() {
    setSyncing(true);
    setMessage('');
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      const result = await response.json();
      setMessage(`✅ ${result.message}`);
      
      // 刷新日志
      setTimeout(() => fetchLogs(), 2000);
      
    } catch (err: any) {
      setMessage(`❌ 同步失败: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  }

  async function handleSyncHistorical() {
    const days = prompt('请输入要同步的天数（建议90天）:', '90');
    if (!days) return;

    setSyncing(true);
    setMessage('');
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days: parseInt(days) })
      });

      const result = await response.json();
      setMessage(`✅ ${result.message}`);
      
      // 刷新日志
      setTimeout(() => fetchLogs(), 2000);
      
    } catch (err: any) {
      setMessage(`❌ 同步失败: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  }

  function getStatusBadge(status: string) {
    const styles = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      skipped: 'bg-gray-100 text-gray-800'
    };

    const labels = {
      success: '成功',
      failed: '失败',
      running: '运行中',
      pending: '等待中',
      skipped: '已跳过'
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🔄 数据同步管理
          </h1>
          <p className="text-lg text-gray-600">
            管理每日股票数据的同步任务
          </p>
        </div>

        {/* 操作区 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">手动同步</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={handleSyncToday}
              disabled={syncing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
            >
              {syncing ? '同步中...' : '📅 同步今日数据'}
            </button>
            
            <button
              onClick={handleSyncHistorical}
              disabled={syncing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
            >
              {syncing ? '同步中...' : '📊 同步历史数据'}
            </button>
          </div>

          {message && (
            <div className={`mt-4 p-3 rounded-lg ${message.includes('✅') ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className={message.includes('✅') ? 'text-green-800 text-sm' : 'text-red-800 text-sm'}>{message}</p>
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>💡 提示：</strong>
            </p>
            <ul className="text-sm text-blue-700 mt-2 space-y-1 ml-4">
              <li>• 系统每晚22点自动同步当日数据</li>
              <li>• 如果同步失败，会每小时自动重试</li>
              <li>• 首次使用建议先同步近90天的历史数据</li>
              <li>• 非交易日会自动跳过同步</li>
            </ul>
          </div>
        </div>

        {/* 同步日志 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">同步日志</h2>
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? '刷新中...' : '🔄 刷新'}
            </button>
          </div>

          {logs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>暂无同步记录</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">同步日期</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">总数</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">成功</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">失败</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">开始时间</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">完成时间</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{log.sync_date}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {log.sync_type === 'initial' ? '初始化' : '每日同步'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        {getStatusBadge(log.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                        {log.total_stocks || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-green-600 font-medium">
                        {log.success_count || 0}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600 font-medium">
                        {log.failed_count || 0}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {log.started_at ? new Date(log.started_at).toLocaleString('zh-CN') : '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {log.completed_at ? new Date(log.completed_at).toLocaleString('zh-CN') : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
