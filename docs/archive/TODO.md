# 📋 StockGuru 待完成需求清单

基于 PRD 文档和参考实现的对比分析

**对比日期**: 2025-10-15  
**PRD 版本**: V1.0  
**当前实现**: Web 版本 (模拟数据)

---

## 📊 需求完成度总览

| 模块 | PRD 需求 | 已完成 | 待完成 | 完成度 |
|------|---------|--------|--------|--------|
| 数据获取 | F-01 | ⚠️ 部分 | 真实 API | 50% |
| 综合评分 | F-02 | ✅ 完成 | - | 100% |
| 动量评分 | F-03 | ⚠️ 部分 | 真实计算 | 50% |
| 参数配置 | F-04 | ✅ 完成 | - | 100% |
| 可视化报告 | F-05 | ⚠️ 部分 | K线图 | 60% |
| 个股信息 | F-06 | ⚠️ 部分 | 完整指标 | 40% |
| **总体** | - | - | - | **67%** |

---

## ❌ 待完成需求详细清单

### 1. 核心功能：数据获取 (F-01)

#### ❌ F-01.1: 真实数据源集成
**PRD 要求**:
- 使用 pywencai 获取成交额 Top100
- 使用 pywencai 获取热度 Top100

**当前状态**:
- ✅ 代码框架已实现 (`data_fetcher.py`)
- ❌ 使用模拟数据，未调用真实 API

**待完成**:
```python
# 需要实现真实的 API 调用
class DataFetcher:
    def fetch_volume_ranking(self, date, top_n):
        # ❌ 当前返回模拟数据
        # ✅ 需要调用: pywencai.get(query=f'{date}成交额前{top_n}')
        pass
    
    def fetch_hot_ranking(self, date, top_n):
        # ❌ 当前返回模拟数据
        # ✅ 需要调用: pywencai.get(query=f'{date}个股热度前{top_n}')
        pass
```

**优先级**: 🔴 高  
**预计工作量**: 2-3 小时  
**依赖**: pywencai 库配置和测试

---

### 2. 核心功能：动量评分 (F-03)

#### ❌ F-03.1: 真实 K线数据获取
**PRD 要求**:
- 获取每只股票过去 25 天的 K线数据
- 使用线性回归计算动量分数

**当前状态**:
- ✅ 算法逻辑已实现 (`momentum_calculator.py`)
- ❌ 使用模拟数据，未获取真实 K线

**待完成**:
```python
# 需要实现真实的 K线数据获取
class MomentumCalculator:
    def calculate_momentum(self, stocks, date):
        for stock in stocks:
            # ❌ 当前使用模拟价格
            # ✅ 需要调用: akshare.stock_zh_a_hist(stock_code)
            kline_data = self._fetch_kline(stock['code'], date, 25)
            momentum = self._calculate_linear_regression(kline_data)
```

**优先级**: 🔴 高  
**预计工作量**: 2-3 小时  
**依赖**: akshare 库配置和测试

---

### 3. 可视化报告 (F-05)

#### ❌ F-05.1: K线图表展示
**PRD 要求**:
- 使用 pyecharts 生成 K线图
- 包含均线 (MA5, MA10, MA20)
- 单页面 HTML 报告

**当前状态**:
- ✅ Web 界面表格展示
- ❌ 缺少 K线图表
- ❌ 缺少均线指标

**待完成**:
1. **前端 K线图组件**
```typescript
// 需要添加 K线图展示组件
import { Line } from 'recharts' // 或使用 ECharts React

function StockChart({ stockCode, data }) {
  // 显示 K线图
  // 显示 MA5, MA10, MA20
}
```

2. **后端 K线数据接口**
```python
@router.get("/stock/{code}/kline")
async def get_stock_kline(code: str, days: int = 25):
    # 返回 K线数据和均线
    return {
        "kline": [...],
        "ma5": [...],
        "ma10": [...],
        "ma20": [...]
    }
```

**优先级**: 🟡 中  
**预计工作量**: 4-6 小时  
**依赖**: 图表库选择 (ECharts / Recharts)

---

