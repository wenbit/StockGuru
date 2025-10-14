'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import StockChart from '@/components/StockChart';
import Link from 'next/link';

interface StockInfo {
  code: string;
  name: string;
  industry?: string;
  list_date?: string;
}

export default function StockDetailPage() {
  const params = useParams();
  const code = params.code as string;
  
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDays, setSelectedDays] = useState(60);

  useEffect(() => {
    fetchStockInfo();
  }, [code]);

  async function fetchStockInfo() {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`http://localhost:8000/api/v1/stock/${code}/info`);
      
      if (!response.ok) {
        throw new Error('获取股票信息失败');
      }

      const data = await response.json();
      setStockInfo(data);
    } catch (err: any) {
      setError(err.message || '加载失败');
      console.error('获取股票信息失败:', err);
    } finally {
      setLoading(false);
    }
  }

  const dayOptions = [
    { value: 30, label: '30天' },
    { value: 60, label: '60天' },
    { value: 90, label: '90天' },
    { value: 120, label: '120天' },
  ];

  if (loading) {
    return (
      <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500 text-lg">加载中...</div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto">
        {/* 头部导航 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <Link 
              href="/"
              className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-lg shadow transition-colors flex items-center gap-2"
            >
              <span>←</span>
              <span>返回首页</span>
            </Link>
            <Link 
              href="/history"
              className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-lg shadow transition-colors flex items-center gap-2"
            >
              <span>📚</span>
              <span>历史记录</span>
            </Link>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">❌ {error}</p>
          </div>
        )}

        {/* 股票信息卡片 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                {stockInfo?.name || code}
              </h1>
              <div className="flex items-center gap-4 text-gray-600">
                <span className="text-xl font-mono">{code}</span>
                {stockInfo?.industry && (
                  <>
                    <span className="text-gray-400">|</span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                      {stockInfo.industry}
                    </span>
                  </>
                )}
                {stockInfo?.list_date && (
                  <>
                    <span className="text-gray-400">|</span>
                    <span className="text-sm">上市日期: {stockInfo.list_date}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 快速统计 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">股票代码</div>
              <div className="text-2xl font-bold text-blue-700">{code}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">行业</div>
              <div className="text-lg font-bold text-purple-700">
                {stockInfo?.industry || '未知'}
              </div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">数据周期</div>
              <div className="text-2xl font-bold text-green-700">{selectedDays}天</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">图表类型</div>
              <div className="text-lg font-bold text-orange-700">K线 + 均线</div>
            </div>
          </div>
        </div>

        {/* 时间周期选择 */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">选择时间周期</h2>
          <div className="flex gap-3">
            {dayOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedDays(option.value)}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
                  selectedDays === option.value
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* K线图 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">
            📈 K线图分析
          </h2>
          <StockChart
            stockCode={code}
            stockName={stockInfo?.name || code}
            days={selectedDays}
          />
        </div>

        {/* 技术指标说明 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">
            📊 技术指标说明
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-4 h-4 bg-green-500 rounded"></div>
                <h3 className="font-semibold text-gray-900">MA5 (5日均线)</h3>
              </div>
              <p className="text-sm text-gray-600">
                短期趋势指标，反映近5个交易日的平均价格走势，适合短线交易参考。
              </p>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-4 h-4 bg-orange-500 rounded"></div>
                <h3 className="font-semibold text-gray-900">MA10 (10日均线)</h3>
              </div>
              <p className="text-sm text-gray-600">
                中短期趋势指标，反映近10个交易日的平均价格，常用于判断短期支撑和压力。
              </p>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-4 h-4 bg-red-500 rounded"></div>
                <h3 className="font-semibold text-gray-900">MA20 (20日均线)</h3>
              </div>
              <p className="text-sm text-gray-600">
                中期趋势指标，反映近20个交易日的平均价格，是重要的趋势判断依据。
              </p>
            </div>
          </div>

          {/* 使用建议 */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">💡 使用建议</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• 当短期均线上穿长期均线时，可能是买入信号（金叉）</li>
              <li>• 当短期均线下穿长期均线时，可能是卖出信号（死叉）</li>
              <li>• 均线密集缠绕时，表示市场处于盘整阶段</li>
              <li>• 均线发散时，表示趋势明确，可顺势而为</li>
            </ul>
          </div>
        </div>

        {/* 免责声明 */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ <strong>免责声明</strong>：本页面提供的数据和分析仅供参考，不构成任何投资建议。
            股市有风险，投资需谨慎。请根据自身情况做出投资决策。
          </p>
        </div>
      </div>
    </main>
  );
}
