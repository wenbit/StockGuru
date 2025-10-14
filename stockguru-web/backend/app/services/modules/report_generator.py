"""
报告生成模块
负责生成可视化HTML报告
"""

import logging
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts.commons.utils import JsCode


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, config):
        """
        初始化报告生成器
        
        Args:
            config: 配置模块
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
    
    def generate_kline_chart(
        self, 
        code: str, 
        name: str, 
        stock_data: pd.DataFrame
    ) -> str:
        """
        生成K线图
        
        Args:
            code: 股票代码
            name: 股票名称
            stock_data: 股票日线数据（包含均线）
            
        Returns:
            图表的HTML字符串
        """
        if stock_data.empty:
            return "<p>无数据</p>"
        
        try:
            # 准备数据
            dates = stock_data['date'].astype(str).tolist()
            
            # K线数据：[开盘, 收盘, 最低, 最高]
            kline_data = stock_data[['open', 'close', 'low', 'high']].values.tolist()
            
            # 成交量数据
            volumes = stock_data['volume'].tolist()
            
            # 创建K线图
            kline = (
                Kline()
                .add_xaxis(xaxis_data=dates)
                .add_yaxis(
                    series_name="",
                    y_axis=kline_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#ef232a",  # 阳线颜色
                        color0="#14b143",  # 阴线颜色
                        border_color="#ef232a",
                        border_color0="#14b143",
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title=f"{name} ({code})",
                        pos_left="center"
                    ),
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        is_scale=True,
                        boundary_gap=False,
                        axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                        splitline_opts=opts.SplitLineOpts(is_show=False),
                        split_number=20,
                        min_="dataMin",
                        max_="dataMax",
                    ),
                    yaxis_opts=opts.AxisOpts(
                        is_scale=True,
                        splitarea_opts=opts.SplitAreaOpts(
                            is_show=True,
                            areastyle_opts=opts.AreaStyleOpts(opacity=1)
                        ),
                    ),
                    datazoom_opts=[
                        opts.DataZoomOpts(
                            is_show=False,
                            type_="inside",
                            xaxis_index=[0, 1],
                            range_start=0,
                            range_end=100,
                        ),
                        opts.DataZoomOpts(
                            is_show=True,
                            xaxis_index=[0, 1],
                            type_="slider",
                            pos_top="90%",
                            range_start=0,
                            range_end=100,
                        ),
                    ],
                    tooltip_opts=opts.TooltipOpts(
                        trigger="axis",
                        axis_pointer_type="cross",
                    ),
                )
            )
            
            # 添加均线
            for period in self.config.MA_PERIODS:
                ma_col = f'ma{period}'
                if ma_col in stock_data.columns:
                    ma_data = stock_data[ma_col].tolist()
                    line = (
                        Line()
                        .add_xaxis(xaxis_data=dates)
                        .add_yaxis(
                            series_name=f"MA{period}",
                            y_axis=ma_data,
                            is_smooth=True,
                            linestyle_opts=opts.LineStyleOpts(width=2),
                            label_opts=opts.LabelOpts(is_show=False),
                        )
                    )
                    kline.overlap(line)
            
            # 创建成交量柱状图
            bar = (
                Bar()
                .add_xaxis(xaxis_data=dates)
                .add_yaxis(
                    series_name="成交量",
                    y_axis=volumes,
                    label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=JsCode("""
                            function(params) {
                                var colorList;
                                if (params.data >= 0) {
                                    colorList = '#ef232a';
                                } else {
                                    colorList = '#14b143';
                                }
                                return colorList;
                            }
                        """)
                    ),
                )
                .set_global_opts(
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        grid_index=1,
                        axislabel_opts=opts.LabelOpts(is_show=False),
                    ),
                    yaxis_opts=opts.AxisOpts(
                        grid_index=1,
                        split_number=2,
                        axislabel_opts=opts.LabelOpts(is_show=False),
                        axisline_opts=opts.AxisLineOpts(is_show=False),
                        splitline_opts=opts.SplitLineOpts(is_show=False),
                    ),
                    legend_opts=opts.LegendOpts(is_show=False),
                )
            )
            
            # 组合图表
            grid = (
                Grid(init_opts=opts.InitOpts(
                    width="100%",
                    height="600px",
                    animation_opts=opts.AnimationOpts(animation=False),
                ))
                .add(
                    kline,
                    grid_opts=opts.GridOpts(
                        pos_left="10%",
                        pos_right="8%",
                        height="60%"
                    ),
                )
                .add(
                    bar,
                    grid_opts=opts.GridOpts(
                        pos_left="10%",
                        pos_right="8%",
                        pos_top="75%",
                        height="15%"
                    ),
                )
            )
            
            # 渲染为HTML字符串
            return grid.render_embed()
            
        except Exception as e:
            self.logger.error(f"生成K线图失败 ({code}): {str(e)}")
            return f"<p>生成图表失败: {str(e)}</p>"
    
    def generate_report(
        self, 
        stocks_df: pd.DataFrame, 
        stock_data_dict: Dict[str, pd.DataFrame]
    ) -> str:
        """
        生成完整的HTML报告
        
        Args:
            stocks_df: 最终筛选出的股票DataFrame
            stock_data_dict: 股票日线数据字典
            
        Returns:
            生成的HTML文件路径
        """
        self.logger.info("开始生成可视化报告...")
        
        if stocks_df.empty:
            self.logger.warning("没有股票数据，无法生成报告")
            return ""
        
        # 准备报告数据
        report_data = []
        
        for idx, row in stocks_df.iterrows():
            code = str(row['code'])
            name = row.get('name', '')
            momentum_score = row.get('momentum_score', 0)
            
            # 获取股票数据
            stock_data = stock_data_dict.get(code, pd.DataFrame())
            
            if stock_data.empty:
                self.logger.warning(f"股票 {code} 没有日线数据，跳过")
                continue
            
            # 生成K线图
            chart_html = self.generate_kline_chart(code, name, stock_data)
            
            report_data.append({
                'rank': len(report_data) + 1,
                'code': code,
                'name': name,
                'momentum_score': f"{momentum_score:.2f}",
                'chart_html': chart_html
            })
        
        if not report_data:
            self.logger.warning("没有有效的图表数据")
            return ""
        
        # 使用Jinja2渲染模板
        try:
            env = Environment(loader=FileSystemLoader(self.config.TEMPLATE_DIR))
            template = env.get_template('report_template.html')
            
            html_content = template.render(
                date=datetime.now().strftime('%Y-%m-%d'),
                stocks=report_data,
                total_count=len(report_data)
            )
            
            # 保存文件
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = os.path.join(self.config.OUTPUT_DIR, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {str(e)}")
            raise
