#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理模块 - 支持去气口音频生成
"""
import os
import json
from typing import List, Dict, Tuple
from pydub import AudioSegment


class AudioProcessor:
    """音频处理器 - 根据字幕标记生成去气口音频"""

    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac']

    def remove_breath_segments(
        self,
        audio_path: str,
        subtitles: List[Dict],
        output_path: str = None
    ) -> str:
        """
        根据字幕中的removed标记，生成去除气口后的音频

        参数:
            audio_path: 原始音频文件路径
            subtitles: 字幕列表（包含removed标记）
            output_path: 输出音频路径（可选）

        返回:
            生成的音频文件路径
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        # 设置输出路径
        if output_path is None:
            base_name = os.path.splitext(audio_path)[0]
            ext = os.path.splitext(audio_path)[1]
            output_path = f"{base_name}_no_breath{ext}"

        print(f"  正在加载音频: {audio_path}")
        audio = AudioSegment.from_file(audio_path)

        # 收集需要保留的音频片段
        segments_to_keep = []

        for subtitle in subtitles:
            # 只保留未被标记为removed的片段
            if subtitle.get('removed') != 1:
                start_ms = subtitle.get('StartMs', 0)
                end_ms = subtitle.get('EndMs', 0)

                # 提取音频片段
                segment = audio[start_ms:end_ms]
                segments_to_keep.append(segment)

        if not segments_to_keep:
            raise Exception("没有可保留的音频片段")

        # 合并所有保留的片段
        print(f"  正在合并 {len(segments_to_keep)} 个音频片段...")
        final_audio = segments_to_keep[0]
        for segment in segments_to_keep[1:]:
            final_audio += segment

        # 导出音频
        print(f"  正在导出音频: {output_path}")
        final_audio.export(output_path, format=os.path.splitext(output_path)[1][1:])

        print(f"  ✅ 去气口音频已生成: {output_path}")

        # 统计信息
        original_duration = len(audio) / 1000
        final_duration = len(final_audio) / 1000
        removed_duration = original_duration - final_duration

        print(f"  原始时长: {original_duration:.1f}秒")
        print(f"  处理后时长: {final_duration:.1f}秒")
        print(f"  去除时长: {removed_duration:.1f}秒 ({removed_duration/original_duration*100:.1f}%)")

        return output_path

    def get_audio_info(self, audio_path: str) -> Dict:
        """
        获取音频信息

        参数:
            audio_path: 音频文件路径

        返回:
            音频信息字典
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        audio = AudioSegment.from_file(audio_path)

        return {
            'duration_ms': len(audio),
            'duration_sec': len(audio) / 1000,
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'frame_rate': audio.frame_rate,
            'frame_width': audio.frame_width
        }
