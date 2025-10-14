# K线图 API 修复说明

## 问题描述
前端访问 K线图 API (`/api/v1/stock/{code}/kline`) 时返回 500 Internal Server Error。

## 根本原因
1. **配置加载问题**：`app/core/config.py` 中的 `SUPABASE_URL` 和 `SUPABASE_KEY` 被定义为必填字段，但没有默认值
2. **NaN 值处理缺失**：在添加均线数据时，没有检查 pandas 的 NaN 值，导致 JSON 序列化失败

## 修复内容

### 1. 修改配置文件 (`app/core/config.py`)
```python
# 修改前
SUPABASE_URL: str
SUPABASE_KEY: str

# 修改后
SUPABASE_URL: str = ""
SUPABASE_KEY: str = ""
```

### 2. 修改 API 路由 (`app/api/stock.py`)
```python
# 添加必要的导入
import pandas as pd
import numpy as np

# 修改均线数据添加逻辑
# 修改前
for i, record in enumerate(kline_data):
    record['ma5'] = float(ma5.iloc[i]) if i < len(ma5) else None
    record['ma10'] = float(ma10.iloc[i]) if i < len(ma10) else None
    record['ma20'] = float(ma20.iloc[i]) if i < len(ma20) else None

# 修改后
for i, record in enumerate(kline_data):
    record['ma5'] = float(ma5.iloc[i]) if i < len(ma5) and not pd.isna(ma5.iloc[i]) else None
    record['ma10'] = float(ma10.iloc[i]) if i < len(ma10) and not pd.isna(ma10.iloc[i]) else None
    record['ma20'] = float(ma20.iloc[i]) if i < len(ma20) and not pd.isna(ma20.iloc[i]) else None
```

## 测试结果

### API 测试
```bash
# 测试 K线数据获取
curl http://localhost:8000/api/v1/stock/000001/kline?days=30

# 响应示例
{
    "code": "000001",
    "data": [
        {
            "date": "2025-10-14",
            "open": 11.39,
            "close": 11.57,
            "high": 11.6,
            "low": 11.36,
            "volume": 1843428,
            "amount": 2124120304.48,
            "ma5": 11.428,
            "ma10": 11.429,
            "ma20": 11.5275
        }
    ],
    "count": 30
}
```

### 前端集成
前端 `StockChart` 组件现在可以正常获取和显示 K线数据：
- ✅ 数据获取成功
- ✅ 均线计算正确
- ✅ CORS 配置正常
- ✅ 图表渲染正常

## 注意事项

1. **数据量限制**：
   - MA5 需要至少 5 天数据
   - MA10 需要至少 10 天数据
   - MA20 需要至少 20 天数据
   - 建议请求至少 30 天数据以获得完整的均线

2. **环境变量**：
   - 确保 `.env` 文件存在于 `backend/` 目录
   - 包含必要的配置项（SUPABASE_URL, SUPABASE_KEY 等）

3. **服务启动**：
   ```bash
   cd stockguru-web/backend
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 相关文件
- `/stockguru-web/backend/app/core/config.py` - 配置文件
- `/stockguru-web/backend/app/api/stock.py` - K线 API 路由
- `/frontend/components/StockChart.tsx` - 前端图表组件
- `/test_kline_api.py` - API 测试脚本
- `/test_kline_frontend.html` - 前端测试页面