#### ❌ F-05.2: HTML 报告导出
**PRD 要求**:
- 一键生成单页面 HTML 报告
- 可离线查看

**当前状态**:
- ✅ Web 界面在线查看
- ❌ 无法导出 HTML

**待完成**:
```python
# 添加报告生成功能
@router.get("/screening/{task_id}/export")
async def export_report(task_id: str):
    # 生成 HTML 报告
    # 包含所有股票的 K线图
    # 返回下载链接
    pass
```

**优先级**: 🟢 低  
**预计工作量**: 3-4 小时  
**依赖**: 模板引擎 (Jinja2)

---

### 4. 个股信息展示 (F-06)

#### ❌ F-06.1: 完整指标展示
**PRD 要求**:
- 基础信息：代码、名称
- 核心指标：动量得分
- 可视化图表：K线图 + 均线

**当前状态**:
- ✅ 基础信息：代码、名称
- ✅ 核心指标：动量分数、综合评分
- ✅ 额外指标：收盘价、涨跌幅
- ❌ 缺少 K线图

**待完成**:
1. **股票详情页**
```typescript
// 创建股票详情页面
// app/stock/[code]/page.tsx
function StockDetailPage({ code }) {
  return (
    <>
      <StockInfo code={code} />
      <StockChart code={code} />
      <StockIndicators code={code} />
    </>
  )
}
```

2. **更多技术指标**
- MACD
- RSI
- 成交量柱状图

**优先级**: 🟡 中  
**预计工作量**: 4-5 小时  
**依赖**: K线图组件完成

---

### 5. 数据持久化

#### ❌ F-07: Supabase 连接修复
**PRD 要求**: (隐含需求)
- 任务记录持久化
- 筛选结果持久化
- 历史记录查询

**当前状态**:
- ✅ 代码框架已实现
- ❌ Supabase 连接失败
- ⚠️ 使用内存存储替代

**待完成**:
```bash
# 修复 Supabase 版本兼容性
cd stockguru-web/backend
source venv/bin/activate

# 方案1: 升级 httpx
pip install httpx==0.27.0

# 方案2: 使用 supabase-py
pip uninstall supabase
pip install supabase-py

# 测试连接
python -c "from app.core.supabase import get_supabase_client; print(get_supabase_client())"
```

**优先级**: 🔴 高  
**预计工作量**: 1-2 小时  
**依赖**: 版本兼容性测试

---

### 6. 历史记录功能

#### ❌ F-08: 历史记录查询
**PRD 要求**: (Web 版新增)
- 查看历史筛选记录
- 对比不同日期的结果
- 筛选结果趋势分析

**当前状态**:
- ✅ 后端 API 已实现 (`list_screenings`)
- ❌ 前端页面未实现

**待完成**:
```typescript
// 创建历史记录页面
// app/history/page.tsx
function HistoryPage() {
  const [tasks, setTasks] = useState([])
  
  return (
    <div>
      <h1>历史记录</h1>
      <TaskList tasks={tasks} />
    </div>
  )
}
```

**优先级**: 🟡 中  
**预计工作量**: 3-4 小时  
**依赖**: Supabase 连接修复

---

### 7. 非功能性需求

#### ❌ F-09: 性能优化
**PRD 要求**:
- 数据获取和计算在 2 分钟内完成

**当前状态**:
- ⚠️ 模拟数据约 8 秒
- ❓ 真实数据性能未测试

**待完成**:
1. **并发数据获取**
```python
import asyncio

async def fetch_all_data(stocks):
    tasks = [fetch_kline(stock) for stock in stocks]
    return await asyncio.gather(*tasks)
```

2. **数据缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_stock_data(code, date):
    # 缓存当日数据
    pass
```

**优先级**: 🟡 中  
**预计工作量**: 2-3 小时  
**依赖**: 真实数据集成完成

---

#### ❌ F-10: 易用性改进
**PRD 要求**:
- 简单的命令行接口或图形界面

**当前状态**:
- ✅ Web 图形界面
- ✅ 一键启动脚本
- ❌ 缺少命令行工具

**待完成**:
```python
# 创建 CLI 工具
# cli.py
import click

