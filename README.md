# 📈 StockGuru - 股票短线复盘助手

一款基于 Python 的股票短线复盘工具，自动筛选强势股并生成可视化报告。

## ✨ 核心功能

- **智能筛选**: 从全市场自动筛选出兼具"资金"和"人气"的强势股
- **动量评分**: 基于线性回归算法计算股票动量得分
- **可视化报告**: 一键生成包含K线图和技术指标的HTML报告
- **参数可配置**: 所有筛选参数均可自定义调整

## 🎯 筛选逻辑

1. **数据获取**: 获取成交额Top100 + 热度Top100
2. **综合评分**: 取交集并进行Min-Max标准化，计算综合得分
3. **初选**: 根据综合评分筛选出前30名
4. **动量计算**: 计算25日动量得分（斜率 × R²）
5. **终选**: 按动量得分排序，筛选出前10名强势股

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
# 克隆项目
cd StockGuru

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

程序执行完成后，会在 `output/` 目录下生成HTML报告文件，双击即可在浏览器中查看。

## ⚙️ 配置说明

编辑 `config.py` 文件可以调整筛选参数：

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
```

## 📁 项目结构

```
StockGuru/
├── prd.md                      # 产品需求文档
├── design.md                   # 技术设计文档
├── requirements.txt            # Python 依赖清单
├── config.py                   # 配置参数
├── main.py                     # 主程序入口
├── modules/                    # 核心模块目录
│   ├── data_fetcher.py        # 数据获取模块
│   ├── stock_filter.py        # 股票筛选模块
│   ├── momentum_calculator.py # 动量计算模块
│   └── report_generator.py    # 报告生成模块
├── templates/                  # HTML 模板目录
│   └── report_template.html   # 报告页面模板
├── output/                     # 输出目录
└── data/                       # 数据缓存目录
```

## 📊 报告示例

生成的报告包含：

- 报告生成日期
- 筛选出的股票列表（按动量得分排序）
- 每只股票的详细信息：
  - 股票代码和名称
  - 动量得分
  - K线图（含MA5、MA10、MA20均线）
  - 成交量柱状图

## ⚠️ 免责声明

本工具仅供学习和复盘参考使用，不构成任何投资建议。

- 筛选结果仅供参考
- 技术分析有滞后性，需结合基本面和消息面
- 短线风险较高，请合理控制仓位
- 市场有风险，投资需谨慎

## 📝 开发日志

- **V1.0** (2025-10-14)
  - 实现核心筛选功能
  - 实现动量计算算法
  - 实现可视化报告生成

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**记住**: 工具是死的，人是活的。这套助手能大大提升你的效率，但最终的交易决策，还是要靠你自己的判断和经验。
