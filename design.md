### **股票短线复盘助手 - 技术设计文档 (TDD)**

| **文档版本** | **V1.0** | **创建日期** | 2025年10月14日 |
| :--- | :--- | :--- | :--- |
| **创建人** | Cascade | **关联文档** | prd.md |

---

## 1. 技术架构概览

### 1.1 整体架构
本项目采用**前后端分离**的设计思路，但输出为**静态 HTML 文件**，无需运行时服务器。

```
┌─────────────────────────────────────────────────────────────┐
│                       用户交互层                              │
│                  (浏览器打开 HTML 文件)                       │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       展示层                                  │
│          HTML (Jinja2 模板) + CSS + JavaScript               │
│              交互式图表 (Pyecharts/Plotly)                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       业务逻辑层                              │
│         数据筛选 + 综合评分 + 动量计算 (Python)               │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       数据访问层                              │
│            pywencai (热度/成交额) + akshare (行情)            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 层级 | 技术栈 | 用途 | 版本要求 |
| :--- | :--- | :--- | :--- |
| **运行环境** | Python | 核心开发语言 | ≥ 3.8 |
| **数据源** | pywencai | 获取成交额排名、热度排名 | latest |
| **数据源** | akshare | 获取日线行情、股票基本信息 | latest |
| **数据处理** | pandas | 数据清洗、筛选、排序 | ≥ 1.3.0 |
| **数据处理** | numpy | 数值计算 | ≥ 1.20.0 |
| **机器学习** | scikit-learn | 线性回归计算动量 | ≥ 0.24.0 |
| **模板引擎** | Jinja2 | 生成 HTML 页面 | ≥ 3.0.0 |
| **图表库** | pyecharts | 绘制 K线图和技术指标 | ≥ 2.0.0 |
| **日期处理** | python-dateutil | 交易日计算 | ≥ 2.8.0 |

---

## 2. 系统模块设计

### 2.1 项目目录结构

```
StockGuru/
├── prd.md                      # 产品需求文档
├── design.md                   # 技术设计文档 (本文件)
├── requirements.txt            # Python 依赖清单
├── config.py                   # 配置参数
├── main.py                     # 主程序入口
├── modules/                    # 核心模块目录
│   ├── __init__.py
│   ├── data_fetcher.py        # 数据获取模块
│   ├── stock_filter.py        # 股票筛选模块
│   ├── momentum_calculator.py # 动量计算模块
│   └── report_generator.py    # 报告生成模块
├── templates/                  # HTML 模板目录
│   └── report_template.html   # 报告页面模板
├── static/                     # 静态资源目录
│   └── style.css              # 自定义样式
├── output/                     # 输出目录
│   └── report_YYYYMMDD.html   # 生成的报告文件
└── data/                       # 数据缓存目录 (可选)
    └── cache/                 # 临时数据缓存
```

### 2.2 核心模块详细设计

#### 2.2.1 配置模块 (`config.py`)

**职责**: 集中管理所有可配置参数

```python
# 筛选参数
VOLUME_TOP_N = 100          # 成交额排名范围
HOT_TOP_N = 100             # 热度排名范围
FINAL_TOP_N = 30            # 综合评分取前N名
MOMENTUM_DAYS = 25          # 动量计算周期(天)
MOMENTUM_TOP_N = 10         # 最终筛选数量

# 综合评分权重
WEIGHT_VOLUME = 0.5         # 成交额权重
WEIGHT_HOT = 0.5            # 热度权重

# 过滤规则
EXCLUDE_ST = True           # 是否排除ST股
EXCLUDE_NEW_STOCK_DAYS = 60 # 排除上市N天内的次新股
MAX_RISE_RATIO = 1.0        # 排除N天内涨幅超过100%的股票

# 图表配置
MA_PERIODS = [5, 10, 20]    # 均线周期
CHART_WIDTH = "100%"        # 图表宽度
CHART_HEIGHT = "500px"      # 图表高度

