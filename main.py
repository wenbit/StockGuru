"""
股票短线复盘助手 - 主程序
"""

import logging
import sys
from datetime import datetime
import config
from modules.data_fetcher import DataFetcher
from modules.stock_filter import StockFilter
from modules.momentum_calculator import MomentumCalculator
from modules.report_generator import ReportGenerator


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_banner():
    """打印程序横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║          📈 股票短线复盘助手 StockGuru V1.0           ║
    ║                                                       ║
    ║          自动筛选强势股 + 可视化复盘报告               ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 打印横幅
    print_banner()
    
    try:
        # 1. 初始化各模块
        logger.info("=" * 60)
        logger.info("初始化模块...")
        logger.info("=" * 60)
        
        fetcher = DataFetcher()
        stock_filter = StockFilter(config)
        calculator = MomentumCalculator(config)
        generator = ReportGenerator(config)
        
        # 使用最近的交易日
        # 为了测试，我们使用一个固定的历史日期
        # 实际使用时可以改为自动获取最近交易日
        date_str = '2024-10-11'  # 使用一个确定有数据的交易日
        logger.info(f"复盘日期: {date_str} (测试模式)")
        
        # 2. 数据获取
        logger.info("\n" + "=" * 60)
        logger.info("[1/5] 数据获取阶段")
        logger.info("=" * 60)
        
        logger.info(f"正在获取成交额排名前 {config.VOLUME_TOP_N} 的股票...")
        volume_df = fetcher.get_volume_top_stocks(date_str, config.VOLUME_TOP_N)
        
        logger.info(f"正在获取热度排名前 {config.HOT_TOP_N} 的股票...")
        hot_df = fetcher.get_hot_top_stocks(date_str, config.HOT_TOP_N)
        
        if volume_df.empty or hot_df.empty:
            logger.error("数据获取失败，程序终止")
            return
        
        logger.info(f"✓ 成交额Top{config.VOLUME_TOP_N}: {len(volume_df)} 只")
        logger.info(f"✓ 热度Top{config.HOT_TOP_N}: {len(hot_df)} 只")
        
        # 3. 综合筛选
        logger.info("\n" + "=" * 60)
        logger.info("[2/5] 综合筛选阶段")
        logger.info("=" * 60)
        
        candidates = stock_filter.calculate_comprehensive_score(volume_df, hot_df)
        
        if candidates.empty:
            logger.error("综合筛选失败，程序终止")
            return
        
        # 应用过滤规则
        candidates = stock_filter.apply_filters(candidates)
        
        logger.info(f"✓ 初选股池: {len(candidates)} 只")
        
        # 4. 获取候选股的历史数据
        logger.info("\n" + "=" * 60)
        logger.info("[3/5] 获取历史行情数据")
        logger.info("=" * 60)
        
        candidate_codes = candidates['code'].astype(str).tolist()
        stock_data_dict = fetcher.batch_get_stock_data(
            candidate_codes, 
            config.KLINE_DAYS
        )
        
        logger.info(f"✓ 成功获取 {len(stock_data_dict)} 只股票的历史数据")
        
        # 5. 动量计算
        logger.info("\n" + "=" * 60)
        logger.info("[4/5] 动量计算阶段")
        logger.info("=" * 60)
        
        # 为每只股票计算均线
        for code, data in stock_data_dict.items():
            stock_data_dict[code] = calculator.calculate_all_ma(data)
        
        final_stocks = calculator.batch_calculate(candidates, stock_data_dict)
        
        if final_stocks.empty:
            logger.error("动量计算失败，程序终止")
            return
        
        logger.info(f"✓ 最终筛选: {len(final_stocks)} 只强势股")
        
        # 打印最终结果
        logger.info("\n" + "-" * 60)
        logger.info("最终筛选结果:")
        logger.info("-" * 60)
        for idx, row in final_stocks.iterrows():
            logger.info(
                f"排名 {idx+1}: {row['code']} {row.get('name', '')} "
                f"动量得分: {row['momentum_score']:.2f}"
            )
        logger.info("-" * 60)
        
        # 6. 生成报告
        logger.info("\n" + "=" * 60)
        logger.info("[5/5] 生成可视化报告")
        logger.info("=" * 60)
        
        report_path = generator.generate_report(final_stocks, stock_data_dict)
        
        if report_path:
            logger.info(f"✓ 报告已生成: {report_path}")
        else:
            logger.error("报告生成失败")
            return
        
        # 完成
        logger.info("\n" + "=" * 60)
        logger.info("🎉 复盘完成！")
        logger.info("=" * 60)
        logger.info(f"报告文件: {report_path}")
        logger.info("请在浏览器中打开查看")
        
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
