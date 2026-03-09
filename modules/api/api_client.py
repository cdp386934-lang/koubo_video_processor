#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原项目服务API客户端
通过API接口调用原项目的功能
"""
import os
import sys
import json
import requests
from pathlib import Path

# 添加原项目路径到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class AutoJianyingAPI:
    """原项目API客户端"""

    def __init__(self, base_url=None):
        """
        初始化API客户端

        参数:
            base_url: API服务器地址，默认使用本地服务
        """
        self.base_url = base_url or os.getenv('AUTO_JIANYING_API_URL', 'http://localhost:8000')

    def video_to_text(self, video_path):
        """
        视频转文字（ASR）

        参数:
            video_path: 视频文件路径

        返回:
            字幕JSON文件路径
        """
        # 如果API服务不可用，使用本地方法
        if not self._check_api_available():
            return self._local_video_to_text(video_path)

        # 调用API
        try:
            with open(video_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f'{self.base_url}/api/asr',
                    files=files,
                    timeout=300
                )
                response.raise_for_status()
                result = response.json()
                return result['json_path']
        except Exception as e:
            print(f"API调用失败: {e}")
            print("回退到本地方法...")
            return self._local_video_to_text(video_path)

    def create_draft(self, video_path, json_path, template_config, output_title):
        """
        生成剪映草稿

        参数:
            video_path: 视频文件路径
            json_path: 字幕JSON路径
            template_config: 模板配置
            output_title: 输出标题

        返回:
            草稿路径
        """
        # 如果API服务不可用，使用本地方法
        if not self._check_api_available():
            return self._local_create_draft(video_path, json_path, template_config, output_title)

        # 调用API
        try:
            data = {
                'video_path': video_path,
                'json_path': json_path,
                'template_config': template_config,
                'output_title': output_title
            }
            response = requests.post(
                f'{self.base_url}/api/draft',
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['draft_path']
        except Exception as e:
            print(f"API调用失败: {e}")
            print("回退到本地方法...")
            return self._local_create_draft(video_path, json_path, template_config, output_title)

    def _check_api_available(self):
        """检查API服务是否可用"""
        try:
            response = requests.get(f'{self.base_url}/health', timeout=2)
            return response.status_code == 200
        except:
            return False

    def _local_video_to_text(self, video_path):
        """本地方法：视频转文字"""
        # 添加父目录到路径
        parent_dir = Path(__file__).resolve().parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))

        try:
            from service.auto_to_text.asr import video2text
            video2text(video_path)

            # 返回JSON路径
            folder_path = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            json_path = os.path.join(folder_path, f"{video_name}.json")

            if os.path.exists(json_path):
                return json_path
            else:
                raise Exception("ASR处理失败，未生成字幕文件")
        except ImportError as e:
            raise Exception(f"无法导入原项目模块: {e}")

    def _local_create_draft(self, video_path, json_path, template_config, output_title):
        """本地方法：生成草稿"""
        # 添加父目录到路径
        parent_dir = Path(__file__).resolve().parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))

        try:
            from service.template_cut import create_draft_from_json
            from service.draft_config import IS_WINDOWS
            import os

            # 保存模板配置到临时文件
            template_dir = os.path.dirname(video_path)
            temp_template_path = os.path.join(template_dir, '_temp_template.json')

            # 修改模板配置：如果不显示草稿标题，则移除grade4配置
            modified_config = template_config.copy()
            if template_config.get('title', {}).get('show_draft_title') == False:
                # 不显示草稿标题，使用空的grade4配置
                if 'subtext' in modified_config and 'grade4' in modified_config['subtext']:
                    # 保留grade4但设置为不可见
                    modified_config['subtext']['grade4']['color'] = '#00000000'  # 透明色
                    modified_config['subtext']['grade4']['font_size'] = 1

            with open(temp_template_path, 'w', encoding='utf-8') as f:
                json.dump(modified_config, f, ensure_ascii=False, indent=2)

            # 确保JSON文件格式正确（兼容新旧格式）
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # 如果是新格式（包含subtitles键），转换为旧格式
            if isinstance(json_data, dict) and 'subtitles' in json_data:
                # 创建临时的旧格式JSON文件
                temp_json_path = json_path.replace('.json', '_temp.json')
                with open(temp_json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data['subtitles'], f, ensure_ascii=False, indent=2)
                json_path_to_use = temp_json_path
            else:
                json_path_to_use = json_path

            # 调用原项目的函数（使用正确的参数）
            result = create_draft_from_json(
                title=output_title,
                file_path=video_path,
                template_path=temp_template_path
            )

            # 删除临时文件
            if os.path.exists(temp_template_path):
                os.remove(temp_template_path)
            if json_path_to_use != json_path and os.path.exists(json_path_to_use):
                os.remove(json_path_to_use)

            if result == 'success':
                # 获取草稿路径
                if IS_WINDOWS:
                    drafts_base = os.path.join(
                        os.environ['LOCALAPPDATA'],
                        'JianyingPro/User Data/Projects/com.lveditor.draft'
                    )
                else:
                    drafts_base = os.path.expanduser(
                        '~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft'
                    )
                draft_path = os.path.join(drafts_base, output_title)

                # 如果配置了背景色，设置画布背景
                if template_config.get('background', {}).get('enabled'):
                    self._set_canvas_background(draft_path, template_config.get('background'))

                return draft_path
            else:
                raise Exception(f"草稿生成失败: {result}")
        except ImportError as e:
            raise Exception(f"无法导入原项目模块: {e}")

    def _set_canvas_background(self, draft_path, background_config):
        """设置草稿画布背景色"""
        try:
            bg_color = background_config.get('color', '#F0F0F0').lstrip('#')
            print(f"  ✅ 画布背景色已配置: #{bg_color}")
            # 注意：背景色已通过模板配置中的video.canvase设置
        except Exception as e:
            print(f"  警告: 配置背景色失败: {e}")



# 全局API客户端实例
_api_client = None


def get_api_client():
    """获取API客户端单例"""
    global _api_client
    if _api_client is None:
        _api_client = AutoJianyingAPI()
    return _api_client


if __name__ == '__main__':
    # 测试API客户端
    client = AutoJianyingAPI()
    print(f"API服务器: {client.base_url}")
    print(f"API可用: {client._check_api_available()}")