# 输出配置
OUTPUT_DIR = "./output"     # 报告输出目录
TEMPLATE_DIR = "./templates" # 模板目录
```

---

#### 2.2.2 数据获取模块 (`modules/data_fetcher.py`)

**职责**: 封装所有外部数据源的访问逻辑

**核心类**: `DataFetcher`

**主要方法**:

| 方法名 | 输入参数 | 返回值 | 功能描述 |
| :--- | :--- | :--- | :--- |
| `get_volume_top_stocks(date, top_n)` | 日期, 排名数量 | DataFrame | 获取成交额排名前N的股票 |
| `get_hot_top_stocks(date, top_n)` | 日期, 排名数量 | DataFrame | 获取热度排名前N的股票 |
| `get_stock_daily_data(code, days)` | 股票代码, 天数 | DataFrame | 获取指定股票的日线行情 |
| `get_stock_info(code)` | 股票代码 | Dict | 获取股票基本信息(名称、行业等) |

**实现要点**:
- 使用 `pywencai.get()` 获取成交额和热度数据
- 使用 `akshare.stock_zh_a_hist()` 获取日线行情
- 实现数据缓存机制，避免重复请求
- 异常处理：网络超时、数据缺失等

**伪代码示例**:
```python
import pywencai
import akshare as ak
import pandas as pd

class DataFetcher:
    def get_volume_top_stocks(self, date, top_n):
        """获取成交额排名前N的股票"""
        query = f'{date}成交额前{top_n}'
        df = pywencai.get(query=query)
        # 数据清洗和标准化
        return df
    
    def get_hot_top_stocks(self, date, top_n):
        """获取热度排名前N的股票"""
        query = f'{date}个股热度前{top_n}'
        df = pywencai.get(query=query)
        return df
    
    def get_stock_daily_data(self, code, days):
        """获取股票日线数据"""
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        return df.tail(days)
```

---

#### 2.2.3 股票筛选模块 (`modules/stock_filter.py`)

**职责**: 实现股票筛选的核心算法

**核心类**: `StockFilter`

**主要方法**:

| 方法名 | 输入参数 | 返回值 | 功能描述 |
| :--- | :--- | :--- | :--- |
| `find_common_stocks(volume_df, hot_df)` | 成交额DF, 热度DF | Set | 找出两个股池的交集 |
| `min_max_normalize(data)` | 数据序列 | Array | Min-Max标准化 |
| `calculate_comprehensive_score(stocks)` | 股票列表 | DataFrame | 计算综合评分 |
| `apply_filters(stocks)` | 股票列表 | DataFrame | 应用过滤规则 |

**核心算法**:

**1. 综合评分算法**
```
标准化成交额 = (成交额 - min) / (max - min)
标准化热度 = (热度 - min) / (max - min)
综合评分 = WEIGHT_VOLUME × 标准化成交额 + WEIGHT_HOT × 标准化热度
```

**2. 过滤规则**
- 排除 ST、*ST 股票（股票名称包含"ST"）
- 排除上市不足 N 天的次新股
- 排除 N 天内涨幅超过阈值的股票

**伪代码示例**:
```python
class StockFilter:
    def calculate_comprehensive_score(self, volume_df, hot_df):
        """计算综合评分"""
        # 找交集
        common_codes = set(volume_df['股票代码']) & set(hot_df['股票代码'])
        
        # 标准化
        volume_norm = self.min_max_normalize(volume_df['成交额'])
        hot_norm = self.min_max_normalize(hot_df['热度'])
        
        # 加权计算
        score = WEIGHT_VOLUME * volume_norm + WEIGHT_HOT * hot_norm
        
        # 排序并取前N名
        return df.nlargest(FINAL_TOP_N, 'score')
    
    def apply_filters(self, stocks_df):
        """应用过滤规则"""
        # 排除ST股
        if EXCLUDE_ST:
            stocks_df = stocks_df[~stocks_df['股票名称'].str.contains('ST')]
        
        # 排除次新股
        # ... 其他过滤逻辑
        
        return stocks_df
