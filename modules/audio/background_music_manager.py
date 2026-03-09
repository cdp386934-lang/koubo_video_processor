#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景音乐管理器 - 为视频添加背景音乐
"""
import os
import json
from typing import List, Dict, Tuple


class BackgroundMusicManager:
    """背景音乐管理器"""

    def __init__(self, music_dir: str = None):
        """
        初始化音乐管理器

        参数:
            music_dir: 音乐文件目录（默认为 music/ 目录）
        """
        if music_dir is None:
            music_dir = os.path.join(
                os.path.dirname(__file__),
                'music'
            )
        self.music_dir = music_dir

        # 确保音乐目录存在
        os.makedirs(self.music_dir, exist_ok=True)

    def create_music_config(self, music_segments: List[Dict]) -> List[Dict]:
        """
        创建音乐配置

        参数:
            music_segments: 音乐片段列表
                [
                    {
                        "start_time": 0,      # 开始时间（秒）
                        "end_time": 30,       # 结束时间（秒）
                        "music_file": "bgm1.mp3",  # 音乐文件名
                        "volume": 0.3,        # 音量（0-1）
                        "fade_in": 1.0,       # 淡入时长（秒）
                        "fade_out": 1.0       # 淡出时长（秒）
                    }
                ]

        返回:
            处理后的音乐配置列表
        """
        processed_segments = []

        for i, segment in enumerate(music_segments):
            # 验证必需字段
            if 'start_time' not in segment or 'end_time' not in segment:
                print(f"⚠️  音乐片段 {i} 缺少时间信息，跳过")
                continue

            if 'music_file' not in segment:
                print(f"⚠️  音乐片段 {i} 缺少音乐文件，跳过")
                continue

            # 获取音乐文件完整路径
            music_file = segment['music_file']
            if not os.path.isabs(music_file):
                music_file = os.path.join(self.music_dir, music_file)

            # 检查文件是否存在
            if not os.path.exists(music_file):
                print(f"⚠️  音乐文件不存在: {music_file}")
                continue

            # 创建配置
            config = {
                'path': music_file,
                'start_time': float(segment['start_time']),
                'end_time': float(segment['end_time']),
                'volume': float(segment.get('volume', 0.3)),
                'fade_in': float(segment.get('fade_in', 1.0)),
                'fade_out': float(segment.get('fade_out', 1.0)),
                'loop': segment.get('loop', False)
            }

            processed_segments.append(config)

        return processed_segments

    def load_music_config_from_file(self, config_file: str) -> List[Dict]:
        """
        从配置文件加载音乐配置

        参数:
            config_file: 配置文件路径（JSON格式）

        返回:
            音乐配置列表
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件不存在: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        music_segments = config.get('music_segments', [])
        return self.create_music_config(music_segments)

    def create_music_config_file(self, output_file: str, template: bool = True):
        """
        创建音乐配置文件模板

        参数:
            output_file: 输出文件路径
            template: 是否创建模板（包含示例）
        """
        if template:
            config = {
                "music_segments": [
                    {
                        "start_time": 0,
                        "end_time": 30,
                        "music_file": "bgm1.mp3",
                        "volume": 0.3,
                        "fade_in": 1.0,
                        "fade_out": 1.0,
                        "loop": False,
                        "description": "开场音乐"
                    },
                    {
                        "start_time": 30,
                        "end_time": 60,
                        "music_file": "bgm2.mp3",
                        "volume": 0.2,
                        "fade_in": 1.0,
                        "fade_out": 1.0,
                        "loop": False,
                        "description": "中段音乐"
                    }
                ],
                "说明": {
                    "start_time": "开始时间（秒）",
                    "end_time": "结束时间（秒）",
                    "music_file": "音乐文件名（放在music/目录下）",
                    "volume": "音量（0-1，建议0.2-0.4）",
                    "fade_in": "淡入时长（秒）",
                    "fade_out": "淡出时长（秒）",
                    "loop": "是否循环播放",
                    "description": "描述（可选）"
                }
            }
        else:
            config = {
                "music_segments": []
            }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"✅ 已创建配置文件: {output_file}")

    def add_music_to_template(self, template_config: Dict,
                             music_segments: List[Dict]) -> Dict:
        """
        将音乐配置添加到模板配置中

        参数:
            template_config: 模板配置字典
            music_segments: 音乐片段列表

        返回:
            更新后的模板配置
        """
        # 处理音乐配置
        processed_music = self.create_music_config(music_segments)

        # 添加到模板
        template_config['audio_list'] = processed_music

        return template_config

    def validate_music_segments(self, music_segments: List[Dict],
                               video_duration: float = None) -> Tuple[bool, List[str]]:
        """
        验证音乐片段配置

        参数:
            music_segments: 音乐片段列表
            video_duration: 视频总时长（秒）

        返回:
            (是否有效, 错误信息列表)
        """
        errors = []

        for i, segment in enumerate(music_segments):
            # 检查时间
            start = segment.get('start_time')
            end = segment.get('end_time')

            if start is None or end is None:
                errors.append(f"片段 {i}: 缺少时间信息")
                continue

            if start >= end:
                errors.append(f"片段 {i}: 开始时间 >= 结束时间")

            if start < 0:
                errors.append(f"片段 {i}: 开始时间 < 0")

            if video_duration and end > video_duration:
                errors.append(f"片段 {i}: 结束时间超过视频时长")

            # 检查音乐文件
            music_file = segment.get('music_file')
            if not music_file:
                errors.append(f"片段 {i}: 缺少音乐文件")
                continue

            if not os.path.isabs(music_file):
                music_file = os.path.join(self.music_dir, music_file)

            if not os.path.exists(music_file):
                errors.append(f"片段 {i}: 音乐文件不存在 - {music_file}")

            # 检查音量
            volume = segment.get('volume', 0.3)
            if not 0 <= volume <= 1:
                errors.append(f"片段 {i}: 音量超出范围 (0-1)")

        # 检查时间重叠
        sorted_segments = sorted(music_segments, key=lambda x: x.get('start_time', 0))
        for i in range(len(sorted_segments) - 1):
            if sorted_segments[i].get('end_time', 0) > sorted_segments[i+1].get('start_time', 0):
                errors.append(f"片段 {i} 和 {i+1} 时间重叠")

        return len(errors) == 0, errors

    def get_music_info(self, music_file: str) -> Dict:
        """
        获取音乐文件信息

        参数:
            music_file: 音乐文件路径

        返回:
            音乐信息字典
        """
        if not os.path.exists(music_file):
            return {'error': '文件不存在'}

        info = {
            'path': music_file,
            'name': os.path.basename(music_file),
            'size': os.path.getsize(music_file),
            'size_mb': round(os.path.getsize(music_file) / 1024 / 1024, 2)
        }

        # 尝试获取音频时长
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(music_file)
            info['duration'] = audio.duration
            audio.close()
        except:
            info['duration'] = None

        return info

    def list_available_music(self) -> List[Dict]:
        """
        列出可用的音乐文件

        返回:
            音乐文件信息列表
        """
        if not os.path.exists(self.music_dir):
            return []

        music_files = []
        for filename in os.listdir(self.music_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.flac')):
                file_path = os.path.join(self.music_dir, filename)
                info = self.get_music_info(file_path)
                music_files.append(info)

        return music_files


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='背景音乐管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建配置文件模板
  python3 background_music_manager.py --create-template music_config.json

  # 列出可用音乐
  python3 background_music_manager.py --list

  # 验证配置文件
  python3 background_music_manager.py --validate music_config.json

  # 查看音乐信息
  python3 background_music_manager.py --info music/bgm1.mp3
        """
    )

    parser.add_argument('--create-template', metavar='FILE',
                       help='创建配置文件模板')
    parser.add_argument('--list', action='store_true',
                       help='列出可用的音乐文件')
    parser.add_argument('--validate', metavar='FILE',
                       help='验证配置文件')
    parser.add_argument('--info', metavar='FILE',
                       help='查看音乐文件信息')
    parser.add_argument('--music-dir', metavar='DIR',
                       help='音乐文件目录（默认: music/）')

    args = parser.parse_args()

    manager = BackgroundMusicManager(music_dir=args.music_dir)

    if args.create_template:
        manager.create_music_config_file(args.create_template, template=True)

    elif args.list:
        print("=" * 60)
        print("可用的音乐文件")
        print("=" * 60)
        music_files = manager.list_available_music()
        if not music_files:
            print("没有找到音乐文件")
            print(f"请将音乐文件放在: {manager.music_dir}")
        else:
            for i, info in enumerate(music_files, 1):
                print(f"\n{i}. {info['name']}")
                print(f"   大小: {info['size_mb']} MB")
                if info.get('duration'):
                    print(f"   时长: {info['duration']:.2f} 秒")

    elif args.validate:
        print("=" * 60)
        print("验证配置文件")
        print("=" * 60)
        try:
            music_config = manager.load_music_config_from_file(args.validate)
            print(f"✅ 配置文件格式正确")
            print(f"   音乐片段数: {len(music_config)}")

            # 验证每个片段
            with open(args.validate, 'r', encoding='utf-8') as f:
                config = json.load(f)
            segments = config.get('music_segments', [])

            is_valid, errors = manager.validate_music_segments(segments)
            if is_valid:
                print("✅ 所有音乐片段配置正确")
            else:
                print("\n⚠️  发现以下问题:")
                for error in errors:
                    print(f"   - {error}")

        except Exception as e:
            print(f"❌ 验证失败: {e}")

    elif args.info:
        print("=" * 60)
        print("音乐文件信息")
        print("=" * 60)
        info = manager.get_music_info(args.info)
        if 'error' in info:
            print(f"❌ {info['error']}")
        else:
            print(f"文件名: {info['name']}")
            print(f"路径: {info['path']}")
            print(f"大小: {info['size_mb']} MB")
            if info.get('duration'):
                print(f"时长: {info['duration']:.2f} 秒")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
