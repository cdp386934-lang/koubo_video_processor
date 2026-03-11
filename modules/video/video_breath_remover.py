#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频去气口处理模块
"""
import os
import json
from typing import List, Dict
from moviepy.editor import VideoFileClip, concatenate_videoclips


class VideoBreathRemover:
    """视频去气口处理器"""

    def __init__(self):
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv']

    def remove_breath_segments(
        self,
        video_path: str,
        subtitles: List[Dict],
        output_path: str = None
    ) -> str:
        """
        根据字幕中的removed标记，生成去除气口后的视频

        参数:
            video_path: 原始视频文件路径
            subtitles: 字幕列表（包含removed标记）
            output_path: 输出视频路径（可选）

        返回:
            生成的视频文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 设置输出路径
        if output_path is None:
            base_name = os.path.splitext(video_path)[0]
            ext = os.path.splitext(video_path)[1]
            output_path = f"{base_name}_no_breath{ext}"

        print(f"  正在加载视频: {video_path}")
        video = VideoFileClip(video_path)

        # 收集需要保留的视频片段
        clips_to_keep = []

        for subtitle in subtitles:
            # 只保留未被标记为removed的片段
            if subtitle.get('removed') != 1:
                start_sec = subtitle.get('StartMs', 0) / 1000
                end_sec = subtitle.get('EndMs', 0) / 1000

                # 提取视频片段
                clip = video.subclip(start_sec, end_sec)
                clips_to_keep.append(clip)

        if not clips_to_keep:
            raise Exception("没有可保留的视频片段")

        # 合并所有保留的片段
        print(f"  正在合并 {len(clips_to_keep)} 个视频片段...")
        final_video = concatenate_videoclips(clips_to_keep, method="compose")

        # 导出视频
        print(f"  正在导出视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )

        # 关闭视频对象
        video.close()
        final_video.close()
        for clip in clips_to_keep:
            clip.close()

        print(f"  ✅ 去气口视频已生成: {output_path}")

        # 统计信息
        original_duration = video.duration
        final_duration = final_video.duration
        removed_duration = original_duration - final_duration

        print(f"  原始时长: {original_duration:.1f}秒")
        print(f"  处理后时长: {final_duration:.1f}秒")
        print(f"  去除时长: {removed_duration:.1f}秒 ({removed_duration/original_duration*100:.1f}%)")

        return output_path
