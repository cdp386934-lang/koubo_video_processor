#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的ASR实现方案
支持多种ASR方式：手动导入、本地Whisper等
"""
import os
import json
from pathlib import Path


class SimpleASR:
    """简单ASR服务"""

    def __init__(self):
        pass

    def manual_import(self, video_path, subtitle_text):
        """
        手动导入字幕文本

        参数:
            video_path: 视频文件路径
            subtitle_text: 字幕文本（每行一句）

        返回:
            字幕JSON文件路径
        """
        # 解析视频路径
        video_path = Path(video_path)
        folder_path = video_path.parent
        file_name = video_path.stem
        json_path = folder_path / f"{file_name}.json"

        # 分割文本为句子
        lines = [line.strip() for line in subtitle_text.strip().split('\n') if line.strip()]

        # 创建字幕数据（简单版本，时间戳需要后续调整）
        subtitles = []
        current_time = 0

        for i, line in enumerate(lines):
            # 估算每句话的时长（按字数，平均每字0.3秒）
            duration = len(line) * 300  # 毫秒

            subtitle = {
                'FinalSentence': line,
                'Text': line,
                'StartMs': current_time,
                'EndMs': current_time + duration,
                'keyword': '',
                'text_grade': 1,
                'video_grade': 1,
                'removed': 0
            }

            subtitles.append(subtitle)
            current_time += duration + 200  # 加200ms间隔

        # 保存JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)

        print(f"✅ 字幕文件已生成: {json_path}")
        print(f"   共 {len(subtitles)} 条字幕")

        return str(json_path)

    def from_srt(self, video_path, srt_path):
        """
        从SRT字幕文件导入

        参数:
            video_path: 视频文件路径
            srt_path: SRT字幕文件路径

        返回:
            字幕JSON文件路径
        """
        # 解析视频路径
        video_path = Path(video_path)
        folder_path = video_path.parent
        file_name = video_path.stem
        json_path = folder_path / f"{file_name}.json"

        # 读取SRT文件
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()

        # 解析SRT
        subtitles = self._parse_srt(srt_content)

        # 保存JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(subtitles, f, ensure_ascii=False, indent=2)

        print(f"✅ 字幕文件已生成: {json_path}")
        print(f"   共 {len(subtitles)} 条字幕")

        return str(json_path)

    def _parse_srt(self, srt_content):
        """解析SRT格式"""
        subtitles = []
        blocks = srt_content.strip().split('\n\n')

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # 解析时间戳
            time_line = lines[1]
            times = time_line.split(' --> ')
            if len(times) != 2:
                continue

            start_ms = self._time_to_ms(times[0])
            end_ms = self._time_to_ms(times[1])

            # 解析文本
            text = '\n'.join(lines[2:])

            subtitle = {
                'FinalSentence': text,
                'Text': text,
                'StartMs': start_ms,
                'EndMs': end_ms,
                'keyword': '',
                'text_grade': 1,
                'video_grade': 1,
                'removed': 0
            }

            subtitles.append(subtitle)

        return subtitles

    def _time_to_ms(self, time_str):
        """将SRT时间格式转换为毫秒"""
        # 格式: 00:00:01,000
        time_str = time_str.strip().replace(',', '.')
        parts = time_str.split(':')

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
        return int(total_ms)

    def from_json(self, video_path, json_path):
        """
        直接使用已有的JSON字幕文件

        参数:
            video_path: 视频文件路径
            json_path: 字幕JSON文件路径

        返回:
            字幕JSON文件路径
        """
        # 验证JSON格式
        with open(json_path, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)

        print(f"✅ 使用已有字幕文件: {json_path}")
        print(f"   共 {len(subtitles)} 条字幕")

        return json_path


def create_subtitle_template(video_path):
    """
    创建字幕模板文件，供用户手动填写

    参数:
        video_path: 视频文件路径

    返回:
        模板文件路径
    """
    video_path = Path(video_path)
    folder_path = video_path.parent
    file_name = video_path.stem
    template_path = folder_path / f"{file_name}_字幕模板.txt"

    template_content = """# 字幕模板
# 请在下方填写字幕内容，每行一句话
# 保存后运行: python3 simple_asr.py import <视频路径> <此文件路径>

# 示例:
# 大家好，欢迎来到我的频道
# 今天我要分享一个非常有用的技巧
# 希望对大家有帮助

"""

    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)

    print(f"✅ 字幕模板已创建: {template_path}")
    print(f"   请编辑此文件，填写字幕内容")

    return str(template_path)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  1. 创建模板: python3 simple_asr.py template <视频路径>")
        print("  2. 导入文本: python3 simple_asr.py import <视频路径> <文本文件路径>")
        print("  3. 导入SRT:  python3 simple_asr.py srt <视频路径> <SRT文件路径>")
        print("  4. 使用JSON: python3 simple_asr.py json <视频路径> <JSON文件路径>")
        sys.exit(1)

    command = sys.argv[1]
    asr = SimpleASR()

    try:
        if command == 'template':
            if len(sys.argv) < 3:
                print("错误: 请提供视频路径")
                sys.exit(1)
            video_path = sys.argv[2]
            create_subtitle_template(video_path)

        elif command == 'import':
            if len(sys.argv) < 4:
                print("错误: 请提供视频路径和文本文件路径")
                sys.exit(1)
            video_path = sys.argv[2]
            text_path = sys.argv[3]

            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # 移除注释行
            lines = [line for line in text.split('\n') if not line.strip().startswith('#')]
            text = '\n'.join(lines)

            asr.manual_import(video_path, text)

        elif command == 'srt':
            if len(sys.argv) < 4:
                print("错误: 请提供视频路径和SRT文件路径")
                sys.exit(1)
            video_path = sys.argv[2]
            srt_path = sys.argv[3]
            asr.from_srt(video_path, srt_path)

        elif command == 'json':
            if len(sys.argv) < 4:
                print("错误: 请提供视频路径和JSON文件路径")
                sys.exit(1)
            video_path = sys.argv[2]
            json_path = sys.argv[3]
            asr.from_json(video_path, json_path)

        else:
            print(f"错误: 未知命令 '{command}'")
            sys.exit(1)

        print("\n✅ 完成！现在可以运行主程序处理视频了")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
