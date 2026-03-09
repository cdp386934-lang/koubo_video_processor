#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕JSON管理器 - 统一管理字幕、关键词和音乐配置
"""
import os
import json
from typing import List, Dict


class SubtitleJsonManager:
    """字幕JSON管理器"""

    def __init__(self):
        pass

    def load_subtitle_json(self, json_path: str) -> Dict:
        """
        加载字幕JSON文件

        返回格式:
        {
            "subtitles": [...],  # 字幕列表
            "music": [...],      # 音乐配置
            "config": {...},     # 模块配置
            "metadata": {...}    # 元数据
        }
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 兼容旧格式（纯数组）
        if isinstance(data, list):
            return {
                "subtitles": data,
                "music": [],
                "config": {},
                "metadata": {}
            }

        # 新格式（包含音乐配置和config）
        return {
            "subtitles": data.get("subtitles", data if isinstance(data, list) else []),
            "music": data.get("music", []),
            "config": data.get("config", {}),
            "metadata": data.get("metadata", {})
        }

    def save_subtitle_json(self, json_path: str, data: Dict, backup: bool = True):
        """
        保存字幕JSON文件

        参数:
            json_path: JSON文件路径
            data: 数据字典（包含subtitles, music, metadata）
            backup: 是否备份原文件
        """
        # 备份原文件
        if backup and os.path.exists(json_path):
            backup_path = json_path + '.backup'
            import shutil
            shutil.copy2(json_path, backup_path)
            print(f"✅ 已备份原文件: {backup_path}")

        # 保存新格式
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_music_to_json(self, json_path: str, music_segments: List[Dict],
                         output_path: str = None):
        """
        将音乐配置添加到字幕JSON

        参数:
            json_path: 字幕JSON文件路径
            music_segments: 音乐片段列表
            output_path: 输出路径（None则覆盖原文件）
        """
        # 加载现有数据
        data = self.load_subtitle_json(json_path)

        # 添加音乐配置
        data['music'] = music_segments

        # 保存
        if output_path is None:
            output_path = json_path

        self.save_subtitle_json(output_path, data)
        print(f"✅ 已添加 {len(music_segments)} 个音乐片段到: {output_path}")

    def get_music_from_json(self, json_path: str) -> List[Dict]:
        """
        从字幕JSON中获取音乐配置

        返回:
            音乐片段列表
        """
        data = self.load_subtitle_json(json_path)
        return data.get('music', [])

    def update_keywords(self, json_path: str, keywords_map: Dict[int, str],
                       output_path: str = None):
        """
        更新字幕中的关键词

        参数:
            json_path: 字幕JSON文件路径
            keywords_map: 关键词映射 {索引: 关键词}
            output_path: 输出路径
        """
        data = self.load_subtitle_json(json_path)
        subtitles = data['subtitles']

        # 更新关键词
        for idx, keyword in keywords_map.items():
            if 0 <= idx < len(subtitles):
                subtitles[idx]['keyword'] = keyword

        # 保存
        if output_path is None:
            output_path = json_path

        self.save_subtitle_json(output_path, data)
        print(f"✅ 已更新 {len(keywords_map)} 个关键词")

    def convert_old_format_to_new(self, json_path: str, output_path: str = None):
        """
        将旧格式（纯数组）转换为新格式（包含音乐配置）

        参数:
            json_path: 旧格式JSON文件
            output_path: 输出路径（None则覆盖原文件）
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        # 如果已经是新格式，直接返回
        if isinstance(old_data, dict) and 'subtitles' in old_data:
            print("✅ 文件已经是新格式")
            return

        # 转换为新格式
        new_data = {
            "subtitles": old_data if isinstance(old_data, list) else [],
            "music": [],
            "metadata": {
                "version": "2.0",
                "converted_from": "old_format"
            }
        }

        # 保存
        if output_path is None:
            output_path = json_path

        self.save_subtitle_json(output_path, new_data, backup=True)
        print(f"✅ 已转换为新格式: {output_path}")

    def set_config(self, json_path: str, module: str, config: Dict):
        """
        设置模块配置

        参数:
            json_path: JSON文件路径
            module: 模块名称（如 'video_to_audio', 'breath_removal', 'deepseek'）
            config: 配置字典
        """
        data = self.load_subtitle_json(json_path)

        if 'config' not in data:
            data['config'] = {}

        data['config'][module] = config
        self.save_subtitle_json(json_path, data, backup=False)

    def get_config(self, json_path: str, module: str) -> Dict:
        """
        获取模块配置

        参数:
            json_path: JSON文件路径
            module: 模块名称

        返回:
            配置字典（如果不存在则返回默认配置）
        """
        # 默认配置
        default_configs = {
            'video_to_audio': {
                'audio_format': 'wav',
                'sample_rate': 44100,
                'bitrate': '192k',
                'channels': 2
            },
            'breath_removal': {
                'enabled': True,
                'filler_words': ['嗯', '啊', '呃', '哦', '额'],
                'max_duration_ms': 500,
                'min_confidence': 0.8
            },
            'deepseek': {
                'enabled': True,
                'model': 'deepseek-chat',
                'max_keywords': 10,
                'importance_levels': [1, 2, 3]
            },
            'background_music': {
                'enabled': True,
                'default_volume': 0.3,
                'default_fade_in': 1.0,
                'default_fade_out': 1.0
            }
        }

        # 尝试从文件加载
        if os.path.exists(json_path):
            data = self.load_subtitle_json(json_path)
            return data.get('config', {}).get(module, default_configs.get(module, {}))
        else:
            return default_configs.get(module, {})

    def add_processing_step(self, json_path: str, step: str, status: str,
                           duration_ms: int, **kwargs):
        """
        添加处理步骤记录

        参数:
            json_path: JSON文件路径
            step: 步骤名称
            status: 状态（'completed', 'failed', 'skipped'）
            duration_ms: 耗时（毫秒）
            **kwargs: 其他额外信息
        """
        from datetime import datetime

        data = self.load_subtitle_json(json_path)

        if 'metadata' not in data:
            data['metadata'] = {}
        if 'processing_steps' not in data['metadata']:
            data['metadata']['processing_steps'] = []

        step_info = {
            'step': step,
            'status': status,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
        step_info.update(kwargs)

        data['metadata']['processing_steps'].append(step_info)
        self.save_subtitle_json(json_path, data, backup=False)

    def update_metadata(self, json_path: str, metadata: Dict):
        """
        更新元数据

        参数:
            json_path: JSON文件路径
            metadata: 要更新的元数据字典
        """
        data = self.load_subtitle_json(json_path)

        if 'metadata' not in data:
            data['metadata'] = {}

        data['metadata'].update(metadata)
        self.save_subtitle_json(json_path, data, backup=False)

    def get_statistics(self, json_path: str) -> Dict:
        """
        获取字幕JSON的统计信息

        返回:
            统计信息字典
        """
        data = self.load_subtitle_json(json_path)
        subtitles = data['subtitles']
        music = data['music']

        # 统计字幕
        total_subtitles = len(subtitles)
        removed_count = sum(1 for s in subtitles if s.get('removed') == 1)
        keyword_count = sum(1 for s in subtitles if s.get('keyword'))

        # 统计关键词等级
        grade_counts = {}
        for s in subtitles:
            grade = s.get('text_grade', 1)
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        # 统计音乐
        total_music_duration = 0
        for m in music:
            duration = m.get('end_time', 0) - m.get('start_time', 0)
            total_music_duration += duration

        # 统计处理步骤
        processing_steps = data.get('metadata', {}).get('processing_steps', [])
        total_processing_time = sum(step.get('duration_ms', 0) for step in processing_steps)

        return {
            'total_subtitles': total_subtitles,
            'removed_subtitles': removed_count,
            'valid_subtitles': total_subtitles - removed_count,
            'keyword_count': keyword_count,
            'grade_counts': grade_counts,
            'music_segments': len(music),
            'total_music_duration': total_music_duration,
            'processing_steps': processing_steps,
            'total_processing_time_ms': total_processing_time
        }

    def create_music_template(self, json_path: str, video_duration: float = None):
        """
        为字幕JSON创建音乐配置模板

        参数:
            json_path: 字幕JSON文件路径
            video_duration: 视频总时长（秒），如果不提供则从字幕推算
        """
        data = self.load_subtitle_json(json_path)
        subtitles = data['subtitles']

        # 推算视频时长
        if video_duration is None and subtitles:
            last_subtitle = subtitles[-1]
            video_duration = last_subtitle.get('EndMs', 0) / 1000

        # 创建音乐模板
        music_template = [
            {
                "start_time": 0,
                "end_time": video_duration if video_duration else 60,
                "music_file": "bgm1.mp3",
                "volume": 0.3,
                "fade_in": 1.0,
                "fade_out": 1.0,
                "loop": False,
                "description": "全程背景音乐"
            }
        ]

        data['music'] = music_template
        self.save_subtitle_json(json_path, data)
        print(f"✅ 已创建音乐模板（时长: {video_duration:.1f}秒）")


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='字幕JSON管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换为新格式
  python3 subtitle_json_manager.py --convert movies/未加工.json

  # 添加音乐配置
  python3 subtitle_json_manager.py --add-music movies/未加工.json music_config.json

  # 创建音乐模板
  python3 subtitle_json_manager.py --create-music-template movies/未加工.json

  # 查看统计信息
  python3 subtitle_json_manager.py --stats movies/未加工.json

  # 获取音乐配置
  python3 subtitle_json_manager.py --get-music movies/未加工.json
        """
    )

    parser.add_argument('json_file', nargs='?', help='字幕JSON文件路径')
    parser.add_argument('--convert', metavar='FILE',
                       help='转换旧格式为新格式')
    parser.add_argument('--add-music', nargs=2, metavar=('JSON', 'MUSIC'),
                       help='添加音乐配置（字幕JSON 音乐配置JSON）')
    parser.add_argument('--create-music-template', metavar='FILE',
                       help='创建音乐配置模板')
    parser.add_argument('--stats', metavar='FILE',
                       help='显示统计信息')
    parser.add_argument('--get-music', metavar='FILE',
                       help='获取音乐配置')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    manager = SubtitleJsonManager()

    if args.convert:
        manager.convert_old_format_to_new(args.convert, args.output)

    elif args.add_music:
        subtitle_json, music_json = args.add_music
        # 加载音乐配置
        with open(music_json, 'r', encoding='utf-8') as f:
            music_config = json.load(f)
        music_segments = music_config.get('music_segments', [])
        manager.add_music_to_json(subtitle_json, music_segments, args.output)

    elif args.create_music_template:
        manager.create_music_template(args.create_music_template)

    elif args.stats:
        print("=" * 60)
        print("字幕JSON统计信息")
        print("=" * 60)
        stats = manager.get_statistics(args.stats)
        print(f"总字幕数: {stats['total_subtitles']}")
        print(f"气口片段: {stats['removed_subtitles']}")
        print(f"有效片段: {stats['valid_subtitles']}")
        print(f"关键词数: {stats['keyword_count']}")
        print(f"\n字幕等级分布:")
        for grade, count in sorted(stats['grade_counts'].items()):
            print(f"  Grade {grade}: {count} 条")
        print(f"\n音乐配置:")
        print(f"  音乐片段: {stats['music_segments']} 个")
        print(f"  总时长: {stats['total_music_duration']:.1f} 秒")

        # 显示处理步骤信息
        if stats.get('processing_steps'):
            print(f"\n处理步骤:")
            print(f"  总处理时间: {stats['total_processing_time_ms'] / 1000:.2f} 秒")
            for step in stats['processing_steps']:
                status_icon = "✅" if step['status'] == 'completed' else "❌"
                print(f"  {status_icon} {step['step']}: {step['duration_ms']}ms ({step['status']})")
                # 显示额外信息
                for key, value in step.items():
                    if key not in ['step', 'status', 'duration_ms', 'timestamp']:
                        print(f"      {key}: {value}")

    elif args.get_music:
        music = manager.get_music_from_json(args.get_music)
        if music:
            print("=" * 60)
            print("音乐配置")
            print("=" * 60)
            for i, m in enumerate(music, 1):
                print(f"\n片段 {i}:")
                print(f"  时间: {m.get('start_time')}s - {m.get('end_time')}s")
                print(f"  文件: {m.get('music_file')}")
                print(f"  音量: {m.get('volume')}")
                if m.get('description'):
                    print(f"  描述: {m.get('description')}")
        else:
            print("⚠️  没有音乐配置")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
