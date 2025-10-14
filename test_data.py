"""
测试数据获取
"""
import pywencai

# 测试获取成交额数据
print("测试获取成交额数据...")
try:
    df = pywencai.get(query='2024-10-11成交额前10', loop=True)
    print(f"获取到 {len(df)} 条数据")
    print(f"列名: {df.columns.tolist()}")
    print("\n前5条数据:")
    print(df.head())
except Exception as e:
    print(f"错误: {e}")

print("\n" + "="*60 + "\n")

# 测试获取热度数据
print("测试获取热度数据...")
try:
    df = pywencai.get(query='2024-10-11个股热度前10', loop=True)
    print(f"获取到 {len(df)} 条数据")
    print(f"列名: {df.columns.tolist()}")
    print("\n前5条数据:")
    print(df.head())
except Exception as e:
    print(f"错误: {e}")
