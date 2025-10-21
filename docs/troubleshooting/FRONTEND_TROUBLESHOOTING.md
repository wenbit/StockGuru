# 前端查询问题排查指南

## ✅ 当前状态

### 后端服务
- **状态**: ✅ 正常运行
- **端口**: 8000
- **健康检查**: http://localhost:8000/health ✅
- **数据统计**: 97,923 条记录，5,278 只股票
- **日期范围**: 2025-09-01 至 2025-10-20

### 前端服务
- **状态**: ✅ 正常运行
- **端口**: 3000（默认）
- **配置**: NEXT_PUBLIC_API_URL=http://localhost:8000

### API 测试
- **查询接口**: ✅ 正常
- **统计接口**: ✅ 正常
- **CORS**: ✅ 已配置

## 🔍 问题排查步骤

### 1. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：

**Console 标签**：
- 是否有 JavaScript 错误？
- 是否有 API 请求失败？
- 错误信息是什么？

**Network 标签**：
- API 请求是否发送？
- 请求地址是否正确？
- 响应状态码是什么？
- 响应内容是什么？

### 2. 常见问题和解决方案

#### 问题 1：CORS 错误

**症状**：
```
Access to fetch at 'http://localhost:8000/api/v1/daily/query' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**解决**：
后端已配置 CORS，但如果仍有问题，检查后端日志：
```bash
tail -50 logs/backend.log | grep CORS
```

#### 问题 2：API 地址错误

**症状**：
```
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**检查**：
```bash
# 1. 确认后端运行
curl http://localhost:8000/health

# 2. 确认前端配置
cat frontend/.env.local

# 3. 测试 API
curl -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{"start_date":"2025-10-20","end_date":"2025-10-20","page":1,"page_size":10"}'
```

#### 问题 3：前端缓存问题

**解决**：
```bash
# 方法 1：硬刷新浏览器
# Chrome/Edge: Ctrl + Shift + R (Mac: Cmd + Shift + R)
# Firefox: Ctrl + F5

# 方法 2：清除浏览器缓存
# 浏览器设置 -> 隐私和安全 -> 清除浏览数据

# 方法 3：重启前端服务
cd frontend
# 停止当前服务 (Ctrl+C)
npm run dev
```

#### 问题 4：环境变量未生效

**检查**：
```bash
# 查看前端环境变量
cat frontend/.env.local

# 应该包含：
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

**修复**：
```bash
# 如果文件不存在或配置错误
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local

# 重启前端服务
cd frontend
# Ctrl+C 停止
npm run dev
```

#### 问题 5：日期范围问题

**症状**：查询特定日期没有数据

**检查数据库**：
```bash
# 查看可用的日期
curl -s http://localhost:8000/api/v1/daily/stats | python3 -m json.tool

# 输出示例：
# "latest_date": "2025-10-20",
# "earliest_date": "2025-09-01"
```

**解决**：
- 确保查询的日期在可用范围内
- 如果需要更多数据，运行同步任务

#### 问题 6：查询参数错误

**常见错误**：
```javascript
// ❌ 错误：日期格式不对
{"start_date": "10/20/2025"}

// ✅ 正确：使用 YYYY-MM-DD 格式
{"start_date": "2025-10-20"}
```

### 3. 快速测试命令

```bash
# 1. 测试后端健康
curl http://localhost:8000/health

# 2. 测试数据统计
curl http://localhost:8000/api/v1/daily/stats

# 3. 测试查询接口
curl -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-20",
    "end_date": "2025-10-20",
    "page": 1,
    "page_size": 10
  }' | python3 -m json.tool | head -50

# 4. 测试涨幅筛选
curl -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-20",
    "end_date": "2025-10-20",
    "min_change_pct": 5.0,
    "page": 1,
    "page_size": 10
  }' | python3 -m json.tool | head -50
```

### 4. 重启服务

如果以上都不行，尝试重启所有服务：

```bash
# 1. 停止所有服务
pkill -f "uvicorn app.main:app"
# 在前端终端按 Ctrl+C

# 2. 重启后端
cd stockguru-web/backend
source .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
cd ../..

# 3. 重启前端
cd frontend
npm run dev
```

## 🎯 具体页面问题

### 查询页面 (/query)

**预期行为**：
1. 页面加载时自动获取数据统计
2. 显示总记录数、股票数量、日期范围
3. 可以选择日期范围查询
4. 可以设置涨跌幅筛选
5. 显示查询结果表格

**如果没有数据显示**：

1. **打开浏览器开发者工具**（F12）
2. **查看 Console**：是否有错误？
3. **查看 Network**：
   - 找到 `/api/v1/daily/stats` 请求
   - 查看响应：是否返回数据？
   - 找到 `/api/v1/daily/query` 请求
   - 查看响应：是否返回数据？

4. **检查查询条件**：
   - 日期范围是否正确？
   - 是否在数据可用范围内？
   - 涨跌幅筛选是否过于严格？

### 同步页面 (/sync)

**预期行为**：
1. 显示最近的同步记录
2. 可以手动触发同步
3. 显示同步进度

**如果无法同步**：
- 检查后端日志：`tail -f logs/backend.log`
- 检查数据库连接
- 确认 baostock 服务可用

## 📊 数据验证

### 当前可用数据

```bash
# 查看数据统计
curl -s http://localhost:8000/api/v1/daily/stats | python3 -m json.tool

# 输出：
# {
#     "status": "success",
#     "data": {
#         "total_records": 97923,
#         "unique_stocks": 5278,
#         "latest_date": "2025-10-20",
#         "earliest_date": "2025-09-01"
#     }
# }
```

### 查询示例

```bash
# 查询 2025-10-20 的数据
curl -s -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-20",
    "end_date": "2025-10-20",
    "page": 1,
    "page_size": 10
  }' | python3 -m json.tool

# 查询涨幅超过 5% 的股票
curl -s -X POST http://localhost:8000/api/v1/daily/query \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-20",
    "end_date": "2025-10-20",
    "min_change_pct": 5.0,
    "page": 1,
    "page_size": 20
  }' | python3 -m json.tool
```

## 🆘 仍然无法解决？

### 收集诊断信息

```bash
# 1. 后端状态
ps aux | grep uvicorn
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/daily/stats

# 2. 前端状态
ps aux | grep next
cat frontend/.env.local

# 3. 浏览器信息
# - 浏览器类型和版本
# - Console 中的错误信息
# - Network 中的请求详情

# 4. 后端日志
tail -100 logs/backend.log
```

### 联系支持

提供以上诊断信息，以便快速定位问题。

---

**最后更新**: 2025-10-21 15:52  
**后端状态**: ✅ 正常运行  
**数据状态**: ✅ 97,923 条记录可用
