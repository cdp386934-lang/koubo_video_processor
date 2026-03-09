#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI标题生成器 - 使用DeepSeek自动生成视频标题
"""
import os
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class TitleGenerator:
    """AI标题生成器"""

    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("未配置DEEPSEEK_API_KEY")

        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")

    def generate_title_from_subtitles(self, subtitles: List[Dict],
                                     style: str = "吸引人") -> str:
        """
        根据字幕内容生成标题

        参数:
            subtitles: 字幕列表
            style: 标题风格（吸引人、简洁、专业、情感化）

        返回:
            生成的标题
        """
        # 提取有效字幕文本
        texts = []
        for subtitle in subtitles:
            if subtitle.get('removed') != 1:  # 跳过气口
                text = subtitle.get('Text', '')
                if text:
                    texts.append(text)

        # 合并文本（最多取前50条）
        content = ' '.join(texts[:50])

        # 根据风格设置提示词
        style_prompts = {
            "吸引人": "生成一个吸引眼球、引发好奇的标题",
            "简洁": "生成一个简洁明了、直击要点的标题",
            "专业": "生成一个专业严谨、有深度的标题",
            "情感化": "生成一个富有情感、引发共鸣的标题"
        }

        prompt = f"""
请根据以下视频内容，{style_prompts.get(style, style_prompts['吸引人'])}。

视频内容：
{content}

要求：
1. 标题长度：10-20字
2. 突出核心观点
3. 适合短视频平台
4. 不要使用标点符号
5. 直接返回标题，不要其他说明

标题：
"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的短视频标题创作专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )

            title = response.choices[0].message.content.strip()
            # 清理标题
            title = title.replace('"', '').replace('"', '').replace('"', '')
            title = title.replace('《', '').replace('》', '')
            title = title.strip()

            return title

        except Exception as e:
            print(f"⚠️  AI生成标题失败: {e}")
            return "精彩视频"

    def generate_multiple_titles(self, subtitles: List[Dict],
                                count: int = 3) -> List[str]:
        """
        生成多个标题供选择

        参数:
            subtitles: 字幕列表
            count: 生成数量

        返回:
            标题列表
        """
        styles = ["吸引人", "简洁", "情感化", "专业"]
        titles = []

        for i in range(min(count, len(styles))):
            title = self.generate_title_from_subtitles(subtitles, styles[i])
            titles.append(title)

        return titles


