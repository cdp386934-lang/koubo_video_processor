#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地ASR实现 - 使用开源语音识别库
"""
import os
import json
import subprocess
from pathlib import Path


class LocalASR:
    """本地ASR服务"""

    def __init__(self):
        self.supported_methods = []
        self._check_available_methods()

    def _check_available_methods(self):
        """检查可用的ASR方法"""
        # 检查是否安装了 whisper
        try:
            import whisper
            self.supported_methods.append('whisper')
        except ImportError:
            pass

        # 检查是否安装了 speech_recognition
        try:
            import speech_recognition
            self.supported_methods.append('speech_recognition')
        except ImportError:
            pass

    def audio_to_text(self, audio_path, method='auto'):
        """
        音频转文字

        参数:
            audio_path: 音频文件路径
            method: 使用的方法 ('auto', 'whisper', 'speech_recognition')

        返回:
            字幕列表
        """
        if method == 'auto':
            if 'whisper' in self.supported_methods:
                method = 'whisper'
            elif 'speech_recognition' in self.supported_methods:
                method = 'speech_recognition'
            else:
                raise Exception("没有可用的ASR方法，请安装: pip install openai-whisper 或 pip install SpeechRecognition")

        if method == 'whisper':
            return self._whisper_asr(audio_path)
        elif method == 'speech_recognition':
            return self._speech_recognition_asr(audio_path)
        else:
            raise Exception(f"不支持的方法: {method}")

    def _whisper_asr(self, audio_path):
        """使用 Whisper 进行ASR"""
        try:
            import whisper
            print("  使用 Whisper 模型进行语音识别...")
            print("  正在加载模型（首次使用会下载模型文件）...")

            # 加载模型（base模型，平衡速度和准确度）
            model = whisper.load_model("base")

            print("  正在识别音频...")
            result = model.transcribe(
                audio_path,
                language='zh',  # 中文
                verbose=False
            )

            # 转换为标准格式
            subtitles = []
            for segment in result['segments']:
                subtitle = {
                    'FinalSentence': segment['text'].strip(),
                    'Text': segment['text'].strip(),
                    'StartMs': int(segment['start'] * 1000),
                    'EndMs': int(segment['end'] * 1000),
                    'keyword': '',
                    'text_grade': 1,
                    'video_grade': 1,
                    'removed': self._is_filler(segment['text'])
                }
                subtitles.append(subtitle)

            return subtitles

        except Exception as e:
            raise Exception(f"Whisper ASR失败: {e}")

    def _speech_recognition_asr(self, audio_path):
        """使用 SpeechRecognition 进行ASR"""
        try:
            import speech_recognition as sr
            print("  使用 SpeechRecognition 进行语音识别...")

            recognizer = sr.Recognizer()

            # 读取音频文件
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)

            # 使用Google Speech Recognition
            print("  正在识别音频...")
            text = recognizer.recognize_google(audio, language='zh-CN')

            # 简单分句（按标点符号）
            sentences = self._split_sentences(text)

            # 估算时间戳
            subtitles = []
            current_time = 0
            for sentence in sentences:
                duration = len(sentence) * 300  # 每字约300ms

                subtitle = {
                    'FinalSentence': sentence,
                    'Text': sentence,
                    'StartMs': current_time,
                    'EndMs': current_time + duration,
                    'keyword': '',
                    'text_grade': 1,
                    'video_grade': 1,
                    'removed': self._is_filler(sentence)
                }
                subtitles.append(subtitle)
                current_time += duration + 200  # 加200ms间隔

            return subtitles

        except Exception as e:
            raise Exception(f"SpeechRecognition ASR失败: {e}")

    def _is_filler(self, text):
        """判断是否为气口/填充词"""
        fillers = ['嗯', '啊', '呃', '哦', '额', '这个', '那个', '就是', '然后']
        text = text.strip()

        # 如果文本很短且是填充词
        if len(text) <= 3:
            for filler in fillers:
                if filler in text:
                    return 1

        return 0

    def _split_sentences(self, text):
        """简单分句"""
        import re
        # 按标点符号分句
        sentences = re.split(r'[。！？\n]', text)
        return [s.strip() for s in sentences if s.strip()]


def audio_to_text_local(audio_path, output_path=None):
    """
    本地音频转文字

    参数:
        audio_path: 音频文件路径
        output_path: 输出JSON路径（可选）

    返回:
        字幕JSON文件路径
    """
    print("=" * 60)
    print("本地ASR - 音频转文字")
    print("=" * 60)
    print()

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    # 初始化ASR
    asr = LocalASR()

    if not asr.supported_methods:
        print("❌ 没有可用的ASR方法")
        print()
        print("请安装以下任一库：")
        print("1. Whisper (推荐): pip install openai-whisper")
        print("2. SpeechRecognition: pip install SpeechRecognition")
        print()
        raise Exception("没有可用的ASR方法")

    print(f"可用方法: {', '.join(asr.supported_methods)}")
    print()

    # 执行ASR
    subtitles = asr.audio_to_text(audio_path)

    print(f"✅ 识别完成，共 {len(subtitles)} 条字幕")

    # 统计气口
    removed_count = sum(1 for s in subtitles if s.get('removed') == 1)
    print(f"   气口片段: {removed_count}")
    print(f"   有效片段: {len(subtitles) - removed_count}")
    print()

    # 保存JSON
    if output_path is None:
        audio_dir = os.path.dirname(audio_path)
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(audio_dir, f"{audio_name}.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subtitles, f, ensure_ascii=False, indent=2)

    print(f"✅ 字幕文件已保存: {output_path}")
    print()

    return output_path


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 local_asr.py <音频文件路径>")
        sys.exit(1)

    audio_path = sys.argv[1]

    try:
        json_path = audio_to_text_local(audio_path)
        print("=" * 60)
        print("✅ 完成！")
        print("=" * 60)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
