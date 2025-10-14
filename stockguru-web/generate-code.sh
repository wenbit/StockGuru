#!/bin/bash

# StockGuru Web 版代码生成脚本
# 此脚本将生成所有必要的代码文件

echo "🚀 开始生成 StockGuru Web 版代码..."

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 生成后端配置文件
echo -e "${BLUE}📝 生成后端配置文件...${NC}"

cat > backend/app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # 前端地址
    FRONTEND_URL: str = "http://localhost:3000"
    
    # 筛选参数
    VOLUME_TOP_N: int = 100
    HOT_TOP_N: int = 100
    FINAL_TOP_N: int = 30
    MOMENTUM_DAYS: int = 25
    MOMENTUM_TOP_N: int = 10
    
    # 综合评分权重
    WEIGHT_VOLUME: float = 0.5
    WEIGHT_HOT: float = 0.5
    
    # 过滤规则
    EXCLUDE_ST: bool = True
    
    # 图表配置
    MA_PERIODS: list = [5, 10, 20]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "stockguru.log"
    
    # 数据获取配置
    KLINE_DAYS: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF

# 2. 生成 Supabase 客户端
cat > backend/app/core/supabase.py << 'EOF'
from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """获取 Supabase 客户端单例"""
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
    
    return _supabase_client
EOF

# 3. 生成 API 路由
cat > backend/app/api/screening.py << 'EOF'
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import date
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ScreeningRequest(BaseModel):
    date: str
    volume_top_n: Optional[int] = 100
    hot_top_n: Optional[int] = 100

class ScreeningResponse(BaseModel):
    task_id: str
    status: str
    message: str

@router.post("/screening", response_model=ScreeningResponse)
async def create_screening(request: ScreeningRequest):
    """创建筛选任务"""
    # TODO: 实现筛选逻辑
    return {
        "task_id": "test-id",
        "status": "pending",
        "message": "任务已创建"
    }

@router.get("/screening/{task_id}")
async def get_screening_result(task_id: str):
    """获取筛选结果"""
    # TODO: 实现获取逻辑
    return {"task_id": task_id, "status": "completed"}

@router.get("/screening")
async def list_screenings(limit: int = 10):
    """获取筛选任务列表"""
    # TODO: 实现列表逻辑
    return []
EOF

echo -e "${GREEN}✅ 后端代码生成完成！${NC}"

# 4. 生成前端示例代码
echo -e "${BLUE}📝 生成前端示例代码...${NC}"

mkdir -p frontend-examples

cat > frontend-examples/api-client.ts << 'EOF'
// lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  async createScreening(params: { date: string }) {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return response.json();
  },
  
  async getScreeningResult(taskId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/screening/${taskId}`);
    return response.json();
  },
};
EOF

cat > frontend-examples/screening-page.tsx << 'EOF'
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
EOF

echo -e "${GREEN}✅ 前端示例代码生成完成！${NC}"

echo ""
echo -e "${GREEN}🎉 所有代码生成完成！${NC}"
echo ""
echo "下一步："
echo "1. 配置 Supabase（参考 SETUP.md）"
echo "2. 配置环境变量"
echo "3. 启动开发服务器"
echo ""
echo "详细步骤请查看 SETUP.md"
