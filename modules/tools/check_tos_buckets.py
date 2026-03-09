#!/usr/bin/env python3
"""检查TOS存储桶列表"""

import os
from dotenv import load_dotenv
from tos import TosClientV2

# 加载环境变量
load_dotenv()

# 获取配置
access_key = os.getenv('VOLCENGINE_ACCESS_KEY')
secret_key = os.getenv('VOLCENGINE_SECRET_KEY')
region = os.getenv('VOLCENGINE_REGION', 'cn-beijing')

print("=" * 60)
print("TOS存储桶诊断")
print("=" * 60)
print(f"\n当前配置:")
print(f"  Access Key: {access_key[:10]}..." if access_key else "  Access Key: 未配置")
print(f"  Region: {region}")
print(f"  配置的Bucket名称: {os.getenv('VOLCENGINE_TOS_BUCKET', 'koubo-audio')}")
print()

try:
    # 创建TOS客户端
    client = TosClientV2(
        ak=access_key,
        sk=secret_key,
        endpoint=f'tos-{region}.volces.com',
        region=region
    )

    print("正在获取存储桶列表...")
    response = client.list_buckets()

    if response.buckets:
        print(f"\n找到 {len(response.buckets)} 个存储桶:")
        print("-" * 60)
        for bucket in response.buckets:
            print(f"  名称: {bucket.name}")
            print(f"  区域: {bucket.location}")
            print(f"  创建时间: {bucket.creation_date}")
            print("-" * 60)
    else:
        print("\n未找到任何存储桶")

except Exception as e:
    print(f"\n错误: {e}")
    print(f"错误类型: {type(e).__name__}")
