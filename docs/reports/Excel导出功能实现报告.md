# Excel 导出功能实现报告

**实现时间**: 2025-10-15 03:57  
**功能**: 导出筛选报告为 Excel 文件

---

## ✨ 功能概述

实现了专业的 Excel 格式报告导出功能，用户可以下载 `.xlsx` 文件进行数据分析和处理。

### 功能特点
- 📊 **Excel 格式**: 标准的 .xlsx 文件，兼容所有 Office 软件
- 🎨 **专业样式**: 精美的表格样式和颜色标识
- 📈 **数据完整**: 包含所有筛选结果和关键指标
- 🔢 **便于分析**: 可直接在 Excel 中进行数据分析和图表制作
- 💾 **自动下载**: 点击按钮自动下载文件

---

## 🛠️ 技术实现

### 1. 后端实现

#### 使用库
- **openpyxl**: Python 的 Excel 文件操作库
- 已安装，无需额外系统依赖

#### API 端点
**端点**: `GET /api/v1/screening/{task_id}/export/excel`

**功能**: 生成并返回 Excel 文件

**流程**:
```python
1. 获取任务结果
2. 创建 Excel 工作簿
3. 设置样式（字体、颜色、边框）
4. 添加标题和表头
5. 填充数据
6. 应用条件格式（涨跌幅颜色）
7. 返回文件流
```

### 2. Excel 样式设计

