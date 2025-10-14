// app/screening/page.tsx
'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export default function ScreeningPage() {
  const [loading, setLoading] = useState(false);
  
  async function handleScreening() {
    setLoading(true);
    try {
      const result = await apiClient.createScreening({ date: '2024-10-11' });
      alert(`任务创建成功: ${result.task_id}`);
    } catch (error) {
      alert('筛选失败');
    } finally {
      setLoading(false);
    }
  }
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">开始筛选</h1>
      <button 
        onClick={handleScreening}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        {loading ? '筛选中...' : '🚀 一键筛选'}
      </button>
    </div>
  );
}