@click.command()
@click.option('--date', default='today', help='筛选日期')
@click.option('--top-n', default=10, help='筛选数量')
def screen(date, top_n):
    """运行股票筛选"""
    click.echo(f'开始筛选 {date} 的股票...')
    # 执行筛选逻辑
```

**优先级**: 🟢 低  
**预计工作量**: 2-3 小时  
**依赖**: 无

---

## ✅ 已完成需求

### 1. 核心筛选算法 ✅
- ✅ F-02: 综合评分与初选
  - Min-Max 标准化
  - 交集计算
  - 综合评分排序

### 2. 参数配置 ✅
- ✅ F-04: 参数可配置
  - VOLUME_TOP_N
  - HOT_TOP_N
  - FINAL_TOP_N
  - MOMENTUM_DAYS
  - MOMENTUM_TOP_N

### 3. Web 界面 ✅
- ✅ 一键筛选按钮
- ✅ 实时进度显示
- ✅ 结果表格展示
- ✅ 响应式设计

### 4. 后台任务 ✅
- ✅ 异步任务处理
- ✅ 进度追踪
- ✅ 错误处理

---

## 📅 开发计划

### 第一阶段：核心功能完善 (优先级：高)
**预计时间**: 1-2 周

1. **修复 Supabase 连接** (1-2 小时)
   - 升级依赖版本
   - 测试连接

2. **集成真实数据源** (4-6 小时)
   - pywencai API 调用
   - akshare K线数据
   - 错误处理和重试

3. **真实动量计算** (2-3 小时)
   - 获取真实 K线
   - 线性回归计算
   - 结果验证

**里程碑**: 完整的筛选流程可用真实数据运行

---

### 第二阶段：可视化增强 (优先级：中)
**预计时间**: 1-2 周

1. **K线图表组件** (4-6 小时)
   - 选择图表库
   - 实现 K线图
   - 添加均线

2. **股票详情页** (4-5 小时)
   - 页面布局
   - 详细指标
   - 技术分析

3. **历史记录页面** (3-4 小时)
   - 列表展示
   - 筛选和排序
   - 详情查看

**里程碑**: 完整的可视化复盘体验

---

### 第三阶段：功能扩展 (优先级：低)
**预计时间**: 2-3 周

1. **HTML 报告导出** (3-4 小时)
2. **命令行工具** (2-3 小时)
3. **性能优化** (2-3 小时)
4. **更多技术指标** (4-6 小时)

**里程碑**: 功能完整的产品

---

## 🎯 优先级排序

### 🔴 高优先级 (必须完成)
1. ✅ Supabase 连接修复
2. ✅ 真实数据源集成 (pywencai + akshare)
3. ✅ 真实动量计算

### 🟡 中优先级 (重要但不紧急)
4. ✅ K线图表展示
5. ✅ 股票详情页
6. ✅ 历史记录功能
7. ✅ 性能优化

### 🟢 低优先级 (锦上添花)
8. ✅ HTML 报告导出
9. ✅ 命令行工具
10. ✅ 更多技术指标

---

## 📊 工作量估算

| 阶段 | 任务数 | 预计时间 | 完成后功能 |
|------|--------|----------|-----------|
| 第一阶段 | 3 | 1-2 周 | 真实数据筛选 |
| 第二阶段 | 3 | 1-2 周 | 完整可视化 |
| 第三阶段 | 4 | 2-3 周 | 功能完善 |
| **总计** | **10** | **4-7 周** | **完整产品** |

---

## 🎉 总结

### 当前状态
- ✅ 基础架构完成 (100%)
- ✅ 核心算法实现 (100%)
- ⚠️ 真实数据集成 (0%)
- ⚠️ 可视化图表 (40%)
- ✅ Web 界面 (80%)

### 下一步行动
1. **立即开始**: 修复 Supabase 连接
2. **本周完成**: 集成真实数据源
3. **下周完成**: K线图表展示

### 最终目标
**打造一个完整的、可用的、高效的股票短线复盘助手！**

---

**创建时间**: 2025-10-15 00:16  
**最后更新**: 2025-10-15 00:16  
**维护者**: Cascade
