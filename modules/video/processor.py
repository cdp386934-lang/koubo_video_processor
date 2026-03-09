import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用相对导入
from ..api.api_client import get_api_client
from ..content.keyword_analyzer import KeywordAnalyzer
from ..content.material_manager import MaterialManager
from ..audio.background_music_manager import BackgroundMusicManager
from ..subtitle.subtitle_json_manager import SubtitleJsonManager
from ..content.title_generator import VideoInfoManager


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

        # 初始化API客户端
        self.api_client = get_api_client()

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
            print("步骤1/7: 视频转音频...")
            self._video_to_audio()

            # 步骤2: 音频转文字（ASR）
            print("步骤2/7: 音频转文字...")
            self._video_to_text()

            # 步骤3: 去气口处理
            print("步骤3/7: 去气口处理...")
            self._remove_breath()

            # 步骤4: DeepSeek 关键词标注
            print("步骤4/7: 关键词标注...")
            self._analyze_keywords()

            # 步骤5: 添加背景音乐
            print("步骤5/7: 添加背景音乐...")
            self._load_background_music()

            # 步骤6: 应用视频信息（标题、简介、作者信息）
            print("步骤6/7: 应用视频信息...")
            self._apply_video_info()

            # 步骤7: 生成剪映草稿
            print("步骤7/7: 生成剪映草稿...")
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

        # 使用API客户端调用ASR服务（传入音频路径或视频路径）
        try:
            print("  调用ASR服务...")
            # 优先使用音频文件，如果不存在则使用视频文件
            input_file = self.audio_path if self.audio_path and os.path.exists(self.audio_path) else self.video_path
            json_path = self.api_client.video_to_text(input_file)
            self.json_path = json_path
            print(f"  ✅ ASR完成: {self.json_path}")
        except Exception as e:
            print(f"  ❌ ASR失败: {e}")
            print(f"\n  请使用以下方式之一提供字幕:")
            print(f"  1. 手动创建: python3 simple_asr.py template {self.video_path}")
            print(f"  2. 导入SRT:  python3 simple_asr.py srt {self.video_path} <SRT文件>")
            print(f"  3. 使用剪映导出字幕后，放在: {self.json_path}")
            raise Exception("ASR失败，请手动提供字幕文件")

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

        # 统计信息
        total = len(subtitles)
        removed_count = sum(1 for s in subtitles if s.get('removed') == 1)

        print(f"  总字幕数: {total}")
        print(f"  气口片段: {removed_count}")
        print(f"  保留片段: {total - removed_count}")

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
        """步骤4: DeepSeek 关键词标注"""
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
                print("  正在使用DeepSeek标注关键词...")

                # 加载数据
                data = self.subtitle_json_manager.load_subtitle_json(self.json_path)
                subtitles = data['subtitles']

                # 分析关键词
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
                print(f"  DeepSeek标注失败: {e}")
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
        """步骤3: 获取Pexels素材"""
        if not self.material_manager:
            print("  Pexels素材功能未启用，跳过")
            return

        try:
            # 读取字幕数据
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 兼容新旧格式
            if isinstance(data, dict) and 'subtitles' in data:
                subtitles = data['subtitles']
            else:
                subtitles = data

            # 获取配置
            pexels_config = self.template_config.get('pexels_config', {})

            # 插入素材
            subtitles, materials = self.material_manager.insert_materials(
                subtitles, pexels_config
            )

            if materials:
                print(f"  成功插入 {len(materials)} 个素材")

                # 保存更新后的字幕
                if isinstance(data, dict) and 'subtitles' in data:
                    data['subtitles'] = subtitles
                else:
                    data = subtitles

                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # 保存更新后的字幕
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(subtitles, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"  素材获取失败: {e}")
            import traceback
            traceback.print_exc()

    def _create_draft(self):
        """步骤3: 生成剪映草稿"""
        # 将视频和字幕复制到剪映缓存目录，确保剪映可以访问
        import shutil
        jianying_cache = os.path.expanduser("~/Movies/JianyingPro/User Data/Cache/VideoAlgorithm")
        os.makedirs(jianying_cache, exist_ok=True)

        video_filename = os.path.basename(self.video_path)
        cached_video_path = os.path.join(jianying_cache, video_filename)

        # 复制视频到缓存目录
        if not os.path.exists(cached_video_path):
            print(f"  复制视频到剪映缓存目录...")
            shutil.copy2(self.video_path, cached_video_path)

        # 复制字幕JSON到缓存目录（转换为旧格式）
        json_filename = os.path.basename(self.json_path)
        cached_json_path = os.path.join(jianying_cache, json_filename)

        # 读取JSON并转换格式
        with open(self.json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # 如果是新格式，转换为旧格式
        if isinstance(json_data, dict) and 'subtitles' in json_data:
            json_data = json_data['subtitles']

        # 保存为旧格式
        with open(cached_json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # 使用API客户端调用草稿生成服务，使用缓存路径
        try:
            self.draft_path = self.api_client.create_draft(
                video_path=cached_video_path,
                json_path=cached_json_path,
                template_config=self.template_config,
                output_title=self.output_title
            )
            print(f"  ✅ 草稿已生成: {self.draft_path}")

            # 添加标题和作者信息
            if self.draft_path:
                self._add_custom_texts_to_draft()

        except Exception as e:
            raise Exception(f"草稿生成失败: {e}")

    def _add_custom_texts_to_draft(self):
        """在草稿中添加自定义标题和作者信息"""
        try:
            # 导入必要的模块
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from service.editor import Draft
            from service.clips.text_clip import TextClip

            # 读取字幕数据获取总时长
            with open(self.json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if isinstance(json_data, dict) and 'subtitles' in json_data:
                subtitles = json_data['subtitles']
            else:
                subtitles = json_data

            # 计算总时长（微秒）
            if subtitles:
                total_duration_ms = max(s.get('EndMs', 0) for s in subtitles)
                total_duration_us = total_duration_ms * 1000  # 转换为微秒
            else:
                total_duration_us = 10000000  # 默认10秒

            # 打开草稿
            draft = Draft(self.draft_path)

            # 画布尺寸（竖屏9:16）
            canvas = [1080, 1920]

            # 添加标题
            if self.template_config.get('title', {}).get('enabled'):
                title_config = self.template_config['title']
                title_text = title_config.get('text', '')

                if title_text:
                    print(f"  添加标题: {title_text[:20]}...")

                    # 创建标题文本
                    title_clip = TextClip(title_text)
                    title_clip.set_font_size(title_config.get('font_size', 16))
                    title_clip.set_color(title_config.get('color', '#000000'))

                    # 设置位置
                    x_pos = title_config.get('x_position', 0)
                    y_pos = title_config.get('y_position', -800)
                    title_clip.set_transform(canvas, x_pos, y_pos)

                    # 设置时长
                    title_clip.segment.set_duration(total_duration_us)

                    # 设置阴影
                    has_shadow = title_config.get('has_shadow', '关闭') == '开启'
                    title_clip.set_shadow(has_shadow)

                    # 添加到草稿
                    draft.add_clip_to_track(title_clip, index=1)
                    print(f"  ✅ 标题已添加")

            # 添加作者信息
            if self.template_config.get('author_info', {}).get('enabled'):
                author_config = self.template_config['author_info']
                author_name = author_config.get('name', '')
                author_title = author_config.get('title', '')
                author_subtitle = author_config.get('subtitle', '')

                # 组合作者信息文本
                author_lines = []
                if author_name:
                    author_lines.append(author_name)
                if author_title:
                    author_lines.append(author_title)
                if author_subtitle:
                    author_lines.append(author_subtitle)
                author_text = '\n'.join(author_lines)

                if author_text:
                    print(f"  添加作者信息: {author_name}")

                    # 创建作者信息文本
                    author_clip = TextClip(author_text)
                    author_clip.set_font_size(author_config.get('font_size', 10))
                    author_clip.set_color(author_config.get('color', '#000000'))

                    # 设置位置
                    x_pos = author_config.get('x_position', 0)
                    y_pos = author_config.get('y_position', 800)
                    author_clip.set_transform(canvas, x_pos, y_pos)

                    # 设置时长
                    author_clip.segment.set_duration(total_duration_us)

                    # 设置阴影
                    has_shadow = author_config.get('has_shadow', '关闭') == '开启'
                    author_clip.set_shadow(has_shadow)

                    # 添加到草稿
                    draft.add_clip_to_track(author_clip, index=2)
                    print(f"  ✅ 作者信息已添加")

            # 保存草稿
            draft.save()
            print(f"  ✅ 草稿已更新")

        except Exception as e:
            import traceback
            print(f"  ⚠️  添加自定义文本失败: {e}")
            print(f"  详细错误: {traceback.format_exc()}")
