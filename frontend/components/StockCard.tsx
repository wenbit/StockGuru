'use client';

import { StockResult } from '@/lib/api-client';
import Link from 'next/link';

interface StockCardProps {
  stock: StockResult;
  rank: number;
  onClick?: () => void;
}

export default function StockCard({ stock, rank, onClick }: StockCardProps) {
  const isPositive = stock.change_pct > 0;
  
  return (
    <div 
      onClick={onClick}
      className="bg-white rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 p-6 cursor-pointer border border-gray-100 hover:border-blue-300"
    >
      {/* 排名徽章 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`
            w-10 h-10 rounded-full flex items-center justify-center font-bold text-white
            ${rank <= 3 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-gradient-to-br from-blue-400 to-blue-600'}
          `}>
            {rank}
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">{stock.stock_name}</h3>
            <p className="text-sm text-gray-500 font-mono">{stock.stock_code}</p>
          </div>
        </div>
        
        {/* 价格和涨跌幅 */}
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">
            ¥{stock.close_price.toFixed(2)}
          </div>
          <div className={`text-lg font-semibold ${isPositive ? 'text-red-600' : 'text-green-600'}`}>
            {isPositive ? '+' : ''}{stock.change_pct.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* 分隔线 */}
      <div className="border-t border-gray-100 my-4"></div>

      {/* 指标网格 */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">动量分数</div>
          <div className="text-xl font-bold text-blue-700">
            {stock.momentum_score.toFixed(2)}
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">综合评分</div>
          <div className="text-xl font-bold text-purple-700">
            {stock.comprehensive_score.toFixed(2)}
          </div>
        </div>
      </div>

      {/* 成交量 */}
      <div className="mt-4 bg-gray-50 rounded-lg p-3">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-600">成交量</span>
          <span className="text-sm font-semibold text-gray-900">
            {(stock.volume / 10000).toFixed(2)}万手
          </span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="mt-4 flex gap-2">
        <button 
          onClick={onClick}
          className="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
        >
          <span>K线图</span>
        </button>
        <Link
          href={`/stock/${stock.stock_code}`}
          className="flex-1 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2"
        >
          <span>详情</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