```

---

#### 2.2.4 动量计算模块 (`modules/momentum_calculator.py`)

**职责**: 计算股票的动量得分

**核心类**: `MomentumCalculator`

**主要方法**:

| 方法名 | 输入参数 | 返回值 | 功能描述 |
| :--- | :--- | :--- | :--- |
| `calculate_momentum(price_series)` | 价格序列 | Float | 计算单只股票的动量分 |
| `batch_calculate(stocks)` | 股票列表 | DataFrame | 批量计算动量分 |

**核心算法**: 线性回归动量

```
1. 获取过去 N 天的收盘价序列
2. 计算相对价格: relative_price = price / price[0]
3. 对相对价格进行线性回归
4. 动量分 = 斜率 × R² × 10000
```

**数学原理**:
- **斜率 (slope)**: 衡量价格上涨的速度
- **R² (决定系数)**: 衡量趋势的稳定性 (0-1之间，越接近1越稳定)
- **乘以10000**: 放大数值，便于比较

**伪代码示例**:
```python
from sklearn.linear_model import LinearRegression
import numpy as np

class MomentumCalculator:
    def calculate_momentum(self, price_series):
        """计算动量得分"""
        # 计算相对价格
        relative_prices = price_series / price_series.iloc[0]
        
        # 准备回归数据
        x = np.arange(len(relative_prices)).reshape(-1, 1)
        y = relative_prices.values
        
        # 线性回归
        lr = LinearRegression()
        lr.fit(x, y)
        
        # 计算动量分
        slope = lr.coef_[0]
        r_squared = lr.score(x, y)
        momentum_score = 10000 * slope * r_squared
        
        return momentum_score
```

---

#### 2.2.5 报告生成模块 (`modules/report_generator.py`)

**职责**: 生成可视化 HTML 报告

**核心类**: `ReportGenerator`

**主要方法**:

| 方法名 | 输入参数 | 返回值 | 功能描述 |
| :--- | :--- | :--- | :--- |
| `generate_kline_chart(stock_data)` | 股票数据 | Chart对象 | 生成K线图 |
| `generate_report(stocks)` | 股票列表 | HTML文件路径 | 生成完整报告 |

**K线图配置**:
- 显示最近 60 个交易日的数据
- 包含 MA5、MA10、MA20 均线
- 成交量柱状图
- 交互式缩放、数据提示

**页面布局**:
```
┌────────────────────────────────────────────┐
│           股票短线复盘报告                   │
│        生成日期: 2025-10-14                 │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ 排名1: 股票代码 - 股票名称                   │
│ 动量得分: 85.6  |  所属行业: 半导体          │
│ ┌──────────────────────────────────────┐   │
│ │         K线图 + 均线 + 成交量          │   │
│ │                                      │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│ 排名2: ...                                 │
└────────────────────────────────────────────┘
```

**伪代码示例**:
```python
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from jinja2 import Environment, FileSystemLoader

class ReportGenerator:
    def generate_kline_chart(self, stock_data):
        """生成K线图"""
        kline = (
            Kline()
            .add_xaxis(stock_data['日期'].tolist())
            .add_yaxis("K线", stock_data[['开盘', '收盘', '最低', '最高']].values.tolist())
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{stock_data['名称']}"),
                xaxis_opts=opts.AxisOpts(is_scale=True),
                yaxis_opts=opts.AxisOpts(is_scale=True),
            )
        )
        
        # 添加均线
        for period in MA_PERIODS:
            ma_line = Line().add_xaxis(...).add_yaxis(f"MA{period}", ...)
            kline.overlap(ma_line)
        
        return kline
    
    def generate_report(self, stocks_data):
        """生成HTML报告"""
        # 为每只股票生成图表
        charts = []
        for stock in stocks_data:
            chart = self.generate_kline_chart(stock)
            charts.append(chart.render_embed())
        
        # 使用Jinja2渲染模板
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template('report_template.html')
        
        html_content = template.render(
            date=datetime.now().strftime('%Y-%m-%d'),
            stocks=stocks_data,
            charts=charts
        )
        
        # 保存文件
        output_path = f"{OUTPUT_DIR}/report_{datetime.now().strftime('%Y%m%d')}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
