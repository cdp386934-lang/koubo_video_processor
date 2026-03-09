"""
口播视频自动处理工具

这个包提供了自动处理口播视频的功能，包括：
- 视频转文字（ASR）
- 自动添加字幕
- 去除气口
- 关键词标注和特效
- 添加美颜效果
- 生成剪映草稿
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .processor import KouboVideoProcessor
from .exporter import JianyingExporter

__all__ = ['KouboVideoProcessor', 'JianyingExporter']
