"""
股票短线复盘助手 - 配置文件
所有可调参数集中管理
"""

# ==================== 筛选参数 ====================
# 成交额排名范围
VOLUME_TOP_N = 100

# 热度排名范围
HOT_TOP_N = 100

# 综合评分取前N名
FINAL_TOP_N = 30

# 动量计算周期(天)
MOMENTUM_DAYS = 25

# 最终筛选数量
MOMENTUM_TOP_N = 10

# ==================== 综合评分权重 ====================
# 成交额权重
WEIGHT_VOLUME = 0.5

# 热度权重
WEIGHT_HOT = 0.5

# ==================== 过滤规则 ====================
# 是否排除ST股
EXCLUDE_ST = True

# 排除上市N天内的次新股
EXCLUDE_NEW_STOCK_DAYS = 60

# 排除N天内涨幅超过此比例的股票 (1.0 = 100%)
MAX_RISE_RATIO = 1.0

# ==================== 图表配置 ====================
# 均线周期
MA_PERIODS = [5, 10, 20]

# 图表宽度
CHART_WIDTH = "100%"

# 图表高度
CHART_HEIGHT = "500px"

# K线图显示的交易日数量
KLINE_DAYS = 60

# ==================== 输出配置 ====================
# 报告输出目录
OUTPUT_DIR = "./output"

# 模板目录
TEMPLATE_DIR = "./templates"

# 静态资源目录
STATIC_DIR = "./static"

# 数据缓存目录
CACHE_DIR = "./data/cache"

# ==================== 日志配置 ====================
# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# 日志文件路径
LOG_FILE = "stockguru.log"
