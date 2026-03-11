#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映草稿生成器
基于 CapCut Mate API 生成可被剪映直接打开的草稿
"""
import json
import os
import platform
import requests
import shutil
import re
from pathlib import Path


class JianyingDraftGenerator:
    """剪映草稿生成器 - 使用 CapCut Mate API"""

    def __init__(self, api_base_url="http://localhost:30000", capcut_mate_path=None):
        self.platform = platform.system()
        self.draft_base_path = self._get_draft_base_path()
        self.project_root = Path(__file__).resolve().parents[2]
        self.api_base_url = api_base_url.rstrip('/')
        self.api_prefix = f"{self.api_base_url}/openapi/capcut-mate/v1"

        # CapCut Mate 项目路径（用于复制草稿）
        if capcut_mate_path:
            self.capcut_mate_path = Path(capcut_mate_path)
        else:
            # 默认路径：假设 capcut-mate 和当前项目在同一父目录下
            self.capcut_mate_path = self.project_root.parent / "capcut-mate"

    def _get_draft_base_path(self):
        """获取剪映草稿基础路径"""
        if self.platform == 'Darwin':
            return os.path.expanduser(
                '~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft'
            )
        if self.platform == 'Windows':
            return os.path.join(
                os.environ['LOCALAPPDATA'],
                'JianyingPro/User Data/Projects/com.lveditor.draft'
            )
        raise Exception(f"不支持的操作系统: {self.platform}")

    def create_draft(self, video_path, json_path, template_config, output_title):
        """创建剪映草稿 - 使用 API"""
        print("  正在通过 API 生成剪映草稿...")

        # 加载字幕和视频信息
        subtitles = self._load_subtitles(json_path)
        video_info = self._get_video_info(video_path)
        canvas_width, canvas_height = self._get_canvas_size(template_config, video_info)

        # 计算时长
        video_duration_ms = int(video_info['duration'] * 1000)
        subtitle_duration_ms = self._get_subtitle_duration(subtitles) // 1000
        material_inserts = self._collect_material_inserts(subtitles)
        material_duration_ms = self._get_material_duration(material_inserts) // 1000
        total_duration_ms = max(video_duration_ms, subtitle_duration_ms, material_duration_ms)
        if total_duration_ms <= 0:
            total_duration_ms = video_duration_ms

        try:
            # 1. 创建草稿
            draft_url = self._api_create_draft(canvas_width, canvas_height)
            print(f"  ✅ 草稿已创建: {draft_url}")

            # 2. 添加背景（如果有）
            has_background = self._api_add_background(
                draft_url, template_config, total_duration_ms
            )

            # 3. 添加主视频
            video_config = template_config.get('video', {}).get('grade1', {})
            self._api_add_main_video(
                draft_url, video_path, video_duration_ms, total_duration_ms, video_config
            )

            # 4. 添加素材视频
            if material_inserts:
                self._api_add_materials(draft_url, material_inserts, total_duration_ms)

            # 5. 添加字幕
            if subtitles:
                self._api_add_subtitles(
                    draft_url, subtitles, template_config, total_duration_ms
                )

            # 6. 添加标题和作者信息
            self._api_add_info_texts(
                draft_url, template_config, total_duration_ms, canvas_width, canvas_height
            )

            # 7. 保存草稿
            final_draft_url = self._api_save_draft(draft_url)
            print(f"  ✅ 草稿已保存: {final_draft_url}")

            # 8. 下载草稿到本地剪映目录
            local_draft_path = self._download_draft_to_local(final_draft_url, output_title)
            if local_draft_path:
                print(f"  ✅ 草稿已复制到本地: {local_draft_path}")
                return local_draft_path

            return final_draft_url

        except requests.exceptions.RequestException as exc:
            print(f"  ❌ API 调用失败: {exc}")
            raise RuntimeError(f"草稿生成失败: {exc}") from exc

    def _api_create_draft(self, width, height):
        """调用 API 创建草稿"""
        url = f"{self.api_prefix}/create_draft"
        payload = {"width": width, "height": height}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        # API 响应格式: {"code": 0, "message": "success", "draft_url": "..."}
        return result.get('draft_url')

    def _api_save_draft(self, draft_url):
        """调用 API 保存草稿"""
        url = f"{self.api_prefix}/save_draft"
        payload = {"draft_url": draft_url}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        # API 响应格式: {"code": 0, "message": "success", "draft_url": "..."}
        return result.get('draft_url')

    def _api_add_main_video(self, draft_url, video_path, video_duration_ms, total_duration_ms, video_config):
        """添加主视频"""
        url = f"{self.api_prefix}/add_videos"

        # 构建视频信息
        video_info = {
            "path": os.path.abspath(video_path),
            "start_time": 0,
            "duration": min(video_duration_ms, total_duration_ms)
        }

        # 获取缩放和位置参数
        scale = float(video_config.get('scale', 1.0))
        x_pos = float(video_config.get('x_position', 0))
        y_pos = float(video_config.get('y_position', 0))

        payload = {
            "draft_url": draft_url,
            "video_infos": [video_info],
            "scale_x": scale,
            "scale_y": scale,
            "transform_x": x_pos,
            "transform_y": y_pos,
            "alpha": 1.0
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        print("  ✅ 主视频已添加")

    def _api_add_background(self, draft_url, template_config, total_duration_ms):
        """添加背景图片"""
        background = template_config.get('background', {})
        if not background.get('enabled') or background.get('type') != 'image':
            return False

        image_path = self._resolve_path(background.get('image_path', ''))
        if not image_path or not os.path.exists(image_path):
            print(f"  ⚠️  背景图片不存在，已跳过: {background.get('image_path', '')}")
            return False

        url = f"{self.api_prefix}/add_images"
        image_info = {
            "path": os.path.abspath(image_path),
            "start_time": 0,
            "duration": total_duration_ms
        }

        payload = {
            "draft_url": draft_url,
            "image_infos": [image_info],
            "scale_x": 1.0,
            "scale_y": 1.0,
            "transform_x": 0,
            "transform_y": 0,
            "alpha": 1.0
        }

        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        print("  ✅ 背景已添加")
        return True

    def _api_add_materials(self, draft_url, materials, total_duration_ms):
        """添加素材视频"""
        if not materials:
            return

        url = f"{self.api_prefix}/add_videos"

        for material in materials:
            start_ms = max(0, material['start_ms'])
            duration_ms = min(material['duration_ms'], max(total_duration_ms - start_ms, 0))
            if duration_ms <= 0:
                continue

            video_info = {
                "path": material['path'],
                "start_time": start_ms,
                "duration": duration_ms
            }

            payload = {
                "draft_url": draft_url,
                "video_infos": [video_info],
                "scale_x": 1.0,
                "scale_y": 1.0,
                "transform_x": 0,
                "transform_y": 0,
                "alpha": 1.0
            }

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

        print(f"  ✅ 已添加 {len(materials)} 个素材")

    def _api_add_subtitles(self, draft_url, subtitles, template_config, total_duration_ms):
        """添加字幕"""
        subtitle_styles = template_config.get('subtext', {})
        url = f"{self.api_prefix}/add_captions"

        caption_infos = []
        for subtitle in subtitles:
            if subtitle.get('removed') == 1:
                continue

            text = subtitle.get('FinalSentence') or subtitle.get('Text') or ''
            text = text.strip()
            if not text:
                continue

            start_ms = max(0, int(subtitle.get('StartMs', 0)))
            end_ms = min(total_duration_ms, int(subtitle.get('EndMs', 0)))
            duration_ms = end_ms - start_ms
            if duration_ms <= 0:
                continue

            # 获取样式配置
            style_config = self._get_subtitle_style_config(subtitle, subtitle_styles)

            caption_info = {
                "content": text,
                "start_time": start_ms,
                "duration": duration_ms,
                "font_size": float(style_config.get('font_size', 10)),
                "color": style_config.get('color', '#FFFFFF'),
                "bold": bool(style_config.get('bold', False)),
                "italic": bool(style_config.get('italic', False)),
                "underline": bool(style_config.get('underline', False))
            }
            caption_infos.append(caption_info)

        if caption_infos:
            payload = {
                "draft_url": draft_url,
                "caption_infos": caption_infos
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            print(f"  ✅ 已添加 {len(caption_infos)} 条字幕")

    def _api_add_info_texts(self, draft_url, template_config, total_duration_ms, canvas_width, canvas_height):
        """添加标题和作者信息"""
        info_items = []

        # 标题
        title_config = template_config.get('title', {})
        if title_config.get('enabled') and title_config.get('text'):
            info_items.append(title_config)

        # 作者信息
        author_config = template_config.get('author_info', {})
        if author_config.get('enabled'):
            author_lines = [
                author_config.get('name', '').strip(),
                author_config.get('title', '').strip(),
                author_config.get('subtitle', '').strip(),
            ]
            author_text = '\n'.join(line for line in author_lines if line)
            if author_text:
                merged = dict(author_config)
                merged['text'] = author_text
                info_items.append(merged)

        # 使用字幕 API 添加文本（因为标题和作者信息本质上也是文本）
        if info_items:
            url = f"{self.api_prefix}/add_captions"
            caption_infos = []

            for config in info_items:
                caption_info = {
                    "content": config.get('text', ''),
                    "start_time": 0,
                    "duration": total_duration_ms,
                    "font_size": float(config.get('font_size', 10)),
                    "color": config.get('color', '#FFFFFF'),
                    "bold": bool(config.get('bold', False)),
                    "italic": bool(config.get('italic', False)),
                    "underline": bool(config.get('underline', False))
                }
                caption_infos.append(caption_info)

            payload = {
                "draft_url": draft_url,
                "caption_infos": caption_infos
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            print(f"  ✅ 已添加 {len(caption_infos)} 个信息文本")

    def _load_subtitles(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        if isinstance(json_data, dict) and 'subtitles' in json_data:
            return json_data['subtitles']
        return json_data

    def _get_video_info(self, video_path):
        try:
            from moviepy.editor import VideoFileClip

            video = VideoFileClip(video_path)
            info = {
                'duration': video.duration,
                'fps': video.fps,
                'width': video.w,
                'height': video.h,
                'size': os.path.getsize(video_path),
            }
            video.close()
            return info
        except Exception as exc:
            print(f"  ⚠️  获取视频信息失败: {exc}")
            return {
                'duration': 0,
                'fps': 30,
                'width': 1080,
                'height': 1920,
                'size': os.path.getsize(video_path),
            }

    def _get_canvas_size(self, template_config, video_info):
        canvas = template_config.get('video_canvas', [])
        if isinstance(canvas, list) and len(canvas) == 2:
            return int(canvas[0]), int(canvas[1])
        return int(video_info.get('width', 1080)), int(video_info.get('height', 1920))

    def _get_subtitle_duration(self, subtitles):
        valid_ends = [subtitle.get('EndMs', 0) for subtitle in subtitles if subtitle.get('removed') != 1]
        if not valid_ends:
            return 0
        return max(valid_ends) * 1000

    def _collect_material_inserts(self, subtitles):
        materials = []
        for subtitle in subtitles:
            material_insert = subtitle.get('material_insert')
            if not material_insert:
                continue

            material_path = material_insert.get('material_path')
            if not material_path or not os.path.exists(material_path):
                continue

            start_ms = int(material_insert.get('time_ms', 0))
            duration_ms = int(material_insert.get('duration_ms', 0))
            if duration_ms <= 0:
                continue

            materials.append({
                'path': os.path.abspath(material_path),
                'start_ms': start_ms,
                'duration_ms': duration_ms,
            })

        materials.sort(key=lambda item: item['start_ms'])
        return materials

    def _get_material_duration(self, materials):
        if not materials:
            return 0
        return max((item['start_ms'] + item['duration_ms']) * 1000 for item in materials)

    def _get_subtitle_style_config(self, subtitle, subtitle_styles):
        if subtitle.get('keyword'):
            return subtitle_styles.get('grade2', subtitle_styles.get('grade1', {}))
        return subtitle_styles.get('grade1', {})

    def _resolve_path(self, path_value):
        if not path_value:
            return None

        candidate = Path(path_value).expanduser()
        if candidate.is_absolute():
            return str(candidate)

        repo_candidate = self.project_root / candidate
        if repo_candidate.exists():
            return str(repo_candidate)

        return str(candidate)

    def _download_draft_to_local(self, draft_url, output_title):
        """下载草稿到本地剪映目录"""
        try:
            # 从 URL 中提取 draft_id
            draft_id = self._extract_draft_id(draft_url)
            if not draft_id:
                print("  ⚠️  无法从 URL 提取 draft_id")
                return None

            # 获取 API 服务器上的草稿目录路径
            source_draft_path = self.capcut_mate_path / "output" / "draft" / draft_id

            if not source_draft_path.exists():
                print(f"  ⚠️  源草稿目录不存在: {source_draft_path}")
                return None

            # 目标路径：本地剪映草稿目录
            target_draft_path = Path(self.draft_base_path) / output_title

            # 如果目标已存在，先删除
            if target_draft_path.exists():
                shutil.rmtree(target_draft_path)

            # 复制草稿目录
            shutil.copytree(source_draft_path, target_draft_path)

            return str(target_draft_path)

        except Exception as exc:
            print(f"  ⚠️  复制草稿到本地失败: {exc}")
            return None

    def _extract_draft_id(self, draft_url):
        """从 draft_url 中提取 draft_id"""
        try:
            # URL 格式: https://xxx/get_draft?draft_id=202603091739481d6860be
            match = re.search(r'draft_id=([^&]+)', draft_url)
            if match:
                return match.group(1)
            return None
        except Exception:
            return None