#### 标题行
- 背景色: 蓝色 (#2563EB)
- 字体: 微软雅黑 16号 粗体 白色
- 合并单元格: A1:H1
- 内容: "📈 StockGuru 股票筛选报告"

#### 信息行
- 合并单元格: A2:H2
- 内容: 生成时间和筛选结果数量
- 居中对齐

#### 表头
- 背景色: 灰色 (#E5E7EB)
- 字体: 微软雅黑 11号 粗体
- 居中对齐
- 边框: 全边框

#### 数据行
- 字体: 默认
- 居中对齐
- 边框: 全边框
- **涨跌幅颜色**:
  - 上涨: 红色 (#FF0000) 粗体
  - 下跌: 绿色 (#00B050) 粗体

### 3. 列宽设置

| 列 | 宽度 | 说明 |
|----|------|------|
| A (排名) | 8 | 数字 |
| B (股票代码) | 12 | 6位代码 |
| C (股票名称) | 15 | 中文名称 |
| D (动量分数) | 12 | 小数 |
| E (综合评分) | 12 | 小数 |
| F (最新价) | 10 | 价格 |
| G (涨跌幅) | 10 | 百分比 |
| H (成交量) | 15 | 大数字 |

---

## 📝 Excel 文件结构

```
┌─────────────────────────────────────────────────────────┐
│  📈 StockGuru 股票筛选报告                               │  (蓝色背景)
├─────────────────────────────────────────────────────────┤
│  生成时间: 2025-10-15 03:57:00  |  筛选结果: 共 10 只股票 │
├────┬─────────┬──────────┬──────────┬──────────┬────────┤
│排名│股票代码 │股票名称  │动量分数  │综合评分  │最新价  │... (灰色背景)
├────┼─────────┼──────────┼──────────┼──────────┼────────┤
│ 1  │ 601212  │ 白银有色 │  85.23   │  0.8765  │  5.53  │...
├────┼─────────┼──────────┼──────────┼──────────┼────────┤
│ 2  │ 000001  │ 平安银行 │  78.45   │  0.8234  │ 12.34  │...
├────┼─────────┼──────────┼──────────┼──────────┼────────┤
│ ...│   ...   │   ...    │   ...    │   ...    │  ...   │...
└────┴─────────┴──────────┴──────────┴──────────┴────────┘

⚠️ 免责声明: 本报告仅供参考，不构成任何投资建议。市场有风险，投资需谨慎。
```

---

## 🎯 使用方法

### 1. 完成筛选任务
在首页进行股票筛选，等待任务完成（进度 100%）

### 2. 导出 Excel
在筛选结果区域，点击"📊 Excel报告"按钮

### 3. 下载文件
浏览器会自动下载 Excel 文件：
```
stockguru_report_20251015_035700.xlsx
```

### 4. 打开文件
使用以下任一软件打开：
- Microsoft Excel
- WPS Office
- LibreOffice Calc
- Google Sheets
- Apple Numbers

---

## 📊 数据列说明

| 列名 | 数据类型 | 说明 | 示例 |
|------|---------|------|------|
| 排名 | 整数 | 最终排名 | 1, 2, 3... |
| 股票代码 | 文本 | 6位数字代码 | 601212 |
| 股票名称 | 文本 | 中文名称 | 白银有色 |
| 动量分数 | 小数 | 动量得分 (2位小数) | 85.23 |
| 综合评分 | 小数 | 综合评分 (4位小数) | 0.8765 |
| 最新价 | 小数 | 收盘价 (2位小数) | 5.53 |
| 涨跌幅 | 小数 | 涨跌百分比 (2位小数) | +4.39 |
| 成交量 | 整数 | 成交量 | 12345678 |

---

## 💡 Excel 使用技巧

### 1. 数据排序
- 选中数据区域
- 点击"数据" → "排序"
- 选择排序列（如按动量分数降序）

### 2. 数据筛选
- 选中表头行
- 点击"数据" → "筛选"
- 使用下拉箭头筛选数据

### 3. 创建图表
- 选中数据
- 点击"插入" → "图表"
- 选择图表类型（柱状图、折线图等）

### 4. 条件格式
- 选中数据列
- 点击"开始" → "条件格式"
- 设置规则（如高亮显示前3名）

### 5. 数据透视表
- 选中所有数据
- 点击"插入" → "数据透视表"
- 进行多维度分析

---

## 🎨 样式特点

### 1. 颜色方案
- **标题**: 蓝色主题 (#2563EB)
- **表头**: 浅灰色 (#E5E7EB)
- **上涨**: 红色 (#FF0000)
- **下跌**: 绿色 (#00B050)

### 2. 字体
- **中文**: 微软雅黑
- **数字**: 默认（Calibri）
- **标题**: 16号粗体
- **表头**: 11号粗体
- **数据**: 11号常规

### 3. 对齐方式
- **标题**: 居中
- **表头**: 居中
- **数据**: 居中
- **免责声明**: 居中

---

## 🔧 技术细节

### openpyxl 核心代码

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# 创建工作簿
wb = Workbook()
ws = wb.active

# 设置样式
title_font = Font(name='微软雅黑', size=16, bold=True, color='FFFFFF')
title_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')

# 添加数据
ws['A1'] = '标题'
ws['A1'].font = title_font
ws['A1'].fill = title_fill

# 保存到内存
excel_buffer = io.BytesIO()
wb.save(excel_buffer)
excel_buffer.seek(0)

# 返回文件
return Response(
    content=excel_buffer.getvalue(),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    headers={"Content-Disposition": f"attachment; filename={filename}"}
)
```

### 条件格式实现

```python
# 涨跌幅颜色
if col == 7:  # 涨跌幅列
    change_pct = stock.get('change_pct', 0)
    if change_pct > 0:
        cell.font = Font(color='FF0000', bold=True)  # 红色
    elif change_pct < 0:
        cell.font = Font(color='00B050', bold=True)  # 绿色
```

---

## 📝 修改文件清单

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `stockguru-web/backend/app/api/screening.py` | 添加 Excel 导出 API | ✅ 已实现 |
| `frontend/app/page.tsx` | 更新导出按钮 | ✅ 已实现 |

---

## ⚠️ 注意事项

### 1. 文件大小
- 10只股票: ~10 KB
- 30只股票: ~15 KB
- 100只股票: ~30 KB

### 2. 兼容性
- ✅ Excel 2007 及以上版本
- ✅ WPS Office
- ✅ LibreOffice 4.0+
- ✅ Google Sheets (上传后)
- ⚠️ Excel 2003 (需要转换)

### 3. 中文字体
- Windows: 微软雅黑自动可用
- macOS: 需要安装微软雅黑或使用系统字体
- Linux: 需要安装中文字体

---

## 🚀 未来优化

### 1. 多工作表
```python
# 添加第二个工作表：详细数据
ws2 = wb.create_sheet("详细数据")
# 添加K线数据、技术指标等
```

### 2. 图表嵌入
```python
from openpyxl.chart import BarChart, Reference

# 创建柱状图
chart = BarChart()
data = Reference(ws, min_col=4, min_row=3, max_row=13)
chart.add_data(data, titles_from_data=True)
ws.add_chart(chart, "J5")
```

### 3. 数据验证
```python
from openpyxl.worksheet.datavalidation import DataValidation

# 添加下拉列表
dv = DataValidation(type="list", formula1='"优秀,良好,一般"')
ws.add_data_validation(dv)
```

### 4. 公式支持
```python
# 添加计算公式
ws['I4'] = '=D4*E4'  # 动量分数 × 综合评分
```

---

## 📊 功能对比

| 特性 | HTML报告 | Excel报告 |
|------|----------|----------|
| 查看方式 | 浏览器 | Excel软件 ✅ |
| 数据分析 | 不支持 | 完全支持 ✅ |
| 排序筛选 | 不支持 | 完全支持 ✅ |
| 图表制作 | 不支持 | 完全支持 ✅ |
| 数据导出 | 需复制 | 直接使用 ✅ |
| 打印效果 | 一般 | 优秀 ✅ |
| 文件大小 | 小 | 小 ✅ |
| 专业性 | 一般 | 专业 ✅ |

---

## ✅ 测试验证

### 1. API 测试
```bash
# 测试 Excel 导出
curl -O "http://localhost:8000/api/v1/screening/{task_id}/export/excel"

# 检查文件
file stockguru_report_*.xlsx
# 输出: Microsoft Excel 2007+
```

### 2. 前端测试
1. 完成一次筛选
2. 点击"📊 Excel报告"按钮
3. 验证文件自动下载
4. 用 Excel 打开检查内容和样式

### 3. 数据验证
- ✅ 所有数据正确
- ✅ 样式完整
- ✅ 颜色正确
- ✅ 中文显示正常

---

## 📚 相关资源

### 文档
- [openpyxl 官方文档](https://openpyxl.readthedocs.io/)
- [Excel 文件格式规范](https://docs.microsoft.com/en-us/openspecs/office_standards/)
- [Python Excel 教程](https://realpython.com/openpyxl-excel-spreadsheets-python/)

### 工具
- [Excel Viewer](https://www.microsoft.com/en-us/microsoft-365/excel)
- [WPS Office](https://www.wps.com/)
- [LibreOffice](https://www.libreoffice.org/)

---

## 📝 总结

### 已实现
- ✅ Excel 文件生成
- ✅ 专业样式设计
- ✅ 条件格式（涨跌幅颜色）
- ✅ 自动下载
- ✅ 完整数据导出

### 优势
- 📊 专业的数据分析工具
- 🎨 精美的样式设计
- 🔢 便于二次处理
- 💾 标准文件格式
- 🚀 零依赖，纯 Python

### 使用建议
- **HTML报告**: 快速查看和在线分享
- **Excel报告**: 数据分析、图表制作、深度研究

---

*最后更新: 2025-10-15 03:57*
