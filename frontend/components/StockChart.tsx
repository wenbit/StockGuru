'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface KlineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  ma5?: number;
  ma10?: number;
  ma20?: number;
}

interface StockChartProps {
  stockCode: string;
  stockName: string;
  days?: number;
}

export default function StockChart({ stockCode, stockName, days = 60 }: StockChartProps) {
  const [data, setData] = useState<KlineData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchKlineData();
  }, [stockCode, days]);

  async function fetchKlineData() {
    setLoading(true);
    setError('');

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${apiUrl}/api/v1/stock/${stockCode}/kline?days=${days}`
      );

      if (!response.ok) {
        throw new Error('获取K线数据失败');
      }

      const result = await response.json();
      setData(result.data);
    } catch (err: any) {
      setError(err.message || '加载失败');
      console.error('获取K线数据失败:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg">
        <div className="text-red-500">❌ {error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-gray-500">暂无数据</div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">
        {stockName} ({stockCode}) - K线图
      </h3>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              // 只显示月-日
              const date = new Date(value);
              return `${date.getMonth() + 1}-${date.getDate()}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)' }}
            formatter={(value: any) => `¥${Number(value).toFixed(2)}`}
          />
          <Legend />

          {/* 收盘价线 */}
          <Line
            type="monotone"
            dataKey="close"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            name="收盘价"
          />

          {/* MA5 均线 */}
          <Line
            type="monotone"
            dataKey="ma5"
            stroke="#10b981"
            strokeWidth={1.5}
            dot={false}
            name="MA5"
            strokeDasharray="5 5"
          />

          {/* MA10 均线 */}
          <Line
            type="monotone"
            dataKey="ma10"
            stroke="#f59e0b"
            strokeWidth={1.5}
            dot={false}
            name="MA10"
            strokeDasharray="5 5"
          />

          {/* MA20 均线 */}
          <Line
            type="monotone"
            dataKey="ma20"
            stroke="#ef4444"
            strokeWidth={1.5}
            dot={false}
            name="MA20"
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
        <div>
          <span className="text-gray-500">最新价:</span>
          <span className="ml-2 font-semibold">
            ¥{data[data.length - 1]?.close.toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">最高:</span>
          <span className="ml-2 font-semibold text-red-600">
            ¥{Math.max(...data.map(d => d.high)).toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">最低:</span>
          <span className="ml-2 font-semibold text-green-600">
            ¥{Math.min(...data.map(d => d.low)).toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">数据天数:</span>
          <span className="ml-2 font-semibold">{data.length}天</span>
        </div>
      </div>
    </div>
  );
}