```

---

## 3. 主程序流程 (`main.py`)

### 3.1 执行流程图

```
开始
  │
  ├─→ 读取配置参数 (config.py)
  │
  ├─→ 初始化数据获取器 (DataFetcher)
  │
  ├─→ 获取成交额Top100 + 热度Top100
  │
  ├─→ 股票筛选 (StockFilter)
  │    ├─ 找交集
  │    ├─ 计算综合评分
  │    ├─ 应用过滤规则
  │    └─ 取前30名
  │
  ├─→ 动量计算 (MomentumCalculator)
  │    ├─ 获取每只股票的历史行情
  │    ├─ 计算动量得分
  │    └─ 排序取前10名
  │
  ├─→ 报告生成 (ReportGenerator)
  │    ├─ 生成K线图
  │    ├─ 渲染HTML模板
  │    └─ 保存文件
  │
  └─→ 输出报告路径，完成
```

### 3.2 主程序伪代码

```python
from modules.data_fetcher import DataFetcher
from modules.stock_filter import StockFilter
from modules.momentum_calculator import MomentumCalculator
from modules.report_generator import ReportGenerator
from config import *
from datetime import datetime

def main():
    print("=" * 50)
    print("股票短线复盘助手 V1.0")
    print("=" * 50)
    
    # 1. 初始化
    fetcher = DataFetcher()
    filter = StockFilter()
    calculator = MomentumCalculator()
    generator = ReportGenerator()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 2. 数据获取
    print(f"\n[1/4] 正在获取 {today} 的市场数据...")
    volume_df = fetcher.get_volume_top_stocks(today, VOLUME_TOP_N)
    hot_df = fetcher.get_hot_top_stocks(today, HOT_TOP_N)
    print(f"✓ 成交额Top{VOLUME_TOP_N}: {len(volume_df)} 只")
    print(f"✓ 热度Top{HOT_TOP_N}: {len(hot_df)} 只")
    
    # 3. 综合筛选
    print(f"\n[2/4] 正在进行综合评分筛选...")
    candidates = filter.calculate_comprehensive_score(volume_df, hot_df)
    candidates = filter.apply_filters(candidates)
    print(f"✓ 初选池: {len(candidates)} 只")
    
    # 4. 动量计算
    print(f"\n[3/4] 正在计算动量得分...")
    final_stocks = calculator.batch_calculate(candidates)
    final_stocks = final_stocks.nlargest(MOMENTUM_TOP_N, 'momentum_score')
    print(f"✓ 最终筛选: {len(final_stocks)} 只")
    
    # 5. 生成报告
    print(f"\n[4/4] 正在生成可视化报告...")
    report_path = generator.generate_report(final_stocks)
    print(f"✓ 报告已生成: {report_path}")
    
    print("\n" + "=" * 50)
    print("复盘完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()
```

---

## 4. HTML 模板设计 (`templates/report_template.html`)

### 4.1 模板结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票短线复盘报告 - {{ date }}</title>
    <link rel="stylesheet" href="../static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
</head>
<body>
    <!-- 页面头部 -->
    <header>
        <h1>📈 股票短线复盘报告</h1>
        <p class="date">生成日期: {{ date }}</p>
    </header>
    
    <!-- 股票列表 -->
    <main>
        {% for stock in stocks %}
        <div class="stock-card">
            <div class="stock-header">
                <h2>排名 {{ loop.index }}: {{ stock.code }} - {{ stock.name }}</h2>
                <div class="metrics">
                    <span class="momentum">动量得分: {{ stock.momentum_score | round(2) }}</span>
                    <span class="industry">行业: {{ stock.industry }}</span>
                </div>
            </div>
            <div class="chart-container">
                {{ charts[loop.index0] | safe }}
            </div>
        </div>
        {% endfor %}
    </main>
    
    <!-- 页面底部 -->
    <footer>
        <p>⚠️ 本报告仅供复盘参考，不构成投资建议。市场有风险，投资需谨慎。</p>
    </footer>
</body>
</html>
```

### 4.2 样式设计要点 (`static/style.css`)

- 使用现代化的卡片式布局
- 响应式设计，支持移动端查看
- 清晰的视觉层次：标题 > 指标 > 图表
- 配色方案：专业、简洁、护眼

---

## 5. 数据流设计

### 5.1 数据流转图

```
外部数据源
    │
    ├─→ pywencai API
    │      └─→ 成交额排名、热度排名 (JSON)
    │
    └─→ akshare API
           └─→ 日线行情、股票信息 (DataFrame)
                  │
                  ▼
            DataFetcher (数据获取)
                  │
                  ├─→ 原始数据 (DataFrame)
                  │
                  ▼
            StockFilter (数据筛选)
                  │
                  ├─→ 候选股池 (DataFrame)
                  │
                  ▼
            MomentumCalculator (动量计算)
                  │
                  ├─→ 最终股票列表 + 动量分 (DataFrame)
                  │
                  ▼
            ReportGenerator (报告生成)
                  │
                  ├─→ HTML 字符串
                  │
                  ▼
            输出文件 (report_YYYYMMDD.html)
```

---

## 6. 异常处理与容错

### 6.1 异常场景

| 异常场景 | 处理策略 |
| :--- | :--- |
| 网络请求失败 | 重试3次，失败后提示用户检查网络 |
| 数据源返回空数据 | 记录日志，跳过该股票，继续处理其他 |
| 股票代码无效 | 过滤掉无效代码，记录警告 |
| 模板文件缺失 | 抛出异常，提示用户检查项目完整性 |
| 输出目录不存在 | 自动创建目录 |

### 6.2 日志设计

使用 Python 标准库 `logging` 记录关键信息：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('stockguru.log'),
        logging.StreamHandler()
    ]
)
```

---

## 7. 性能优化

### 7.1 优化策略

| 优化点 | 策略 | 预期效果 |
| :--- | :--- | :--- |
| 数据获取 | 使用本地缓存，避免重复请求 | 减少50%网络请求 |
| 并发处理 | 使用线程池并发获取多只股票数据 | 提速3-5倍 |
| 数据计算 | 使用 numpy 向量化计算 | 提速10倍以上 |
| 图表渲染 | 延迟加载，按需渲染 | 减少内存占用 |

### 7.2 性能指标

- 数据获取: ≤ 30秒
- 数据处理: ≤ 10秒
- 报告生成: ≤ 20秒
- **总耗时: ≤ 60秒**

---

## 8. 测试计划

### 8.1 单元测试

| 模块 | 测试用例 |
| :--- | :--- |
| `data_fetcher.py` | 测试数据获取的正确性和异常处理 |
| `stock_filter.py` | 测试筛选算法的准确性 |
| `momentum_calculator.py` | 测试动量计算的数学正确性 |
| `report_generator.py` | 测试HTML生成的完整性 |

### 8.2 集成测试

- 端到端测试：从数据获取到报告生成的完整流程
- 边界测试：空数据、极端数据的处理
- 性能测试：大数据量下的执行时间

---

## 9. 部署与使用

### 9.1 安装步骤

```bash
# 1. 克隆项目
git clone <repository_url>
cd StockGuru

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py
```

### 9.2 使用说明

1. 运行 `python main.py`
2. 等待程序执行完成（约1-2分钟）
3. 在 `output/` 目录下找到生成的 HTML 文件
4. 双击打开，即可在浏览器中查看复盘报告

### 9.3 参数调整

编辑 `config.py` 文件，修改相关参数后重新运行即可。

---

## 10. 未来扩展方向

### 10.1 V2.0 功能规划

- **回测功能**: 验证策略的历史表现
- **多策略支持**: 允许用户选择不同的筛选策略
- **实时监控**: 盘中实时更新强势股列表
- **消息推送**: 通过邮件或微信推送报告

### 10.2 技术演进

- 引入数据库存储历史数据
- 开发 Web 版本，支持在线访问
- 集成更多数据源和技术指标

---

## 附录

### A. 依赖清单 (`requirements.txt`)

```
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=0.24.0
pywencai
akshare
pyecharts>=2.0.0
jinja2>=3.0.0
python-dateutil>=2.8.0
```

### B. 参考资料

- Pyecharts 官方文档: https://pyecharts.org/
- Akshare 官方文档: https://akshare.akfamily.xyz/
- Jinja2 官方文档: https://jinja.palletsprojects.com/

---

**文档结束**
