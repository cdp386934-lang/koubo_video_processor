#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建灰白色背景图片
"""
from PIL import Image, ImageDraw
import os

def create_gray_white_background(width=1080, height=1920, output_path=None):
    """
    创建灰白色渐变背景图片

    参数:
        width: 图片宽度（默认1080，适配9:16）
        height: 图片高度（默认1920，适配9:16）
        output_path: 输出路径
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__),
            'assets',
            'gray_white_background.png'
        )

    # 创建assets目录
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 创建图片
    img = Image.new('RGB', (width, height), color='#F5F5F5')

    # 可选：添加渐变效果
    draw = ImageDraw.Draw(img)

    # 保存图片
    img.save(output_path, 'PNG')
    print(f"✅ 背景图片已创建: {output_path}")

    return output_path

if __name__ == '__main__':
    create_gray_white_background()
