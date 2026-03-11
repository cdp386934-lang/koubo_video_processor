#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合成模块 - 使用 ffmpeg 将素材合成到主视频中
"""
import os
import subprocess
import json
from typing import List, Dict, Optional, Tuple


class VideoCompositor:
    """视频合成器 - 使用 ffmpeg 合成素材"""

    def __init__(self):
        self.ffmpeg_path = 'ffmpeg'
        self.ffprobe_path = 'ffprobe'

    def get_video_info(self, video_path: str) -> Dict:
        """
        获取视频信息

        参数:
            video_path: 视频文件路径

        返回:
            视频信息字典
        """
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # 提取视频流信息
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                raise Exception("未找到视频流")

            return {
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'duration': float(data['format']['duration']),
                'fps': eval(video_stream['r_frame_rate'])  # 如 "25/1" -> 25.0
            }

        except Exception as e:
            print(f"  ⚠️  获取视频信息失败: {e}")
            return {
                'width': 1080,
                'height': 1920,
                'duration': 0,
                'fps': 30
            }

    def composite_materials(
        self,
        main_video: str,
        materials: List[Dict],
        output_path: str,
        overlay_position: str = 'center'
    ) -> str:
        """
        将素材合成到主视频中

        参数:
            main_video: 主视频路径
            materials: 素材列表，每个素材包含:
                - material_path: 素材视频路径
                - start_time: 开始时间（秒）
                - duration: 持续时间（秒）
            output_path: 输出视频路径
            overlay_position: 覆盖位置 (center/top/bottom)

        返回:
            输出视频路径
        """
        if not materials:
            print("  ⚠️  没有素材需要合成")
            return main_video

        print(f"  正在合成 {len(materials)} 个素材到视频中...")

        # 获取主视频信息
        main_info = self.get_video_info(main_video)
        main_width = main_info['width']
        main_height = main_info['height']

        # 构建 ffmpeg 命令
        # 策略：使用 overlay 滤镜在指定时间点覆盖素材
        try:
            # 如果只有一个素材，使用简单的方法
            if len(materials) == 1:
                return self._composite_single_material(
                    main_video, materials[0], output_path,
                    main_width, main_height, overlay_position
                )
            else:
                # 多个素材，需要复杂的滤镜链
                return self._composite_multiple_materials(
                    main_video, materials, output_path,
                    main_width, main_height, overlay_position
                )

        except Exception as e:
            print(f"  ❌ 视频合成失败: {e}")
            raise

    def _composite_single_material(
        self,
        main_video: str,
        material: Dict,
        output_path: str,
        main_width: int,
        main_height: int,
        overlay_position: str
    ) -> str:
        """合成单个素材"""
        material_path = material['material_path']
        start_time = material['start_time']
        duration = material['duration']

        # 计算覆盖位置
        x, y = self._calculate_overlay_position(
            overlay_position, main_width, main_height
        )

        # 构建 ffmpeg 命令
        # 滤镜链：
        # 1. 缩放素材到主视频大小
        # 2. 在指定时间点覆盖
        filter_complex = (
            f"[1:v]scale={main_width}:{main_height}[overlay];"
            f"[0:v][overlay]overlay={x}:{y}:enable='between(t,{start_time},{start_time + duration})'"
        )

        cmd = [
            self.ffmpeg_path,
            '-i', main_video,
            '-i', material_path,
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        print(f"  执行 ffmpeg 命令...")
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  ✅ 视频合成完成: {output_path}")

        return output_path

    def _composite_multiple_materials(
        self,
        main_video: str,
        materials: List[Dict],
        output_path: str,
        main_width: int,
        main_height: int,
        overlay_position: str
    ) -> str:
        """合成多个素材"""
        # 计算覆盖位置
        x, y = self._calculate_overlay_position(
            overlay_position, main_width, main_height
        )

        # 构建输入文件列表
        inputs = ['-i', main_video]
        for material in materials:
            inputs.extend(['-i', material['material_path']])

        # 构建滤镜链
        # 策略：先缩放所有素材，然后依次覆盖
        filter_parts = []

        # 缩放所有素材
        for i in range(len(materials)):
            filter_parts.append(
                f"[{i + 1}:v]scale={main_width}:{main_height}[overlay{i}]"
            )

        # 依次覆盖
        current_input = "[0:v]"
        for i, material in enumerate(materials):
            start_time = material['start_time']
            duration = material['duration']
            end_time = start_time + duration

            if i == len(materials) - 1:
                # 最后一个素材，输出到最终结果
                filter_parts.append(
                    f"{current_input}[overlay{i}]overlay={x}:{y}:"
                    f"enable='between(t,{start_time},{end_time})'"
                )
            else:
                # 中间素材，输出到临时标签
                filter_parts.append(
                    f"{current_input}[overlay{i}]overlay={x}:{y}:"
                    f"enable='between(t,{start_time},{end_time})'[tmp{i}]"
                )
                current_input = f"[tmp{i}]"

        filter_complex = ";".join(filter_parts)

        cmd = [
            self.ffmpeg_path,
            *inputs,
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            output_path
        ]

        print(f"  执行 ffmpeg 命令...")
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"  ✅ 视频合成完成: {output_path}")

        return output_path

    def _calculate_overlay_position(
        self,
        position: str,
        main_width: int,
        main_height: int
    ) -> Tuple[str, str]:
        """
        计算覆盖位置

        参数:
            position: 位置 (center/top/bottom/left/right)
            main_width: 主视频宽度
            main_height: 主视频高度

        返回:
            (x, y) 坐标表达式
        """
        if position == 'center':
            return '0', '0'  # 完全覆盖
        elif position == 'top':
            return '0', '0'
        elif position == 'bottom':
            return '0', f'main_h-overlay_h'
        elif position == 'left':
            return '0', '0'
        elif position == 'right':
            return f'main_w-overlay_w', '0'
        else:
            return '0', '0'  # 默认完全覆盖

    def composite_from_subtitle_data(
        self,
        main_video: str,
        subtitle_data: Dict,
        output_path: str,
        overlay_position: str = 'center'
    ) -> str:
        """
        从字幕数据中提取素材信息并合成

        参数:
            main_video: 主视频路径
            subtitle_data: 字幕数据（包含 material_insert 标记）
            output_path: 输出视频路径
            overlay_position: 覆盖位置

        返回:
            输出视频路径
        """
        # 提取素材信息
        subtitles = subtitle_data.get('subtitles', [])
        materials = []

        for subtitle in subtitles:
            if 'material_insert' in subtitle:
                material_info = subtitle['material_insert']
                material_path = material_info.get('material_path')

                if material_path and os.path.exists(material_path):
                    materials.append({
                        'material_path': material_path,
                        'start_time': material_info.get('time_ms', 0) / 1000,  # 转换为秒
                        'duration': material_info.get('duration_ms', 4000) / 1000  # 转换为秒
                    })

        if not materials:
            print("  ⚠️  字幕数据中没有找到素材插入标记")
            return main_video

        print(f"  找到 {len(materials)} 个素材需要合成")

        # 合成视频
        return self.composite_materials(
            main_video, materials, output_path, overlay_position
        )


# ==================== 命令行工具 ====================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='视频合成工具')
    parser.add_argument('main_video', help='主视频路径')
    parser.add_argument('subtitle_json', help='字幕JSON文件路径（包含素材标记）')
    parser.add_argument('-o', '--output', required=True, help='输出视频路径')
    parser.add_argument('--position', default='center',
                       choices=['center', 'top', 'bottom', 'left', 'right'],
                       help='素材覆盖位置')

    args = parser.parse_args()

    # 读取字幕数据
    with open(args.subtitle_json, 'r', encoding='utf-8') as f:
        subtitle_data = json.load(f)

    # 创建合成器
    compositor = VideoCompositor()

    # 合成视频
    print("\n" + "=" * 60)
    print("视频合成")
    print("=" * 60)
    print(f"主视频: {args.main_video}")
    print(f"字幕数据: {args.subtitle_json}")
    print(f"输出路径: {args.output}")
    print(f"覆盖位置: {args.position}")
    print()

    try:
        output_path = compositor.composite_from_subtitle_data(
            args.main_video,
            subtitle_data,
            args.output,
            args.position
        )

        print("\n" + "=" * 60)
        print("✅ 合成完成")
        print("=" * 60)
        print(f"输出文件: {output_path}")

    except Exception as e:
        print(f"\n❌ 合成失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
