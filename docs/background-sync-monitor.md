# 后台同步进度监控功能

## 🎯 功能说明

添加了一个独立的后台同步进度监控面板，可以实时显示当前正在运行的同步任务，**无需手动点击开始同步按钮**。

## ✨ 核心特性

### 1. 自动检测
- 每3秒自动检查是否有活跃的同步任务
- 无论任务从哪里启动（Web界面、命令行、定时任务）都能检测到
- 自动显示/隐藏进度面板

### 2. 实时更新
- 进度百分比实时更新
- 当前同步日期实时显示
- 成功/失败/跳过统计实时更新
- 预计完成时间动态计算

### 3. 美观设计
- 渐变蓝色背景，醒目显示
- 动画效果（脉冲图标、进度条过渡）
- 毛玻璃效果（backdrop-blur）
- 响应式布局

## 🎨 UI设计

### 面板布局

```
┌─────────────────────────────────────────────────────────┐
│ 🔄 后台同步进度                              33.3%      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                         │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│ │当前日期  │ │进度     │ │成功     │ │失败/跳过│      │
│ │2025-10-18│ │3/10     │ │2        │ │0/1      │      │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                         │
│ 正在同步 2025-10-18...                                 │
│ 预计完成: 16:25:30                                     │
│                                                         │
│ ⚠️ 最近错误:                                           │
│ • 2025-10-02: connection timeout                       │
└─────────────────────────────────────────────────────────┘
```

### 颜色方案

- **背景**: 蓝色到靛蓝渐变 (`from-blue-500 to-indigo-600`)
- **文字**: 白色
- **进度条**: 白色，带阴影
- **卡片**: 半透明白色 (`bg-white/20`)
- **成功**: 绿色 (`text-green-300`)
- **失败**: 黄色 (`text-yellow-300`)
- **错误**: 红色背景 (`bg-red-500/30`)

## 🔧 技术实现

### 后端API

#### 新增端点
```
GET /api/v1/sync-status/sync/batch/active
```

**功能**: 获取当前活跃的批量同步任务

**响应**:
```json
{
  "status": "success",
  "data": {
    "task_id": "2025-10-01_2025-10-09_1697587200",
    "progress": {
      "status": "running",
      "total": 9,
      "current": 3,
      "success": 2,
      "failed": 0,
      "skipped": 1,
      "current_date": "2025-10-03",
      "message": "正在同步 2025-10-03... (33.3%)",
      "progress_percent": 33.3,
      "estimated_completion": "2025-10-18T16:25:30",
      "errors": []
    }
  }
}
```

**无活跃任务时**:
```json
{
  "status": "success",
  "data": null
}
```

### 前端实现

#### 状态管理
```tsx
const [backgroundProgress, setBackgroundProgress] = useState<any>(null);
const [hasBackgroundTask, setHasBackgroundTask] = useState(false);
```

#### 自动轮询
```tsx
useEffect(() => {
  const checkBackgroundTask = async () => {
    const res = await fetch('/api/v1/sync-status/sync/batch/active');
    const data = await res.json();
    
    if (data.status === 'success' && data.data) {
      setBackgroundProgress(data.data.progress);
      setHasBackgroundTask(true);
    } else {
      setBackgroundProgress(null);
      setHasBackgroundTask(false);
    }
  };
  
  checkBackgroundTask(); // 立即执行
  const interval = setInterval(checkBackgroundTask, 3000); // 每3秒
  
  return () => clearInterval(interval);
}, []);
```

#### 条件渲染
```tsx
{hasBackgroundTask && backgroundProgress && (
  <div className="bg-gradient-to-r from-blue-500 to-indigo-600 ...">
    {/* 进度面板内容 */}
  </div>
)}
```

## 📊 显示内容

### 1. 顶部信息
- **标题**: "后台同步进度" + 脉冲动画图标
- **百分比**: 大号显示，实时更新

### 2. 进度条
- 白色进度条，带过渡动画
- 半透明背景
- 阴影效果

### 3. 统计卡片（4个）
- **当前日期**: 正在同步的日期
- **进度**: 当前/总数
- **成功**: 成功数量（绿色）
- **失败/跳过**: 失败和跳过数量（黄色）

### 4. 状态消息
- 当前状态描述
- 预计完成时间（如果有）

### 5. 错误信息（如果有）
- 最近3个错误
- 红色半透明背景
- 显示日期和错误原因

## 🔄 工作流程

### 场景1：页面加载
```
1. 页面加载
2. 立即检查活跃任务
3. 如果有任务 → 显示进度面板
4. 如果无任务 → 不显示
5. 开始3秒轮询
```

### 场景2：任务启动
```
1. 用户在命令行启动同步
2. 3秒内前端检测到
3. 自动显示进度面板
4. 开始实时更新
```

### 场景3：任务完成
```
1. 后台任务完成
2. 状态变为 completed
3. 3秒内前端检测到
4. 自动隐藏进度面板
```

## 💡 使用场景

### 1. 命令行同步
```bash
# 在终端启动同步
python3 scripts/test_copy_sync.py --all --date 2025-10-18

# 打开浏览器查看进度
# http://localhost:3000/sync-status
# 自动显示实时进度
```

### 2. API同步
```bash
# 通过API启动
curl -X POST http://localhost:8000/api/v1/sync-status/sync/batch \
  -d '{"start_date": "2025-10-01", "end_date": "2025-10-09"}'

# 浏览器自动显示进度
```

### 3. 定时任务
```python
# 定时任务自动同步
# 用户打开页面即可看到进度
```

## ⚡ 性能优化

### 1. 轮询频率
- 3秒一次，平衡实时性和性能
- 避免过于频繁的请求

### 2. 条件渲染
- 只在有任务时渲染面板
- 减少不必要的DOM操作

### 3. 自动清理
- 组件卸载时清理定时器
- 避免内存泄漏

## ✅ 优势对比

### 优化前
- ❌ 必须点击"开始同步"才能看到进度
- ❌ 命令行启动的任务看不到进度
- ❌ 需要手动刷新查看状态

### 优化后
- ✅ 自动检测所有同步任务
- ✅ 无需任何操作即可查看
- ✅ 实时更新，无需刷新
- ✅ 美观的视觉设计
- ✅ 完整的错误信息

## 🎯 总结

后台同步进度监控功能已完成：

1. **✅ 自动检测** - 每3秒检查活跃任务
2. **✅ 实时显示** - 进度、统计、时间
3. **✅ 美观设计** - 渐变背景、动画效果
4. **✅ 完整信息** - 进度、错误、预估时间
5. **✅ 无需操作** - 自动显示/隐藏

现在打开页面就能看到后台同步的实时进度了！🎉
