/**
 * StockGuru API 客户端
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ScreeningParams {
  date: string;
  volume_top_n?: number;
  hot_top_n?: number;
}

export interface ScreeningResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskResult {
  id?: string;              // Supabase 返回的字段
  task_id?: string;         // 内存存储返回的字段
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result_count?: number;
  results?: StockResult[];
  error_message?: string;
  created_at?: string;
  completed_at?: string;
  actual_date?: string;     // 实际数据日期
  query_date?: string;      // 查询日期
  no_data_reason?: string;  // 无数据原因
}

export interface StockResult {
  stock_code: string;
  stock_name: string;
  momentum_score: number;
  comprehensive_score: number;
  final_rank: number;
  close_price: number;
  change_pct: number;
  volume: number;
}

export const apiClient = {
  /**
   * 创建筛选任务
   */
  async createScreening(params: ScreeningParams): Promise<ScreeningResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * 获取筛选结果
   */
  async getScreeningResult(taskId: string): Promise<TaskResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * 清除所有缓存
   */
  async clearAllCache(): Promise<{ message: string; count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/cache`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * 清除指定日期的缓存
   */
  async clearCacheByDate(date: string): Promise<{ message: string; date: string; count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/cache/${date}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },
};
