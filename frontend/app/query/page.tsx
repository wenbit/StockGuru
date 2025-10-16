'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import * as XLSX from 'xlsx';

interface DailyStockData {
  id: number;
  stock_code: string;
  stock_name: string;
  trade_date: string;
  open_price: number;
  close_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  amount: number;
  change_pct: number;
  change_amount: number;
  turnover_rate: number;
  amplitude: number;
}

interface QueryParams {
  start_date: string;
  end_date: string;
  change_pct_min: string;
  change_pct_max: string;
  sort_by: string;
  sort_order: string;
  page: number;
  page_size: number;
}

export default function QueryPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DailyStockData[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [error, setError] = useState('');
  
  // 查询参数
  const [params, setParams] = useState<QueryParams>({
    start_date: '',
    end_date: '',
    change_pct_min: '',
    change_pct_max: '',
    sort_by: 'change_pct',
    sort_order: 'desc',
    page: 1,
    page_size: 50  // 默认50条
  });
  
  // 总数限制（可选）
  const [limitInput, setLimitInput] = useState<string>('');

  // 数据统计
  const [stats, setStats] = useState<any>(null);

  // 初始化日期
  useEffect(() => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    setParams(prev => ({
      ...prev,
      start_date: yesterday.toISOString().split('T')[0],  // 默认昨天
      end_date: yesterday.toISOString().split('T')[0]     // 默认昨天
    }));

    // 获取数据统计
    fetchStats();
  }, []);

  async function fetchStats() {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/stats`);
      const result = await response.json();
      if (result.status === 'success') {
        setStats(result.data);
      }
    } catch (err) {
      console.error('获取统计信息失败:', err);
    }
  }

  async function handleQuery() {
    setLoading(true);
    setError('');
    
    try {
      // 如果填写了总数限制，使用限制值；否则使用默认的 page_size
      const actualPageSize = limitInput ? parseInt(limitInput) : params.page_size;
      
      const queryData: any = {
        start_date: params.start_date,
        end_date: params.end_date,
        sort_by: params.sort_by,
        sort_order: params.sort_order,
        page: params.page,
        page_size: actualPageSize
      };

      // 只有填写了涨跌幅才添加到查询条件
      if (params.change_pct_min !== '') {
        queryData.change_pct_min = parseFloat(params.change_pct_min);
      }
      if (params.change_pct_max !== '') {
        queryData.change_pct_max = parseFloat(params.change_pct_max);
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(queryData)
      });

      if (!response.ok) {
        throw new Error('查询失败');
      }

      const result = await response.json();
      setData(result.data);
      setTotal(result.total);
      setTotalPages(result.total_pages);
      
    } catch (err: any) {
      setError(err.message || '查询失败');
      console.error('查询错误:', err);
    } finally {
      setLoading(false);
    }
  }

  function handlePageChange(newPage: number) {
    setParams(prev => ({ ...prev, page: newPage }));
    // 自动触发查询
    setTimeout(() => handleQuery(), 100);
  }

  function formatNumber(num: number | null | undefined): string {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
  }

  function formatVolume(vol: number | null | undefined): string {
    if (vol === null || vol === undefined) return '-';
    if (vol >= 100000000) {
      return (vol / 100000000).toFixed(2) + '亿';
    } else if (vol >= 10000) {
      return (vol / 10000).toFixed(2) + '万';
    }
    return vol.toString();
  }

  // 导出 Excel（与页面表格列顺序完全一致）
  function handleExportExcel() {
    if (data.length === 0) {
      alert('没有数据可导出');
      return;
    }

    // 准备导出数据（顺序与页面表格一致）
    const exportData = data.map(item => ({
      '日期': item.trade_date,
      '股票代码': item.stock_code,
      '股票名称': item.stock_name,
      '收盘价': item.close_price,
      '涨跌幅': item.change_pct ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct}%` : '-',
      '成交量': item.volume,
      '成交额': item.amount,
    }));

    // 创建工作簿
    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '股票数据');

    // 设置列宽
    const colWidths = [
      { wch: 12 }, // 日期
      { wch: 10 }, // 股票代码
      { wch: 12 }, // 股票名称
      { wch: 10 }, // 收盘价
      { wch: 12 }, // 涨跌幅
      { wch: 15 }, // 成交量
      { wch: 15 }, // 成交额
    ];
    ws['!cols'] = colWidths;

    // 生成文件名
    const fileName = `股票数据_${params.start_date}_${params.end_date}_${new Date().getTime()}.xlsx`;

    // 下载文件
    XLSX.writeFile(wb, fileName);
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            📊 股票数据查询
          </h1>
          <p className="text-lg text-gray-600">
            查询历史交易数据，按涨跌幅筛选
          </p>
        </div>

        {/* 数据统计 */}
        {stats && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">数据概览</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600">{formatNumber(stats.total_records)}</div>
                <div className="text-sm text-gray-600 mt-1">总记录数</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-3xl font-bold text-green-600">{formatNumber(stats.unique_stocks)}</div>
                <div className="text-sm text-gray-600 mt-1">股票数量</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{stats.earliest_date || '-'}</div>
                <div className="text-sm text-gray-600 mt-1">最早日期</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">{stats.latest_date || '-'}</div>
                <div className="text-sm text-gray-600 mt-1">最新日期</div>
              </div>
            </div>
          </div>
        )}

        {/* 查询表单 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">查询条件</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 开始日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                开始日期
              </label>
              <input
                type="date"
                value={params.start_date}
                onChange={(e) => setParams(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 结束日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                结束日期
              </label>
              <input
                type="date"
                value={params.end_date}
                onChange={(e) => setParams(prev => ({ ...prev, end_date: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 最小涨跌幅 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最小涨跌幅 (%)
              </label>
              <input
                type="number"
                step="0.01"
                placeholder="例如: -5 或 5"
                value={params.change_pct_min}
                onChange={(e) => setParams(prev => ({ ...prev, change_pct_min: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 最大涨跌幅 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最大涨跌幅 (%)
              </label>
              <input
                type="number"
                step="0.01"
                placeholder="例如: 10"
                value={params.change_pct_max}
                onChange={(e) => setParams(prev => ({ ...prev, change_pct_max: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 排序方式 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                排序方式
              </label>
              <select
                value={params.sort_order}
                onChange={(e) => setParams(prev => ({ ...prev, sort_order: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="desc">降序（高到低）</option>
                <option value="asc">升序（低到高）</option>
              </select>
            </div>

            {/* 总数 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                总数
              </label>
              <input
                type="number"
                min="1"
                max="10000"
                placeholder="不填则返回所有结果"
                value={limitInput}
                onChange={(e) => {
                  setLimitInput(e.target.value);
                  setParams(prev => ({ ...prev, page: 1 }));
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* 查询按钮 */}
          <div className="mt-6">
            <button
              onClick={handleQuery}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  查询中...
                </>
              ) : (
                '🔍 开始查询'
              )}
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* 查询结果 */}
        {data.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">
                查询结果 <span className="text-gray-500 text-base ml-2">共 {formatNumber(total)} 条</span>
              </h2>
              <div className="flex items-center gap-4">
                <button
                  onClick={handleExportExcel}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  导出 Excel
                </button>
                <div className="text-sm text-gray-600">
                  第 {params.page} / {totalPages} 页
                </div>
              </div>
            </div>

            {/* 数据表格 */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日期</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股票代码</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">股票名称</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">收盘价</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">涨跌幅</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">成交量</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">成交额</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{item.trade_date}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600">{item.stock_code}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{item.stock_name}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">{formatNumber(item.close_price)}</td>
                      <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-semibold ${
                        item.change_pct > 0 ? 'text-red-600' : item.change_pct < 0 ? 'text-green-600' : 'text-gray-600'
                      }`}>
                        {item.change_pct > 0 ? '+' : ''}{formatNumber(item.change_pct)}%
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">{formatVolume(item.volume)}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900">{formatVolume(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 分页 */}
            <div className="mt-6 flex justify-center items-center gap-2">
              <button
                onClick={() => handlePageChange(1)}
                disabled={params.page === 1}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                首页
              </button>
              <button
                onClick={() => handlePageChange(params.page - 1)}
                disabled={params.page === 1}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                上一页
              </button>
              <span className="px-4 py-1 text-sm text-gray-700">
                {params.page} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(params.page + 1)}
                disabled={params.page >= totalPages}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                下一页
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={params.page >= totalPages}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                末页
              </button>
            </div>
          </div>
        )}

        {/* 使用说明 */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">💡 使用说明</h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• <strong>涨跌幅筛选</strong>：可填写正负值，例如 +5 表示涨幅≥5%，-3 表示跌幅≥3%</p>
            <p>• <strong>日期范围</strong>：查询指定时间范围内的所有交易日数据</p>
            <p>• <strong>数据来源</strong>：数据每晚22点自动同步，来源于akshare（东方财富）</p>
            <p>• <strong>排序方式</strong>：默认按涨跌幅降序排列（涨幅最大的在前）</p>
          </div>
        </div>
      </div>
    </main>
  );
}
