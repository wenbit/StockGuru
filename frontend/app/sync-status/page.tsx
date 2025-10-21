'use client';

import { useState, useEffect } from 'react';

interface SyncStatus {
  id: number;
  sync_date: string;
  status: string;
  total_records: number;
  success_count: number;
  failed_count: number;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  error_message: string | null;
  remarks: string | null;
  process_id: string | null;
  created_at: string;
  updated_at: string;
}

interface StatusSummary {
  total_days: number;
  status_count: {
    pending: number;
    syncing: number;
    success: number;
    failed: number;
    skipped: number;
  };
  recent_records: SyncStatus[];
}

interface SyncProgress {
  total: number;
  success: number;
  failed: number;
  pending: number;
  progress: number;
}

export default function SyncStatusPage() {
  const [summary, setSummary] = useState<StatusSummary | null>(null);
  const [recentStatus, setRecentStatus] = useState<SyncStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');
  const [syncProgress, setSyncProgress] = useState<SyncProgress | null>(null);
  const [showProgress, setShowProgress] = useState(false);
  
  // 批量同步日期选择
  const [batchStartDate, setBatchStartDate] = useState('');
  const [batchEndDate, setBatchEndDate] = useState('');
  
  // 后台同步进度监控
  const [backgroundProgress, setBackgroundProgress] = useState<any>(null);
  const [hasBackgroundTask, setHasBackgroundTask] = useState(false);
  const [refreshingProgress, setRefreshingProgress] = useState(false);
  
  // 分页和查询
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [pageSize] = useState(50);
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  
  // 统计数据（从列表计算）
  const [stats, setStats] = useState({
    total: 0,
    success: 0,
    failed: 0,
    syncing: 0,
    skipped: 0
  });

  // 加载数据
  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);
  
  // 检查后台任务的函数
  const checkBackgroundTask = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-status/sync/batch/active`);
      const data = await res.json();
      
      if (data.status === 'success' && data.data) {
        setBackgroundProgress(data.data.progress);
        setHasBackgroundTask(true);
      } else {
        setBackgroundProgress(null);
        setHasBackgroundTask(false);
      }
    } catch (err) {
      console.error('检查后台任务失败:', err);
    }
  };
  
  // 手动刷新进度
  const refreshProgress = async () => {
    setRefreshingProgress(true);
    await checkBackgroundTask();
    setTimeout(() => setRefreshingProgress(false), 500);
  };
  
  // 后台进度监控 - 每2秒检查一次（更快的刷新）
  useEffect(() => {
    // 立即执行一次
    checkBackgroundTask();
    
    // 每2秒检查一次（从3秒改为2秒，更实时）
    const interval = setInterval(checkBackgroundTask, 2000);
    
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      // 构建查询参数
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      });
      
      if (filterStartDate) params.append('start_date', filterStartDate);
      if (filterEndDate) params.append('end_date', filterEndDate);
      if (filterStatus) params.append('status', filterStatus);
      
      // 获取分页数据
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-status/list?${params}`);
      const data = await res.json();
      
      if (data.status === 'success') {
        setRecentStatus(data.data.records);
        setTotalPages(data.data.total_pages);
        setTotalRecords(data.data.total);
        
        // 使用后端返回的统计信息
        setStats(data.data.stats);
      }
    } catch (err) {
      console.error('加载数据失败:', err);
    } finally {
      setLoading(false);
    }
  }

  // 轮询进度
  async function pollProgress(syncDate: string) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-progress/date/${syncDate}`);
        const data = await res.json();
        
        if (data.status === 'success') {
          setSyncProgress(data.data);
          
          // 如果完成了，停止轮询
          if (data.data.pending === 0) {
            clearInterval(interval);
            setShowProgress(false);
            setMessage(`✅ 同步完成！成功: ${data.data.success}, 失败: ${data.data.failed}`);
            loadData();
          }
        }
      } catch (err) {
        console.error('获取进度失败:', err);
      }
    }, 2000); // 每2秒查询一次
    
    // 30分钟后自动停止轮询
    setTimeout(() => clearInterval(interval), 30 * 60 * 1000);
  }

  // 同步今日数据
  async function syncToday() {
    if (!confirm('确定要同步今日数据吗？\n\n支持断点续传，可随时中断后继续。')) return;
    
    setSyncing(true);
    setMessage('');
    
    const today = new Date().toISOString().split('T')[0];
    
    try {
      // 使用批量同步API
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-status/sync/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          start_date: today,
          end_date: today
        })
      });
      const data = await res.json();
      
      if (data.status === 'success') {
        const result = data.data;
        setMessage(`✅ 同步完成: 成功 ${result.success} 个, 失败 ${result.failed} 个, 跳过 ${result.skipped} 个`);
        loadData();
      } else {
        setMessage('❌ 启动失败: ' + (data.message || '未知错误'));
      }
    } catch (err: any) {
      setMessage('❌ 启动失败: ' + err.message);
    } finally {
      setSyncing(false);
    }
  }

  // 批量同步
  async function syncBatch() {
    if (!batchStartDate || !batchEndDate) {
      alert('请选择开始日期和结束日期');
      return;
    }
    
    if (new Date(batchStartDate) > new Date(batchEndDate)) {
      alert('开始日期不能晚于结束日期');
      return;
    }

    if (!confirm(`确定要同步 ${batchStartDate} 到 ${batchEndDate} 的数据吗？`)) return;
    
    setSyncing(true);
    setMessage('');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-status/sync/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          start_date: batchStartDate,
          end_date: batchEndDate
        })
      });
      const data = await res.json();
      
      if (data.status === 'success') {
        const taskId = data.data.task_id;
        setMessage(`🔄 同步任务已启动，正在同步 ${data.data.total_days} 天的数据...`);
        
        // 开始轮询进度
        pollBatchProgress(taskId);
      } else {
        setMessage('❌ 同步失败: ' + (data.message || '未知错误'));
        setSyncing(false);
      }
    } catch (err: any) {
      setMessage('❌ 同步失败: ' + err.message);
      setSyncing(false);
    }
  }
  
  // 轮询批量同步进度
  function pollBatchProgress(taskId: string) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/sync-status/sync/batch/progress/${taskId}`);
        const data = await res.json();
        
        if (data.status === 'success') {
          const progress = data.data;
          
          // 更新消息显示进度
          const percent = progress.progress_percent || (progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0);
          
          let msg = `🔄 ${progress.message}\n` +
            `进度: ${progress.current}/${progress.total} (${percent}%)\n` +
            `成功: ${progress.success}, 失败: ${progress.failed}, 跳过: ${progress.skipped}`;
          
          // 添加预计完成时间
          if (progress.estimated_completion) {
            const eta = new Date(progress.estimated_completion);
            msg += `\n预计完成: ${eta.toLocaleTimeString('zh-CN')}`;
          }
          
          // 显示错误信息
          if (progress.errors && progress.errors.length > 0) {
            msg += `\n\n⚠️ 最近错误:\n`;
            progress.errors.slice(-3).forEach((err: any) => {
              msg += `  ${err.date}: ${err.error}\n`;
            });
          }
          
          setMessage(msg);
          
          // 检查是否完成
          if (progress.status === 'completed' || progress.status === 'failed') {
            clearInterval(interval);
            setSyncing(false);
            
            if (progress.status === 'completed') {
              setMessage(`✅ ${progress.message}`);
            } else {
              setMessage(`❌ ${progress.message}`);
            }
            
            // 刷新数据
            loadData();
          }
        }
      } catch (err) {
        console.error('查询进度失败:', err);
      }
    }, 2000); // 每2秒查询一次
    
    // 30分钟后自动停止
    setTimeout(() => {
      clearInterval(interval);
      if (syncing) {
        setSyncing(false);
        setMessage('⚠️ 同步超时，请刷新页面查看结果');
      }
    }, 30 * 60 * 1000);
  }

  // 获取状态标签样式
  function getStatusBadge(status: string) {
    const styles: Record<string, string> = {
      success: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      syncing: 'bg-blue-100 text-blue-800',
      skipped: 'bg-gray-100 text-gray-800'
    };
    
    const labels: Record<string, string> = {
      success: '成功',
      failed: '失败',
      pending: '待同步',
      syncing: '同步中',
      skipped: '跳过'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    );
  }

  // 格式化时间
  function formatTime(time: string | null) {
    if (!time) return '-';
    return new Date(time).toLocaleString('zh-CN');
  }

  // 格式化耗时
  function formatDuration(seconds: number | null) {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}分${secs}秒`;
  }
  
  // 处理查询按钮点击
  function handleQuery() {
    if (currentPage === 1) {
      // 如果已经在第一页，直接加载数据
      loadData();
    } else {
      // 否则重置到第一页，useEffect会自动加载
      setCurrentPage(1);
    }
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            🔄 数据同步状态管理
          </h1>
          <p className="text-lg text-gray-600">
            监控和管理每日数据同步任务
          </p>
        </div>

        {/* 后台同步进度监控 */}
        {hasBackgroundTask && backgroundProgress && (
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg p-6 mb-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold flex items-center gap-2 mb-2">
                  <span className="animate-pulse">🔄</span>
                  后台同步进度
                </h2>
                <div className="text-sm opacity-90">
                  {backgroundProgress.start_time && backgroundProgress.end_time && (
                    <span>同步范围: {backgroundProgress.start_time} 至 {backgroundProgress.end_time}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={refreshProgress}
                  disabled={refreshingProgress}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors duration-200 disabled:opacity-50 flex items-center gap-2"
                  title="刷新进度"
                >
                  <span className={refreshingProgress ? 'animate-spin' : ''}>🔄</span>
                  刷新
                </button>
                <span className="text-3xl font-bold">
                  {backgroundProgress.progress_percent || 0}%
                </span>
              </div>
            </div>
            
            {/* 进度条 - 增强版 */}
            <div className="relative w-full bg-white/30 rounded-full h-4 mb-4 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-white to-blue-100 h-4 rounded-full transition-all duration-500 shadow-lg relative"
                style={{ width: `${backgroundProgress.progress_percent || 0}%` }}
              >
                {/* 动画效果 */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
              </div>
              {/* 百分比文字 */}
              <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white drop-shadow-lg">
                {backgroundProgress.progress_percent || 0}%
              </div>
            </div>
            
            {/* 详细信息 - 增强版 */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm hover:bg-white/30 transition-all">
                <div className="text-xs opacity-90 mb-1">📅 当前日期</div>
                <div className="text-lg font-bold">{backgroundProgress.current_date || '-'}</div>
              </div>
              <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm hover:bg-white/30 transition-all">
                <div className="text-xs opacity-90 mb-1">📊 进度</div>
                <div className="text-lg font-bold">
                  {backgroundProgress.current}/{backgroundProgress.total}
                  <span className="text-sm ml-1">天</span>
                </div>
              </div>
              <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm hover:bg-white/30 transition-all">
                <div className="text-xs opacity-90 mb-1">✅ 成功</div>
                <div className="text-lg font-bold text-green-300">{backgroundProgress.success}</div>
              </div>
              <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm hover:bg-white/30 transition-all">
                <div className="text-xs opacity-90 mb-1">❌ 失败</div>
                <div className="text-lg font-bold text-red-300">{backgroundProgress.failed}</div>
              </div>
              <div className="bg-white/20 rounded-lg p-3 backdrop-blur-sm hover:bg-white/30 transition-all">
                <div className="text-xs opacity-90 mb-1">⏭️ 跳过</div>
                <div className="text-lg font-bold text-yellow-300">{backgroundProgress.skipped}</div>
              </div>
            </div>
            
            {/* 状态消息 - 增强版 */}
            <div className="bg-white/20 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-2">
                <span className="text-lg animate-pulse">💬</span>
                <div className="flex-1">
                  <div className="text-sm font-medium">{backgroundProgress.message || '正在同步...'}</div>
                  <div className="flex items-center gap-4 mt-2 text-xs opacity-90">
                    {backgroundProgress.task_start_time && (
                      <span>⏰ 开始: {new Date(backgroundProgress.task_start_time).toLocaleTimeString('zh-CN')}</span>
                    )}
                    {backgroundProgress.estimated_completion && (
                      <span>🎯 预计完成: {new Date(backgroundProgress.estimated_completion).toLocaleTimeString('zh-CN')}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            {/* 错误信息 */}
            {backgroundProgress.errors && backgroundProgress.errors.length > 0 && (
              <div className="mt-4 bg-red-500/30 rounded-lg p-3 backdrop-blur-sm">
                <div className="text-sm font-bold mb-2">⚠️ 最近错误:</div>
                {backgroundProgress.errors.slice(-3).map((err: any, idx: number) => (
                  <div key={idx} className="text-xs opacity-90">
                    • {err.date}: {err.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 批量同步 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center gap-4 p-4 bg-green-50 rounded-lg">
            <label className="text-sm font-medium text-gray-700">批量同步：</label>
            <input
              type="date"
              value={batchStartDate}
              onChange={(e) => setBatchStartDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="开始日期"
            />
            <span className="text-gray-500">至</span>
            <input
              type="date"
              value={batchEndDate}
              onChange={(e) => setBatchEndDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="结束日期"
            />
            <button
              onClick={syncBatch}
              disabled={syncing || !batchStartDate || !batchEndDate}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              开始同步
            </button>
          </div>

          {message && (
            <div className={`mt-4 p-4 rounded-lg ${message.startsWith('✅') ? 'bg-green-50 text-green-800' : message.startsWith('🔄') ? 'bg-blue-50 text-blue-800' : 'bg-red-50 text-red-800'}`}>
              <pre className="whitespace-pre-wrap font-sans">{message}</pre>
            </div>
          )}

          {/* 实时进度显示 */}
          {showProgress && syncProgress && (
            <div className="mt-4 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-blue-900">
                  🔄 同步进度
                </h3>
                <span className="text-2xl font-bold text-blue-700">
                  {syncProgress.progress.toFixed(1)}%
                </span>
              </div>
              
              {/* 进度条 */}
              <div className="w-full bg-blue-200 rounded-full h-4 mb-4">
                <div 
                  className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                  style={{ width: `${syncProgress.progress}%` }}
                ></div>
              </div>
              
              {/* 详细统计 */}
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-gray-600">总数</div>
                  <div className="text-xl font-bold text-gray-900">{syncProgress.total.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-green-600">成功</div>
                  <div className="text-xl font-bold text-green-700">{syncProgress.success.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-red-600">失败</div>
                  <div className="text-xl font-bold text-red-700">{syncProgress.failed.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-yellow-600">待同步</div>
                  <div className="text-xl font-bold text-yellow-700">{syncProgress.pending.toLocaleString()}</div>
                </div>
              </div>
              
              {/* 提示信息 */}
              <div className="mt-4 text-sm text-blue-700">
                💡 支持断点续传：可随时关闭页面，下次继续同步
              </div>
            </div>
          )}
        </div>

        {/* 状态统计 */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-lg p-6 min-w-0">
            <div className="text-sm text-gray-600 mb-1">总天数</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
          </div>
          <div className="bg-green-50 rounded-xl shadow-lg p-6 min-w-0">
            <div className="text-sm text-green-600 mb-1">成功</div>
            <div className="text-3xl font-bold text-green-700">{stats.success}</div>
          </div>
          <div className="bg-red-50 rounded-xl shadow-lg p-6 min-w-0">
            <div className="text-sm text-red-600 mb-1">失败</div>
            <div className="text-3xl font-bold text-red-700">{stats.failed}</div>
          </div>
          <div className="bg-blue-50 rounded-xl shadow-lg p-6 min-w-0">
            <div className="text-sm text-blue-600 mb-1">同步中</div>
            <div className="text-3xl font-bold text-blue-700">{stats.syncing}</div>
          </div>
        </div>

        {/* 同步记录表格 */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            📋 同步记录 (共 {totalRecords} 条)
          </h2>
          
          {/* 查询条件 */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">开始日期</label>
                  <input
                    type="date"
                    value={filterStartDate}
                    onChange={(e) => setFilterStartDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">结束日期</label>
                  <input
                    type="date"
                    value={filterEndDate}
                    onChange={(e) => setFilterEndDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">状态</label>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">全部</option>
                    <option value="success">成功</option>
                    <option value="failed">失败</option>
                    <option value="syncing">同步中</option>
                    <option value="skipped">跳过</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={handleQuery}
                    disabled={loading}
                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 disabled:opacity-50"
                  >
                    {loading ? '查询中...' : '查询'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">加载中...</p>
            </div>
          ) : recentStatus.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              暂无同步记录
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">总数</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">成功</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">失败</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">开始时间</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">结束时间</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">耗时</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">备注</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentStatus.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                        {record.sync_date}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        {getStatusBadge(record.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                        {record.total_records?.toLocaleString() || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-green-600">
                        {record.success_count?.toLocaleString() || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-red-600">
                        {record.failed_count?.toLocaleString() || '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {formatTime(record.start_time)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {formatTime(record.end_time)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                        {formatDuration(record.duration_seconds)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                        {record.remarks || record.error_message || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* 分页 */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                  <div className="text-sm text-gray-700">
                    第 {currentPage} 页，共 {totalPages} 页 | 总计 {totalRecords} 条记录
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      首页
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      上一页
                    </button>
                    <button
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      下一页
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      末页
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 使用说明 */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">💡 使用说明</h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• <strong>同步今日数据</strong>: 手动触发今日数据同步</p>
            <p>• <strong>批量同步</strong>: 选择开始和结束日期进行批量同步</p>
            <p>• <strong>自动同步</strong>: 系统每晚20:00自动同步当日数据</p>
            <p>• <strong>状态说明</strong>: 成功=已完成, 失败=需重试, 同步中=正在进行, 跳过=非交易日</p>
            <p>• <strong>查询功能</strong>: 支持按日期范围和状态筛选，每页显示50条记录</p>
          </div>
        </div>
      </div>
    </main>
  );
}