class VideoInfoManager:
    """视频信息管理器"""

    def __init__(self):
        self.title_generator = None

    def load_video_info_config(self, config_path: str) -> Dict:
        """
        加载视频信息配置

        返回格式:
        {
            "title": {
                "enabled": true,
                "auto_generate": true,
                "text": "手动指定的标题",
                "style": "吸引人"
            },
            "video_description": {
                "enabled": true,
                "text": "视频简介"
            },
            "author_info": {
                "enabled": true,
                "name": "作者名",
                "title": "作者头衔",
                "subtitle": "作者简介"
            }
        }
        """
        if not os.path.exists(config_path):
            return self.get_default_config()

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "title": {
                "enabled": True,
                "auto_generate": True,
                "text": "",
                "style": "吸引人",
                "font_size": 16,
                "x_position": 0,
                "y_position": 1162,
                "color": "#000000",
                "has_shadow": "关闭",
                "alignment": "center"
            },
            "video_description": {
                "enabled": False,
                "text": "",
                "font_size": 12,
                "x_position": 0,
                "y_position": 1000,
                "color": "#666666",
                "has_shadow": "关闭",
                "alignment": "center"
            },
            "author_info": {
                "enabled": True,
                "name": "作者名",
                "title": "作者头衔",
                "subtitle": "作者简介",
                "font_size": 10,
                "x_position": 0,
                "y_position": -1298,
                "color": "#000000",
                "has_shadow": "关闭",
                "alignment": "center"
            }
        }

    def create_config_template(self, output_path: str):
        """创建配置文件模板"""
        config = self.get_default_config()

        # 添加说明
        config["_说明"] = {
            "title": {
                "enabled": "是否启用标题",
                "auto_generate": "是否自动生成标题（使用AI）",
                "text": "手动指定的标题（auto_generate=false时使用）",
                "style": "标题风格：吸引人、简洁、专业、情感化",
                "y_position": "Y轴位置（1162=视频下方，-1298=视频上方）"
            },
            "video_description": {
                "enabled": "是否启用视频简介",
                "text": "视频简介文本",
                "y_position": "Y轴位置（建议在标题下方）"
            },
            "author_info": {
                "enabled": "是否启用作者信息",
                "name": "作者名称",
                "title": "作者头衔",
                "subtitle": "作者简介"
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"✅ 已创建配置模板: {output_path}")

    def generate_title_for_video(self, subtitles: List[Dict],
                                config: Dict) -> str:
        """
        为视频生成标题

        参数:
            subtitles: 字幕列表
            config: 标题配置

        返回:
            标题文本
        """
        title_config = config.get('title', {})

        # 如果禁用标题
        if not title_config.get('enabled', True):
            return ""

        # 如果手动指定了标题
        if not title_config.get('auto_generate', True):
            return title_config.get('text', '')

        # 使用AI生成标题
        if self.title_generator is None:
            try:
                self.title_generator = TitleGenerator()
            except Exception as e:
                print(f"⚠️  无法初始化标题生成器: {e}")
                return title_config.get('text', '精彩视频')

        style = title_config.get('style', '吸引人')
        title = self.title_generator.generate_title_from_subtitles(
            subtitles, style
        )

        return title

    def apply_video_info_to_template(self, template_config: Dict,
                                    video_info_config: Dict,
                                    subtitles: List[Dict] = None) -> Dict:
        """
        将视频信息配置应用到模板

        参数:
            template_config: 模板配置
            video_info_config: 视频信息配置
            subtitles: 字幕列表（用于生成标题）

        返回:
            更新后的模板配置
        """
        # 处理标题
        title_config = video_info_config.get('title', {})
        if title_config.get('enabled', True):
            # 生成或获取标题
            if subtitles and title_config.get('auto_generate', True):
                title_text = self.generate_title_for_video(subtitles, video_info_config)
            else:
                title_text = title_config.get('text', '')

            # 更新模板
            template_config['title'] = {
                'enabled': True,
                'text': title_text,
                'font_size': title_config.get('font_size', 16),
                'x_position': title_config.get('x_position', 0),
                'y_position': title_config.get('y_position', 1162),
                'color': title_config.get('color', '#000000'),
                'has_shadow': title_config.get('has_shadow', '关闭'),
                'alignment': title_config.get('alignment', 'center')
            }

        # 处理视频简介
        desc_config = video_info_config.get('video_description', {})
        if desc_config.get('enabled', False):
            template_config['video_description'] = {
                'enabled': True,
                'text': desc_config.get('text', ''),
                'font_size': desc_config.get('font_size', 12),
                'x_position': desc_config.get('x_position', 0),
                'y_position': desc_config.get('y_position', 1000),
                'color': desc_config.get('color', '#666666'),
                'has_shadow': desc_config.get('has_shadow', '关闭'),
                'alignment': desc_config.get('alignment', 'center')
            }

        # 处理作者信息
        author_config = video_info_config.get('author_info', {})
        if author_config.get('enabled', True):
            template_config['author_info'] = {
                'enabled': True,
                'name': author_config.get('name', ''),
                'title': author_config.get('title', ''),
                'subtitle': author_config.get('subtitle', ''),
                'font_size': author_config.get('font_size', 10),
                'x_position': author_config.get('x_position', 0),
                'y_position': author_config.get('y_position', -1298),
                'color': author_config.get('color', '#000000'),
                'has_shadow': author_config.get('has_shadow', '关闭'),
                'alignment': author_config.get('alignment', 'center')
            }

        return template_config


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='视频信息管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建配置模板
  python3 title_generator.py --create-template video_info.json

  # 生成标题
  python3 title_generator.py --generate-title movies/未加工.json

  # 生成多个标题
  python3 title_generator.py --generate-multiple movies/未加工.json --count 3
        """
    )

    parser.add_argument('--create-template', metavar='FILE',
                       help='创建配置文件模板')
    parser.add_argument('--generate-title', metavar='FILE',
                       help='为字幕JSON生成标题')
    parser.add_argument('--generate-multiple', metavar='FILE',
                       help='生成多个标题供选择')
    parser.add_argument('--count', type=int, default=3,
                       help='生成标题数量（默认3个）')
    parser.add_argument('--style', default='吸引人',
                       help='标题风格（吸引人、简洁、专业、情感化）')

    args = parser.parse_args()

    manager = VideoInfoManager()

    if args.create_template:
        manager.create_config_template(args.create_template)

    elif args.generate_title:
        # 加载字幕
        from ..subtitle.subtitle_json_manager import SubtitleJsonManager
        json_manager = SubtitleJsonManager()
        data = json_manager.load_subtitle_json(args.generate_title)
        subtitles = data['subtitles']

        # 生成标题
        try:
            generator = TitleGenerator()
            title = generator.generate_title_from_subtitles(subtitles, args.style)
            print("=" * 60)
            print("生成的标题:")
            print("=" * 60)
            print(f"\n{title}\n")
        except Exception as e:
            print(f"❌ 生成失败: {e}")

    elif args.generate_multiple:
        # 加载字幕
        from ..subtitle.subtitle_json_manager import SubtitleJsonManager
        json_manager = SubtitleJsonManager()
        data = json_manager.load_subtitle_json(args.generate_multiple)
        subtitles = data['subtitles']

        # 生成多个标题
        try:
            generator = TitleGenerator()
            titles = generator.generate_multiple_titles(subtitles, args.count)
            print("=" * 60)
            print(f"生成的 {len(titles)} 个标题:")
            print("=" * 60)
            for i, title in enumerate(titles, 1):
                print(f"\n{i}. {title}")
            print()
        except Exception as e:
            print(f"❌ 生成失败: {e}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
