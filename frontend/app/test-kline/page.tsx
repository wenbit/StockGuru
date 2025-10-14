'use client';

import { useState } from 'react';
import StockChart from '@/components/StockChart';

export default function TestKlinePage() {
  const [stockCode, setStockCode] = useState('000001');
  const [stockName, setStockName] = useState('平安银行');
  const [days, setDays] = useState(60);

  const testStocks = [
    { code: '000001', name: '平安银行' },
    { code: '600000', name: '浦发银行' },
    { code: '000002', name: '万科A' },
    { code: '600519', name: '贵州茅台' },
  ];

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">K线图测试页面</h1>

        {/* 控制面板 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">测试控制</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                股票代码
              </label>
              <input
                type="text"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="例如: 000001"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                股票名称
              </label>
              <input
                type="text"
                value={stockName}
                onChange={(e) => setStockName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="例如: 平安银行"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                天数
              </label>
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                min="10"
                max="120"
              />
            </div>
          </div>

          {/* 快速选择 */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              快速选择股票
            </label>
            <div className="flex flex-wrap gap-2">
              {testStocks.map((stock) => (
                <button
                  key={stock.code}
                  onClick={() => {
                    setStockCode(stock.code);
                    setStockName(stock.name);
                  }}
                  className="px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-md transition-colors"
                >
                  {stock.name} ({stock.code})
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* K线图展示 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">K线图展示</h2>
          <StockChart
            stockCode={stockCode}
            stockName={stockName}
            days={days}
          />
        </div>

        {/* API 信息 */}
        <div className="mt-6 bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold mb-2">API 信息</h3>
          <p className="text-sm text-gray-600">
            API 地址: http://localhost:8000/api/v1/stock/{stockCode}/kline?days={days}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            当前请求: http://localhost:8000/api/v1/stock/{stockCode}/kline?days={days}
          </p>
        </div>

        {/* 测试说明 */}
        <div className="mt-6 bg-gray-100 rounded-lg p-4">
          <h3 className="font-semibold mb-2">测试说明</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>✓ 测试不同股票代码的K线数据获取</li>
            <li>✓ 测试不同天数参数（建议30天以上以查看完整均线）</li>
            <li>✓ 验证MA5、MA10、MA20均线显示</li>
            <li>✓ 检查数据加载状态和错误处理</li>
            <li>✓ 验证图表交互和响应式布局</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
