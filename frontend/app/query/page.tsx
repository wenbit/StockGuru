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
  const [allData, setAllData] = useState<DailyStockData[]>([]);  // 存储所有数据（用于前端分页）
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [error, setError] = useState('');
  const [frontendPage, setFrontendPage] = useState(1);  // 前端分页的当前页
  
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
    setFrontendPage(1);  // 重置前端分页
    
    try {
      // 如果填写了总数限制，需要特殊处理：
      // 1. 先查询所有符合条件的数据（用一个大的page_size）
      // 2. 取前N条（总数限制）
      // 3. 然后在前端分页显示
      const hasLimit = limitInput && parseInt(limitInput) > 0;
      const limitValue = hasLimit ? parseInt(limitInput) : 0;
      
      const queryData: any = {
        start_date: params.start_date,
        end_date: params.end_date,
        sort_by: params.sort_by,
        sort_order: params.sort_order,
        page: hasLimit ? 1 : params.page,  // 有限制时只查第1页
        page_size: hasLimit ? limitValue : params.page_size  // 有限制时用限制值作为page_size
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
      
      // 如果有总数限制，使用前端分页
      if (hasLimit) {
        setAllData(result.data);  // 保存所有数据
        setTotal(result.data.length);  // 实际返回的数量
        
        // 计算前端分页
        const pageSize = params.page_size;  // 每页50条
        const totalPages = Math.ceil(result.data.length / pageSize);
        setTotalPages(totalPages);
        
        // 显示当前页的数据
        const startIndex = (frontendPage - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        setData(result.data.slice(startIndex, endIndex));
      } else {
        // 没有限制，使用后端分页
        setAllData([]);
        setData(result.data);
        setTotal(result.total);
        setTotalPages(result.total_pages);
      }
      
    } catch (err: any) {
      setError(err.message || '查询失败');
      console.error('查询错误:', err);
    } finally {
      setLoading(false);
    }
  }

  function handlePageChange(newPage: number) {
    const hasLimit = limitInput && parseInt(limitInput) > 0;
    
    if (hasLimit && allData.length > 0) {
      // 前端分页：直接切换显示的数据
      setFrontendPage(newPage);
      const pageSize = params.page_size;
      const startIndex = (newPage - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      setData(allData.slice(startIndex, endIndex));
    } else {
      // 后端分页：重新查询
      setParams(prev => ({ ...prev, page: newPage }));
      setTimeout(() => handleQuery(), 100);
    }
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

  // 导出 CSV（备用方案）
  function exportToCSV(dataToExport: any[]) {
    console.log('使用CSV格式导出...');
    
    // CSV 表头
    const headers = ['日期', '股票代码', '股票名称', '收盘价', '涨跌幅', '成交量', '成交额'];
    
    // CSV 数据行
    const rows = dataToExport.map(item => [
      item.trade_date,
      item.stock_code,
      item.stock_name,
      item.close_price,
      item.change_pct ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct}%` : '-',
      item.volume,
      item.amount,
    ]);
    
    // 组合成 CSV 字符串
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    // 添加 BOM 以支持中文
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    
    // 创建下载链接
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `股票数据_${params.start_date}_${params.end_date}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('CSV导出成功！');
  }

  // 导出 Excel（导出所有查询结果）
  async function handleExportExcel() {
    try {
      console.log('开始导出Excel...');
      
      if (data.length === 0) {
        alert('没有数据可导出');
        return;
      }

      // 显示加载提示
      const loadingDiv = document.createElement('div');
      loadingDiv.id = 'export-loading';
      loadingDiv.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;padding:30px;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.3);z-index:9999;text-align:center;';
      loadingDiv.innerHTML = '<div style="font-size:18px;font-weight:bold;margin-bottom:10px;">正在导出数据...</div><div id="export-progress" style="color:#666;">准备中...</div>';
      document.body.appendChild(loadingDiv);

      const updateProgress = (msg: string) => {
        const progressEl = document.getElementById('export-progress');
        if (progressEl) progressEl.textContent = msg;
      };

      let dataToExport: any[] = [];
      const hasLimit = limitInput && parseInt(limitInput) > 0;

      if (hasLimit && allData.length > 0) {
        // 有总数限制，导出所有已加载的数据
        console.log(`导出已加载的数据: ${allData.length} 条`);
        updateProgress(`准备导出 ${allData.length} 条数据...`);
        dataToExport = allData;
      } else {
        // 需要获取所有数据（分批获取，每批1000条）
        console.log(`开始获取全部数据: ${total} 条`);
        updateProgress(`正在获取 ${total} 条数据...`);
        
        try {
          const startTime = Date.now();
          const maxPageSize = 1000; // API 限制
          const totalPages = Math.ceil(total / maxPageSize);
          
          dataToExport = [];
          
          for (let page = 1; page <= totalPages; page++) {
            const queryData: any = {
              start_date: params.start_date,
              end_date: params.end_date,
              sort_by: params.sort_by,
              sort_order: params.sort_order,
              page: page,
              page_size: maxPageSize
            };

            if (params.change_pct_min !== '') {
              queryData.change_pct_min = parseFloat(params.change_pct_min);
            }
            if (params.change_pct_max !== '') {
              queryData.change_pct_max = parseFloat(params.change_pct_max);
            }

            updateProgress(`正在获取数据... ${Math.round(page / totalPages * 100)}% (${dataToExport.length}/${total})`);

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/daily/query`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(queryData)
            });

            if (!response.ok) {
              throw new Error(`获取数据失败: ${response.status}`);
            }

            const result = await response.json();
            if (result.data && result.data.length > 0) {
              dataToExport.push(...result.data);
            }
            
            // 如果获取的数据少于请求的数量，说明已经是最后一页
            if (!result.data || result.data.length < maxPageSize) {
              break;
            }
          }
          
          const fetchTime = ((Date.now() - startTime) / 1000).toFixed(1);
          console.log(`成功获取数据: ${dataToExport.length} 条，耗时: ${fetchTime}秒`);
          
          if (dataToExport.length === 0) {
            throw new Error('未获取到数据');
          }
          
          updateProgress(`已获取 ${dataToExport.length} 条数据，正在生成文件...`);
        } catch (err) {
          document.body.removeChild(loadingDiv);
          console.error('获取数据失败:', err);
          alert('导出失败：' + (err as Error).message);
          return;
        }
      }

      console.log(`准备导出 ${dataToExport.length} 条数据`);

      // 使用 CSV 格式（更快更可靠）
      updateProgress('正在生成CSV文件...');
      
      // 使用 setTimeout 让 UI 有机会更新
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const startExport = Date.now();
      
      // CSV 表头
      const headers = ['日期', '股票代码', '股票名称', '收盘价', '涨跌幅', '成交量', '成交额'];
      
      // 批量处理数据（每次1000条）
      const batchSize = 1000;
      const csvRows: string[] = [headers.join(',')];
      
      for (let i = 0; i < dataToExport.length; i += batchSize) {
        const batch = dataToExport.slice(i, i + batchSize);
        const batchRows = batch.map(item => [
          item.trade_date,
          item.stock_code,
          item.stock_name,
          item.close_price,
          item.change_pct ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct}%` : '-',
          item.volume || '',
          item.amount || '',
        ].join(','));
        
        csvRows.push(...batchRows);
        
        // 更新进度
        const progress = Math.round((i + batch.length) / dataToExport.length * 100);
        updateProgress(`正在处理数据... ${progress}%`);
        
        // 让 UI 有机会更新
        if (i % 2000 === 0) {
          await new Promise(resolve => setTimeout(resolve, 10));
        }
      }
      
      const csvContent = csvRows.join('\n');
      const exportTime = ((Date.now() - startExport) / 1000).toFixed(1);
      console.log(`CSV生成完成，耗时: ${exportTime}秒`);
      
      updateProgress('正在下载文件...');
      
      // 添加 BOM 以支持中文
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
      
      // 创建下载链接
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `股票数据_${params.start_date}_${params.end_date}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      // 移除加载提示
      document.body.removeChild(loadingDiv);
      
      console.log('导出成功！');
      alert(`导出成功！\n已导出 ${dataToExport.length} 条数据\n文件格式：CSV（Excel可直接打开）`);
      
    } catch (err) {
      // 移除加载提示
      const loadingDiv = document.getElementById('export-loading');
      if (loadingDiv) document.body.removeChild(loadingDiv);
      
      console.error('导出失败:', err);
      alert('导出失败：' + (err as Error).message);
    }
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
                <option value="desc">涨跌幅（降序）</option>
                <option value="asc">涨跌幅（升序）</option>
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
                查询结果 
                <span className="text-gray-500 text-base ml-2">
                  符合条件 {formatNumber(total)} 条，当前显示 {data.length} 条
                </span>
              </h2>
              <div className="flex items-center gap-4">
                <button
                  onClick={handleExportExcel}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  导出数据
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
            {totalPages > 1 && (
              <div className="mt-6 flex justify-center items-center gap-2">
                <button
                  onClick={() => handlePageChange(1)}
                  disabled={(limitInput ? frontendPage : params.page) === 1}
                  className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  首页
                </button>
                <button
                  onClick={() => handlePageChange((limitInput ? frontendPage : params.page) - 1)}
                  disabled={(limitInput ? frontendPage : params.page) === 1}
                  className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  上一页
                </button>
                <span className="px-4 py-1 text-sm text-gray-700">
                  {limitInput ? frontendPage : params.page} / {totalPages}
                </span>
                <button
                  onClick={() => handlePageChange((limitInput ? frontendPage : params.page) + 1)}
                  disabled={(limitInput ? frontendPage : params.page) >= totalPages}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                下一页
              </button>
              <button
                onClick={() => handlePageChange(totalPages)}
                disabled={(limitInput ? frontendPage : params.page) >= totalPages}
                className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                末页
              </button>
            </div>
            )}
          </div>
        )}

        {/* 使用说明 */}
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">💡 使用说明</h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• <strong>涨跌幅筛选</strong>：可填写正负值，例如 +5 表示涨幅≥5%，-3 表示跌幅≥3%</p>
            <p>• <strong>日期范围</strong>：查询指定时间范围内的所有交易日数据</p>
            <p>• <strong>数据来源</strong>：数据每天19点自动同步，来源于 baostock（免费证券数据平台）</p>
            <p>• <strong>排序方式</strong>：默认按涨跌幅降序排列（涨幅最大的在前）</p>
            <p>• <strong>导出功能</strong>：导出CSV格式文件（Excel可直接打开），会导出所有符合条件的数据，不仅限于当前页</p>
          </div>
        </div>
      </div>
    </main>
  );
}
