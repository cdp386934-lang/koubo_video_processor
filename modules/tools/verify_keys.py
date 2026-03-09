#!/usr/bin/env python3
"""验证火山引擎密钥格式"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("火山引擎密钥验证")
print("=" * 60)
print()

access_key = os.getenv('VOLCENGINE_ACCESS_KEY')
secret_key = os.getenv('VOLCENGINE_SECRET_KEY')

print("当前配置的密钥:")
print(f"  Access Key: {access_key}")
print(f"  Secret Key: {secret_key}")
print()

print("密钥格式检查:")
print(f"  Access Key 长度: {len(access_key) if access_key else 0}")
print(f"  Secret Key 长度: {len(secret_key) if secret_key else 0}")
print()

print("⚠️  注意事项:")
print("1. Access Key 通常是一个长字符串（40-50个字符）")
print("2. Secret Key 通常也是一个长字符串（40-50个字符）")
print("3. 请确认这些密钥是从火山引擎控制台正确复制的")
print()
print("如何获取正确的密钥:")
print("1. 登录火山引擎控制台: https://console.volcengine.com")
print("2. 进入 '访问控制' -> 'API访问密钥'")
print("3. 创建或查看现有的密钥对")
print("4. 复制 Access Key ID 和 Secret Access Key")
print()
