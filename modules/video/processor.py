import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用相对导入
from ..asr.local_asr import LocalASR
from ..asr.simple_asr import SimpleASR
from ..content.keyword_analyzer import KeywordAnalyzer
from ..content.material_manager import MaterialManager
from ..audio.background_music_manager import BackgroundMusicManager
from ..audio.audio_processor import AudioProcessor
from ..subtitle.subtitle_json_manager import SubtitleJsonManager
from ..content.title_generator import VideoInfoManager
from .draft_generator import JianyingDraftGenerator
from .video_breath_remover import VideoBreathRemover


class KouboVideoProcessor:
    """口播视频自动处理器"""

    def __init__(self, video_path, template_path=None, output_title=None):
        """
        初始化处理器

        参数:
            video_path: 输入视频路径
            template_path: 模板配置路径（可选，默认使用koubo_default）
            output_title: 输出标题（可选，默认使用视频文件名）
        """
        self.video_path = os.path.abspath(video_path)
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")

        # 设置模板路径
        if template_path is None:
            # 模板文件在项目根目录的 assets/templates/ 下
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_path = os.path.join(
                project_root,
                'assets',
                'templates',
                'koubo_default.json'
            )
        self.template_path = template_path

        # 加载模板配置
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_config = json.load(f)

        # 设置输出标题
        if output_title is None:
            video_name = os.path.splitext(os.path.basename(self.video_path))[0]
            self.output_title = video_name
        else:
            self.output_title = output_title

        self.json_path = None
        self.draft_path = None
        self.audio_path = None  # 添加音频路径属性

        # 初始化本地ASR
        self.local_asr = LocalASR()
        self.simple_asr = SimpleASR()

        # 初始化草稿生成器
        self.draft_generator = JianyingDraftGenerator()

        # 初始化DeepSeek分析器（如果启用）
        self.keyword_analyzer = None
        if self.template_config.get('enable_deepseek', False):
            try:
                self.keyword_analyzer = KeywordAnalyzer()
                print("DeepSeek分析器已启用")
            except Exception as e:
                print(f"DeepSeek分析器初始化失败: {e}")

        # 初始化素材管理器（如果启用）
        self.material_manager = None
        pexels_config = self.template_config.get('pexels_config', {})
        if pexels_config.get('enabled', False):
            try:
                self.material_manager = MaterialManager()
                print("Pexels素材获取器已启用")
            except Exception as e:
                print(f"Pexels获取器初始化失败: {e}")

        # 初始化背景音乐管理器
        self.music_manager = BackgroundMusicManager()
        self.music_config_path = None

        # 初始化字幕JSON管理器
        self.subtitle_json_manager = SubtitleJsonManager()

        # 初始化视频信息管理器
        self.video_info_manager = VideoInfoManager()
        self.video_info_config_path = None

        # 初始化音频处理器
        self.audio_processor = AudioProcessor()

        # 初始化视频去气口处理器
        self.video_breath_remover = VideoBreathRemover()

        # 去气口处理选项
        self.generate_no_breath_audio = False
        self.generate_no_breath_video = False

    def set_background_music(self, music_config_path: str = None, music_segments: list = None):
        """
        设置背景音乐

        参数:
            music_config_path: 音乐配置文件路径（JSON格式）
            music_segments: 音乐片段列表（直接传入）

        注意: music_config_path 和 music_segments 二选一
        """
        if music_config_path:
            # 从文件加载
            self.music_config_path = music_config_path
            print(f"✅ 已加载音乐配置: {music_config_path}")
        elif music_segments:
            # 直接使用传入的配置
            music_config = self.music_manager.create_music_config(music_segments)
            self.template_config['audio_list'] = music_config
            print(f"✅ 已设置 {len(music_config)} 个音乐片段")
        else:
            print("⚠️  未提供音乐配置")

    def set_video_info(self, video_info_config_path: str = None):
        """
        设置视频信息配置

        参数:
            video_info_config_path: 视频信息配置文件路径（JSON格式）
        """
        if video_info_config_path:
            self.video_info_config_path = video_info_config_path
            print(f"✅ 已加载视频信息配置: {video_info_config_path}")
        else:
            print("⚠️  未提供视频信息配置，将使用默认配置")

    def _load_background_music(self):
        """步骤5: 加载背景音乐配置到模板"""
        import time
        start_time = time.time()

        music_segments = 0

        # 优先级1: 从字幕JSON中读取音乐配置
        try:
            music_from_json = self.subtitle_json_manager.get_music_from_json(self.json_path)
            if music_from_json:
                # 处理音乐配置
                music_config = self.music_manager.create_music_config(music_from_json)
                self.template_config['audio_list'] = music_config
                music_segments = len(music_config)
                print(f"  ✅ 从字幕JSON加载 {music_segments} 个音乐片段")

                # 记录处理步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='background_music',
                    status='completed',
                    duration_ms=duration_ms,
                    music_segments=music_segments
                )
                return
        except Exception as e:
            print(f"  ⚠️  从字幕JSON加载音乐失败: {e}")

        # 优先级2: 从单独的音乐配置文件读取
        if self.music_config_path:
            try:
                music_config = self.music_manager.load_music_config_from_file(
                    self.music_config_path
                )
                self.template_config['audio_list'] = music_config
                music_segments = len(music_config)
                print(f"  ✅ 从配置文件加载 {music_segments} 个音乐片段")

                # 记录处理步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='background_music',
                    status='completed',
                    duration_ms=duration_ms,
                    music_segments=music_segments
                )
                return
            except Exception as e:
                print(f"  ⚠️  加载音乐配置失败: {e}")

        # 优先级3: 使用模板中的音乐配置
        if self.template_config.get('audio_list'):
            music_segments = len(self.template_config.get('audio_list', []))
            print(f"  ✅ 使用模板中的音乐配置")

            # 记录处理步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='background_music',
                status='completed',
                duration_ms=duration_ms,
                music_segments=music_segments
            )
        else:
            print(f"  ⚠️  未配置背景音乐")

            # 记录跳过步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='background_music',
                status='skipped',
                duration_ms=duration_ms,
                music_segments=0
            )

    def _apply_video_info(self):
        """步骤5: 应用视频信息（标题、简介、作者信息）"""
        # 加载视频信息配置
        if self.video_info_config_path:
            try:
                video_info_config = self.video_info_manager.load_video_info_config(
                    self.video_info_config_path
                )
            except Exception as e:
                print(f"  ⚠️  加载视频信息配置失败: {e}")
                video_info_config = self.video_info_manager.get_default_config()
        else:
            video_info_config = self.video_info_manager.get_default_config()

        # 加载字幕数据（用于生成标题）
        try:
            data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
            subtitles = data['subtitles']
        except Exception as e:
            print(f"  ⚠️  加载字幕失败: {e}")
            subtitles = []

        # 应用视频信息到模板
        try:
            self.template_config = self.video_info_manager.apply_video_info_to_template(
                self.template_config,
                video_info_config,
                subtitles
            )

            # 显示应用的信息
            if self.template_config.get('title', {}).get('enabled'):
                title_text = self.template_config['title'].get('text', '')
                print(f"  ✅ 视频标题: {title_text}")

            if self.template_config.get('author_info', {}).get('enabled'):
                author_name = self.template_config['author_info'].get('name', '')
                print(f"  ✅ 作者信息: {author_name}")

        except Exception as e:
            print(f"  ⚠️  应用视频信息失败: {e}")

    def process(self):
        """
        执行完整的处理流程

        返回:
            dict: {
                'status': 'success' or 'failed',
                'draft_path': 草稿路径,
                'json_path': 字幕JSON路径,
                'message': 处理信息
            }
        """
        try:
            # 步骤1: 视频转音频
            print("步骤1/8: 视频转音频...")
            self._video_to_audio()

            # 步骤2: 音频转文字（ASR）
            print("步骤2/8: 音频转文字...")
            self._video_to_text()

            # 步骤3: 去气口处理
            print("步骤3/8: 去气口处理...")
            self._remove_breath()

            # 步骤4: 关键词标注
            print("步骤4/8: 关键词标注...")
            self._analyze_keywords()

            # 步骤5: 素材获取与插入
            print("步骤5/9: 素材获取与插入...")
            self._fetch_materials()

            # 步骤6: 视频合成（将素材合成到视频中）
            print("步骤6/9: 视频合成...")
            self._composite_materials()

            # 步骤7: 添加背景音乐
            print("步骤7/9: 添加背景音乐...")
            self._load_background_music()

            # 步骤8: 应用视频信息（标题、简介、作者信息）
            print("步骤8/9: 应用视频信息...")
            self._apply_video_info()

            # 步骤9: 生成剪映草稿
            print("步骤9/9: 生成剪映草稿...")
            self._create_draft()

            print("✅ 处理完成")

            return {
                'status': 'success',
                'draft_path': self.draft_path,
                'json_path': self.json_path,
                'message': '处理完成'
            }
        except Exception as e:
            import traceback
            return {
                'status': 'failed',
                'message': str(e),
                'traceback': traceback.format_exc()
            }

    def _video_to_audio(self):
        """步骤1: 视频转音频"""
        import time
        start_time = time.time()

        folder_path = os.path.dirname(self.video_path)
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]

        # 获取配置
        config = self.subtitle_json_manager.get_config(
            os.path.join(folder_path, f"{video_name}.json"),
            'video_to_audio'
        )
        audio_format = config.get('audio_format', 'wav')

        # 设置音频输出路径
        self.audio_path = os.path.join(folder_path, f"{video_name}.{audio_format}")

        # 检查音频文件是否已存在
        if os.path.exists(self.audio_path):
            print(f"  ✅ 发现已有音频文件: {self.audio_path}")
            print(f"  跳过视频转音频步骤")
            return self.audio_path

        # 提取音频
        try:
            from moviepy.editor import VideoFileClip
            print(f"  正在提取音频...")

            video = VideoFileClip(self.video_path)
            sample_rate = config.get('sample_rate', 44100)

            # 根据格式选择编码器
            if audio_format == 'wav':
                codec = 'pcm_s16le'
            elif audio_format == 'mp3':
                codec = 'libmp3lame'
            else:
                codec = None

            video.audio.write_audiofile(
                self.audio_path,
                fps=sample_rate,
                codec=codec,
                verbose=False,
                logger=None
            )
            video.close()

            print(f"  ✅ 音频提取完成: {self.audio_path}")

        except Exception as e:
            print(f"  ❌ 音频提取失败: {e}")
            raise Exception(f"视频转音频失败: {e}")

        # 记录处理步骤
        duration_ms = int((time.time() - start_time) * 1000)
        if self.json_path and os.path.exists(self.json_path):
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='video_to_audio',
                status='completed',
                duration_ms=duration_ms,
                audio_path=self.audio_path,
                audio_format=audio_format
            )

        return self.audio_path

    def _video_to_text(self):
        """步骤2: 音频转文字（ASR）"""
        import time
        start_time = time.time()

        folder_path = os.path.dirname(self.video_path)
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        self.json_path = os.path.join(folder_path, f"{video_name}.json")

        # 检查是否已有字幕文件
        if os.path.exists(self.json_path):
            print(f"  ✅ 发现已有字幕文件: {self.json_path}")
            print(f"  跳过ASR步骤")
            return

        # 使用本地ASR进行语音识别
        try:
            print("  使用本地ASR进行语音识别...")
            # 优先使用音频文件
            input_file = self.audio_path if self.audio_path and os.path.exists(self.audio_path) else self.video_path

            # 检查是否有可用的ASR方法
            if not self.local_asr.supported_methods:
                print(f"  ⚠️  没有可用的本地ASR方法")
                print(f"\n  请使用以下方式之一提供字幕:")
                print(f"  1. 安装 Whisper: pip install openai-whisper")
                print(f"  2. 手动创建: python3 -m modules.asr.simple_asr template {self.video_path}")
                print(f"  3. 导入SRT:  python3 -m modules.asr.simple_asr srt {self.video_path} <SRT文件>")
                raise Exception("没有可用的ASR方法，请安装 Whisper 或手动提供字幕")

            # 执行ASR
            subtitles = self.local_asr.audio_to_text(input_file)

            # 保存为新格式（包含subtitles键）
            data = {
                'subtitles': subtitles,
                'config': {},
                'processing_steps': []
            }

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"  ✅ ASR完成: {self.json_path}")
            print(f"  共识别 {len(subtitles)} 条字幕")

        except Exception as e:
            print(f"  ❌ ASR失败: {e}")
            print(f"\n  请使用以下方式之一提供字幕:")
            print(f"  1. 安装 Whisper: pip install openai-whisper")
            print(f"  2. 手动创建: python3 -m modules.asr.simple_asr template {self.video_path}")
            print(f"  3. 导入SRT:  python3 -m modules.asr.simple_asr srt {self.video_path} <SRT文件>")
            raise Exception(f"ASR失败: {e}")

        if not os.path.exists(self.json_path):
            raise Exception("ASR处理失败，未生成字幕文件")

        # 记录处理步骤
        duration_ms = int((time.time() - start_time) * 1000)
        self.subtitle_json_manager.add_processing_step(
            self.json_path,
            step='asr',
            status='completed',
            duration_ms=duration_ms
        )

    def _remove_breath(self):
        """步骤3: 去气口处理"""
        import time
        start_time = time.time()

        # 加载配置
        config = self.subtitle_json_manager.get_config(self.json_path, 'breath_removal')
        if not config.get('enabled', True):
            print("  ⏭️  跳过去气口处理")
            return

        # 使用新的JSON管理器加载数据
        data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
        subtitles = data['subtitles']

        # 导入去气口处理器
        from modules.audio.breath_remover import BreathRemover
        breath_remover = BreathRemover()

        # 获取配置参数
        max_gap = config.get('max_gap', 500) / 1000  # 转换为秒，默认0.5秒

        # 执行去气口检测（基于字间间隔）
        print(f"  使用字间间隔检测（最大间隔: {max_gap}秒）")
        subtitles, removed_count = breath_remover.remove_breaths_by_interval(
            subtitles, max_gap
        )

        # 保存更新后的字幕
        data['subtitles'] = subtitles
        self.subtitle_json_manager.save_subtitle_json(self.json_path, data)

        # 统计信息
        total = len(subtitles)
        print(f"  总字幕数: {total}")
        print(f"  气口片段: {removed_count}")
        print(f"  保留片段: {total - removed_count}")

        # 生成去气口音频（如果启用）
        if config.get('generate_audio', False) and self.audio_path:
            try:
                print(f"\n  正在生成去气口音频...")
                no_breath_audio = self.audio_processor.remove_breath_segments(
                    self.audio_path,
                    subtitles
                )
                print(f"  ✅ 去气口音频: {no_breath_audio}")
            except Exception as e:
                print(f"  ⚠️  生成去气口音频失败: {e}")

        # 生成去气口视频（如果启用）
        if config.get('generate_video', False):
            try:
                print(f"\n  正在生成去气口视频...")
                no_breath_video = self.video_breath_remover.remove_breath_segments(
                    self.video_path,
                    subtitles
                )
                print(f"  ✅ 去气口视频: {no_breath_video}")
            except Exception as e:
                print(f"  ⚠️  生成去气口视频失败: {e}")

        # 记录处理步骤
        duration_ms = int((time.time() - start_time) * 1000)
        self.subtitle_json_manager.add_processing_step(
            self.json_path,
            step='breath_removal',
            status='completed',
            duration_ms=duration_ms,
            removed_count=removed_count
        )

    def _analyze_keywords(self):
        """步骤4: 生成关键字并贴入字幕，保存到JSON"""
        import time
        start_time = time.time()

        # 加载配置
        config = self.subtitle_json_manager.get_config(self.json_path, 'deepseek')
        if not config.get('enabled', True):
            print("  ⏭️  跳过关键词标注")
            return

        # 使用DeepSeek标注关键词
        if self.keyword_analyzer:
            try:
                print("  [1/3] 正在使用DeepSeek生成关键词...")

                # 加载数据
                data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
                subtitles = data['subtitles']

                # 分析关键词
                print("  [2/3] 正在分析字幕内容并提取关键词...")
                subtitles = self.keyword_analyzer.analyze_keywords(subtitles)

                # 统计关键词数量
                keyword_count = sum(1 for s in subtitles if s.get('keyword'))
                keywords_in_text = sum(1 for s in subtitles if s.get('keywords'))

                print(f"  ✅ 生成关键词: {keyword_count}个")
                print(f"  ✅ 关键词已贴入字幕: {keywords_in_text}条")

                # 更新数据
                data['subtitles'] = subtitles

                # 保存更新后的字幕（保持新格式）
                print("  [3/3] 正在保存字幕到JSON...")
                self.subtitle_json_manager.save_subtitle_json(
                    self.json_path, data, backup=False
                )
                print(f"  ✅ 字幕已保存到: {self.json_path}")

                # 记录处理步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='deepseek_keywords',
                    status='completed',
                    duration_ms=duration_ms,
                    keywords_count=keyword_count
                )

            except Exception as e:
                print(f"  ❌ DeepSeek标注失败: {e}")
                # 记录失败步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='deepseek_keywords',
                    status='failed',
                    duration_ms=duration_ms,
                    error=str(e)
                )
        else:
            print("  ⏭️  DeepSeek分析器未启用")

    def _process_subtitles(self):
        """步骤2: 处理字幕数据，去除气口 + DeepSeek关键词标注（已废弃，保留用于兼容）"""
        # 使用新的JSON管理器加载数据
        data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
        subtitles = data['subtitles']

        # 统计信息
        total = len(subtitles)
        removed_count = sum(1 for s in subtitles if s.get('removed') == 1)

        print(f"  总字幕数: {total}")
        print(f"  气口片段: {removed_count}")
        print(f"  保留片段: {total - removed_count}")

        # 使用DeepSeek标注关键词
        if self.keyword_analyzer:
            try:
                print("  正在使用DeepSeek标注关键词...")
                subtitles = self.keyword_analyzer.analyze_keywords(subtitles)

                # 统计关键词数量
                keyword_count = sum(1 for s in subtitles if s.get('keyword'))
                print(f"  标注关键词: {keyword_count}个")

                # 更新数据
                data['subtitles'] = subtitles

                # 保存更新后的字幕（保持新格式）
                self.subtitle_json_manager.save_subtitle_json(
                    self.json_path, data, backup=False
                )

            except Exception as e:
                print(f"  DeepSeek标注失败: {e}")

    def _fetch_materials(self):
        """步骤5: 获取Pexels素材并插入到JSON"""
        import time
        start_time = time.time()

        # 加载配置
        pexels_config = self.template_config.get('pexels_config', {})

        if not pexels_config.get('enabled', False):
            print("  ⏭️  素材插入未启用")
            # 记录跳过步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='material_insertion',
                status='skipped',
                duration_ms=duration_ms
            )
            return

        if not self.material_manager:
            print("  ⚠️  素材管理器未初始化")
            return

        try:
            # 加载字幕数据
            data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
            subtitles = data['subtitles']

            print(f"  正在分析素材插入点...")

            # 插入素材
            subtitles, materials = self.material_manager.insert_materials(
                subtitles, pexels_config
            )

            if materials:
                print(f"  ✅ 成功插入 {len(materials)} 个素材")

                # 更新数据
                data['subtitles'] = subtitles

                # 将素材信息也保存到 JSON 中
                if 'materials' not in data:
                    data['materials'] = []
                data['materials'].extend(materials)

                # 保存更新后的字幕
                self.subtitle_json_manager.save_subtitle_json(
                    self.json_path, data, backup=False
                )

                # 记录处理步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='material_insertion',
                    status='completed',
                    duration_ms=duration_ms,
                    materials_count=len(materials)
                )
            else:
                print(f"  ⚠️  未获取到素材")
                # 记录处理步骤
                duration_ms = int((time.time() - start_time) * 1000)
                self.subtitle_json_manager.add_processing_step(
                    self.json_path,
                    step='material_insertion',
                    status='completed',
                    duration_ms=duration_ms,
                    materials_count=0
                )

        except Exception as e:
            print(f"  ❌ 素材获取失败: {e}")
            # 记录失败步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='material_insertion',
                status='failed',
                duration_ms=duration_ms,
                error=str(e)
            )
            import traceback
            traceback.print_exc()

    def _composite_materials(self):
        """步骤6: 视频合成 - 将素材合成到视频中"""
        import time
        start_time = time.time()

        # 检查配置
        pexels_config = self.template_config.get('pexels_config', {})
        if not pexels_config.get('enabled', False):
            print("  ⏭️  素材插入未启用，跳过视频合成")
            return

        # 检查是否启用视频合成
        if not pexels_config.get('composite_video', True):
            print("  ⏭️  视频合成未启用")
            return

        try:
            # 加载字幕数据
            data = self.subtitle_json_manager.load_subtitle_json(self.json_path)

            # 检查是否有素材
            materials = data.get('materials', [])
            if not materials:
                print("  ⚠️  没有素材需要合成")
                return

            print(f"  找到 {len(materials)} 个素材需要合成")

            # 导入视频合成器
            from modules.video.video_compositor import VideoCompositor
            compositor = VideoCompositor()

            # 生成输出路径
            video_dir = os.path.dirname(self.video_path)
            video_name = os.path.splitext(os.path.basename(self.video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}_with_materials.mp4")

            # 获取覆盖位置配置
            overlay_position = pexels_config.get('overlay_position', 'center')

            # 合成视频
            print(f"  正在合成视频...")
            composited_video = compositor.composite_from_subtitle_data(
                self.video_path,
                data,
                output_path,
                overlay_position
            )

            # 更新视频路径为合成后的视频
            self.video_path = composited_video
            print(f"  ✅ 视频合成完成: {composited_video}")

            # 记录处理步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='video_composition',
                status='completed',
                duration_ms=duration_ms,
                output_video=composited_video
            )

        except Exception as e:
            print(f"  ⚠️  视频合成失败: {e}")
            print(f"  将使用原始视频继续处理")
            # 记录失败步骤
            duration_ms = int((time.time() - start_time) * 1000)
            self.subtitle_json_manager.add_processing_step(
                self.json_path,
                step='video_composition',
                status='failed',
                duration_ms=duration_ms,
                error=str(e)
            )
            import traceback
            traceback.print_exc()

    def _create_draft(self):
        """步骤7: 生成剪映草稿"""
        try:
            # 使用独立的草稿生成器
            self.draft_path = self.draft_generator.create_draft(
                video_path=self.video_path,
                json_path=self.json_path,
                template_config=self.template_config,
                output_title=self.output_title
            )

            print(f"  ✅ 草稿已生成: {self.draft_path}")

        except Exception as e:
            raise Exception(f"草稿生成失败: {e}")
