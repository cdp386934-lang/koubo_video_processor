#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去气口功能模块 - 整合所有去气口相关功能
"""
import os
import json
import re
from typing import List, Dict, Tuple, Optional


class BreathRemover:
    """统一的去气口处理器"""

    def __init__(self):
        # 常见的气口词/填充词
        self.filler_words = [
            # 单字气口
            '嗯', '啊', '呃', '哦', '额', '诶', '唉',
            # 双字气口
            '这个', '那个', '就是', '然后', '所以', '因为',
            '嗯嗯', '啊啊', '呃呃',
            # 三字气口
            '就是说', '怎么说', '你知道',
            # 其他
            '嗯哼', '嗯呐', '对对对', '是是是', '好好好'
        ]

        # 气口的特征
        self.breath_patterns = [
            r'^[嗯啊呃哦额诶唉]+$',  # 纯气口音
            r'^[嗯啊呃哦额]{1,2}[，。、]?$',  # 气口+标点
        ]

        # 检查音频分析库是否可用
        self.audio_analyzer_available = False
        self._check_audio_libs()

    def _check_audio_libs(self):
        """检查音频处理库是否可用"""
        try:
            import librosa
            import numpy as np
            self.audio_analyzer_available = True
        except ImportError:
            pass

    # ==================== 基础检测方法 ====================

    def detect_breath_in_subtitle(self, subtitle: Dict) -> bool:
        """
        检测单条字幕是否为气口

        参数:
            subtitle: 字幕字典

        返回:
            True表示是气口，False表示不是
        """
        text = subtitle.get('Text', '').strip()
        final_sentence = subtitle.get('FinalSentence', '').strip()

        # 检查文本长度
        if len(text) == 0:
            return True

        # 检查是否匹配气口模式
        for pattern in self.breath_patterns:
            if re.match(pattern, text):
                return True

        # 检查是否在填充词列表中
        if text in self.filler_words:
            return True

        # 检查时长（气口通常很短）
        duration = subtitle.get('EndMs', 0) - subtitle.get('StartMs', 0)
        if duration < 300 and len(text) <= 2:  # 小于300ms且文字很少
            return True

        return False

    def remove_breaths_from_subtitles(self, subtitles: List[Dict]) -> Tuple[List[Dict], int]:
        """
        从字幕列表中标记气口片段

        参数:
            subtitles: 字幕列表

        返回:
            (处理后的字幕列表, 气口数量)
        """
        removed_count = 0

        for subtitle in subtitles:
            # 如果已经标记为removed，跳过
            if subtitle.get('removed') == 1:
                removed_count += 1
                continue

            # 检测是否为气口
            if self.detect_breath_in_subtitle(subtitle):
                subtitle['removed'] = 1
                removed_count += 1

        return subtitles, removed_count

    # ==================== 高级去气口方法 ====================

    def remove_breaths_by_interval(
        self,
        subtitles: List[Dict],
        max_interval_sec: float = 0.5
    ) -> Tuple[List[Dict], int]:
        """
        基于字间间隔的高级去气口

        检测每个字幕片段之间的间隔，如果间隔小于指定阈值，
        且当前片段符合气口特征，则标记为气口（removed=1）

        参数:
            subtitles: 字幕列表
            max_interval_sec: 最大允许间隔（秒），默认0.5秒
                            只有间隔小于此值时才考虑去除气口

        返回:
            (处理后的字幕列表, 气口数量)
        """
        if not subtitles or len(subtitles) < 2:
            return subtitles, 0

        max_interval_ms = max_interval_sec * 1000  # 转换为毫秒
        removed_count = 0

        # 遍历相邻的字幕片段
        for i in range(len(subtitles) - 1):
            current = subtitles[i]
            next_subtitle = subtitles[i + 1]

            # 如果当前片段已经被标记为removed，跳过
            if current.get('removed') == 1:
                removed_count += 1
                continue

            # 计算当前片段结束时间和下一个片段开始时间的间隔
            current_end = current.get('EndMs', 0)
            next_start = next_subtitle.get('StartMs', 0)
            interval = next_start - current_end

            # 只有当间隔小于阈值时，才检查是否为气口
            if interval < max_interval_ms:
                # 检查当前片段是否符合气口特征
                if self.detect_breath_in_subtitle(current):
                    current['removed'] = 1
                    removed_count += 1

        # 检查最后一个片段是否已被标记
        if subtitles[-1].get('removed') == 1:
            removed_count += 1

        return subtitles, removed_count

    # ==================== 高级音频分析方法 ====================

    def analyze_audio_breaths(self, audio_path: str, subtitles: List[Dict]) -> List[int]:
        """
        基于音频分析检测气口

        参数:
            audio_path: 音频文件路径
            subtitles: 字幕列表

        返回:
            气口片段的索引列表
        """
        if not self.audio_analyzer_available:
            print("  ⚠️  音频分析库未安装，跳过音频分析")
            print("     安装方法: pip install librosa numpy")
            return []

        try:
            import librosa
            import numpy as np

            print("  正在加载音频文件...")
            y, sr = librosa.load(audio_path, sr=None)

            breath_indices = []

            for idx, subtitle in enumerate(subtitles):
                start_ms = subtitle.get('StartMs', 0)
                end_ms = subtitle.get('EndMs', 0)

                # 转换为样本索引
                start_sample = int(start_ms * sr / 1000)
                end_sample = int(end_ms * sr / 1000)

                # 提取音频片段
                audio_segment = y[start_sample:end_sample]

                if len(audio_segment) == 0:
                    continue

                # 计算能量
                energy = np.sum(audio_segment ** 2) / len(audio_segment)

                # 计算过零率
                zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_segment)))) / len(audio_segment)

                # 气口特征：低能量 + 高过零率
                if energy < 0.001 and zero_crossings > 0.1:
                    breath_indices.append(idx)

            print(f"  音频分析检测到 {len(breath_indices)} 个气口")
            return breath_indices

        except Exception as e:
            print(f"  ⚠️  音频分析失败: {e}")
            return []

    def remove_breaths_with_audio_analysis(
        self,
        audio_path: str,
        subtitles: List[Dict]
    ) -> Tuple[List[Dict], int]:
        """
        结合音频分析和文本检测去除气口

        参数:
            audio_path: 音频文件路径
            subtitles: 字幕列表

        返回:
            (处理后的字幕列表, 气口数量)
        """
        # 先进行文本检测
        subtitles, text_removed = self.remove_breaths_from_subtitles(subtitles)

        # 如果音频分析可用，进行音频分析
        if self.audio_analyzer_available and os.path.exists(audio_path):
            audio_breath_indices = self.analyze_audio_breaths(audio_path, subtitles)

            # 标记音频分析检测到的气口
            for idx in audio_breath_indices:
                if subtitles[idx].get('removed') != 1:
                    subtitles[idx]['removed'] = 1

        # 统计总气口数
        removed_count = sum(1 for s in subtitles if s.get('removed') == 1)

        return subtitles, removed_count

    # ==================== 手动标记方法 ====================

    def mark_breath_manually(self, subtitles: List[Dict], indices: List[int]) -> List[Dict]:
        """
        手动标记指定索引的字幕为气口

        参数:
            subtitles: 字幕列表
            indices: 要标记为气口的索引列表

        返回:
            处理后的字幕列表
        """
        for idx in indices:
            if 0 <= idx < len(subtitles):
                subtitles[idx]['removed'] = 1

        return subtitles

    def unmark_breath(self, subtitles: List[Dict], indices: List[int]) -> List[Dict]:
        """
        取消标记指定索引的气口

        参数:
            subtitles: 字幕列表
            indices: 要取消标记的索引列表

        返回:
            处理后的字幕列表
        """
        for idx in indices:
            if 0 <= idx < len(subtitles):
                subtitles[idx]['removed'] = 0

        return subtitles

    # ==================== 统计和报告方法 ====================

    def get_breath_statistics(self, subtitles: List[Dict]) -> Dict:
        """
        获取气口统计信息

        参数:
            subtitles: 字幕列表

        返回:
            统计信息字典
        """
        total = len(subtitles)
        removed = sum(1 for s in subtitles if s.get('removed') == 1)
        kept = total - removed

        # 计算气口总时长
        breath_duration = sum(
            s.get('EndMs', 0) - s.get('StartMs', 0)
            for s in subtitles if s.get('removed') == 1
        )

        # 计算保留内容总时长
        kept_duration = sum(
            s.get('EndMs', 0) - s.get('StartMs', 0)
            for s in subtitles if s.get('removed') != 1
        )

        return {
            'total_count': total,
            'removed_count': removed,
            'kept_count': kept,
            'removal_rate': removed / total if total > 0 else 0,
            'breath_duration_ms': breath_duration,
            'kept_duration_ms': kept_duration,
            'breath_duration_sec': breath_duration / 1000,
            'kept_duration_sec': kept_duration / 1000
        }

    def print_statistics(self, stats_or_subtitles):
        """
        打印气口统计信息

        参数:
            stats_or_subtitles: 统计字典或字幕列表
        """
        # 如果传入的是字典（统计信息），直接使用
        if isinstance(stats_or_subtitles, dict):
            stats = stats_or_subtitles
        else:
            # 如果传入的是列表（字幕），计算统计信息
            stats = self.get_breath_statistics(stats_or_subtitles)

        print(f"  总字幕数: {stats['total_count']}")
        print(f"  气口片段: {stats['removed_count']}")
        print(f"  保留片段: {stats['kept_count']}")
        print(f"  去除率: {stats['removal_rate']:.1%}")
        print(f"  气口时长: {stats['breath_duration_sec']:.1f}秒")
        print(f"  保留时长: {stats['kept_duration_sec']:.1f}秒")

    # ==================== 文件处理方法 ====================

    def process_subtitle_file(
        self,
        json_path: str,
        audio_path: Optional[str] = None,
        use_audio_analysis: bool = False,
        use_interval_detection: bool = False,
        max_interval_sec: float = 0.5
    ) -> Dict:
        """
        处理字幕JSON文件

        参数:
            json_path: 字幕JSON文件路径
            audio_path: 音频文件路径（可选）
            use_audio_analysis: 是否使用音频分析
            use_interval_detection: 是否使用字间间隔检测
            max_interval_sec: 最大允许间隔（秒），默认0.5秒

        返回:
            处理结果字典
        """
        # 读取字幕文件
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 兼容新旧格式
        if isinstance(data, dict) and 'subtitles' in data:
            subtitles = data['subtitles']
        else:
            subtitles = data

        # 处理气口
        if use_interval_detection:
            # 使用字间间隔检测
            subtitles, removed_count = self.remove_breaths_by_interval(
                subtitles, max_interval_sec
            )
        elif use_audio_analysis and audio_path:
            # 使用音频分析
            subtitles, removed_count = self.remove_breaths_with_audio_analysis(
                audio_path, subtitles
            )
        else:
            # 使用基础文本检测
            subtitles, removed_count = self.remove_breaths_from_subtitles(subtitles)

        # 保存回文件
        if isinstance(data, dict) and 'subtitles' in data:
            data['subtitles'] = subtitles
        else:
            data = subtitles

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 获取统计信息
        stats = self.get_breath_statistics(subtitles)

        return {
            'status': 'success',
            'json_path': json_path,
            'statistics': stats
        }


# ==================== 命令行工具 ====================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='去气口工具')
    parser.add_argument('json_path', help='字幕JSON文件路径')
    parser.add_argument('--audio', help='音频文件路径（用于音频分析）')
    parser.add_argument('--audio-analysis', action='store_true', help='启用音频分析')
    parser.add_argument('--interval', action='store_true', help='启用字间间隔检测')
    parser.add_argument('--max-interval', type=float, default=0.5,
                       help='最大允许间隔（秒），默认0.5秒')
    parser.add_argument('--stats', action='store_true', help='只显示统计信息')

    args = parser.parse_args()

    remover = BreathRemover()

    if args.stats:
        # 只显示统计信息
        with open(args.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'subtitles' in data:
            subtitles = data['subtitles']
        else:
            subtitles = data

        print("\n气口统计信息:")
        print("=" * 60)
        remover.print_statistics(subtitles)
        print("=" * 60)
    else:
        # 处理文件
        print(f"\n处理文件: {args.json_path}")
        print("=" * 60)

        if args.interval:
            print(f"使用字间间隔检测（最大间隔: {args.max_interval}秒）")
        elif args.audio_analysis:
            print("使用音频分析")
        else:
            print("使用基础文本检测")

        print()

        result = remover.process_subtitle_file(
            args.json_path,
            args.audio,
            args.audio_analysis,
            args.interval,
            args.max_interval
        )

        print("\n处理完成!")
        print("=" * 60)
        remover.print_statistics(result['statistics'])
        print("=" * 60)


if __name__ == '__main__':
    main()

