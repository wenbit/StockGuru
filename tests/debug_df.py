"""
调试DataFrame结构
"""
from modules.data_fetcher import DataFetcher

fetcher = DataFetcher()

# 获取数据
volume_df = fetcher.get_volume_top_stocks('2024-10-11', 10)

print("=" * 60)
print("成交额DataFrame信息:")
print("=" * 60)
print(f"形状: {volume_df.shape}")
print(f"\n列名: {volume_df.columns.tolist()}")
print(f"\n列名是否有重复: {volume_df.columns.duplicated().any()}")
if volume_df.columns.duplicated().any():
    print(f"重复的列: {volume_df.columns[volume_df.columns.duplicated()].tolist()}")
print(f"\n索引: {volume_df.index.tolist()}")
print(f"索引是否有重复: {volume_df.index.duplicated().any()}")
print(f"\n前3行数据:")
print(volume_df.head(3))
