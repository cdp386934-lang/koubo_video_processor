#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材管理模块 - 整合Pexels素材获取和插入功能
"""
import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class MaterialManager:
    """统一的素材管理器"""

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        初始化素材管理器

        参数:
            api_key: Pexels API密钥
            cache_dir: 缓存目录
        """
        self.api_key = api_key or os.getenv('PEXELS_API_KEY')
        self.cache_dir = cache_dir or os.path.expanduser('~/.koubo_cache/pexels')
        os.makedirs(self.cache_dir, exist_ok=True)

        self.base_url = 'https://api.pexels.com/videos'

    # ==================== Pexels素材获取 ====================

    def search_videos(
        self,
        query: str,
        orientation: str = 'portrait',
        size: str = 'medium',
        per_page: int = 5
    ) -> List[Dict]:
        """
        搜索Pexels视频素材

        参数:
            query: 搜索关键词
            orientation: 方向（portrait/landscape/square）
            size: 尺寸（large/medium/small）
            per_page: 每页数量

        返回:
            视频列表
        """
        if not self.api_key:
            print("  ⚠️  Pexels API未配置")
            return []

        try:
            headers = {'Authorization': self.api_key}
            params = {
                'query': query,
                'orientation': orientation,
                'size': size,
                'per_page': per_page
            }

            response = requests.get(
                f'{self.base_url}/search',
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('videos', [])
            else:
                print(f"  ⚠️  Pexels API错误: {response.status_code}")
                return []

        except Exception as e:
            print(f"  ⚠️  Pexels搜索失败: {e}")
            return []

    def download_video(self, video_url: str, filename: str) -> Optional[str]:
        """
        下载视频到缓存目录

        参数:
            video_url: 视频URL
            filename: 文件名

        返回:
            本地文件路径
        """
        try:
            cache_path = os.path.join(self.cache_dir, filename)

            # 如果已缓存，直接返回
            if os.path.exists(cache_path):
                print(f"  ✅ 使用缓存素材: {filename}")
                return cache_path

            # 下载
            print(f"  下载素材: {filename}")
            response = requests.get(video_url, timeout=30)

            if response.status_code == 200:
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                print(f"  ✅ 下载完成: {cache_path}")
                return cache_path
            else:
                print(f"  ⚠️  下载失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"  ⚠️  下载失败: {e}")
            return None

    def get_material_for_content(
        self,
        keywords: List[str],
        max_videos: int = 3
    ) -> List[Dict]:
        """
        根据关键词获取素材

        参数:
            keywords: 关键词列表
            max_videos: 最大视频数

        返回:
            素材信息列表
        """
        materials = []

        for keyword in keywords[:max_videos]:
            videos = self.search_videos(keyword, per_page=1)

            if videos:
                video = videos[0]
                video_files = video.get('video_files', [])

                # 选择合适的视频文件（HD质量）
                hd_file = None
                for vf in video_files:
                    if vf.get('quality') == 'hd' and vf.get('width') <= 1080:
                        hd_file = vf
                        break

                if not hd_file and video_files:
                    hd_file = video_files[0]

                if hd_file:
                    filename = f"{keyword}_{video['id']}.mp4"
                    local_path = self.download_video(hd_file['link'], filename)

                    if local_path:
                        materials.append({
                            'keyword': keyword,
                            'video_id': video['id'],
                            'local_path': local_path,
                            'duration': video.get('duration', 5),
                            'width': hd_file.get('width'),
                            'height': hd_file.get('height')
                        })

        return materials

    # ==================== 素材插入分析 ====================

    def analyze_insertion_points(
        self,
        subtitles: List[Dict],
        insert_interval: int = 45,
        clip_duration: int = 4
    ) -> List[Dict]:
        """
        分析素材插入点

        参数:
            subtitles: 字幕列表
            insert_interval: 插入间隔（秒）
            clip_duration: 素材时长（秒）

        返回:
            插入点列表
        """
        # 兼容新旧格式
        if isinstance(subtitles, dict) and 'subtitles' in subtitles:
            subtitle_list = subtitles['subtitles']
        else:
            subtitle_list = subtitles

        # 过滤已删除的字幕
        valid_subtitles = [s for s in subtitle_list if s.get('removed') != 1]

        if not valid_subtitles:
            return []

        insertion_points = []
        last_insert_time = 0
        insert_interval_ms = insert_interval * 1000

        for i, subtitle in enumerate(valid_subtitles):
            start_ms = subtitle.get('StartMs', 0)
            end_ms = subtitle.get('EndMs', 0)

            # 检查是否到达插入间隔
            if start_ms - last_insert_time >= insert_interval_ms:
                # 在句子结束处插入
                text = subtitle.get('FinalSentence', subtitle.get('Text', ''))
                if text and text[-1] in ['。', '！', '？', '.', '!', '?']:
                    insertion_points.append({
                        'index': i,
                        'time_ms': end_ms,
                        'duration_ms': clip_duration * 1000
                    })
                    last_insert_time = end_ms

        return insertion_points

    def extract_keywords_for_materials(
        self,
        subtitles: List[Dict],
        max_keywords: int = 5
    ) -> List[str]:
        """
        从字幕中提取用于搜索素材的关键词

        参数:
            subtitles: 字幕列表
            max_keywords: 最大关键词数

        返回:
            关键词列表
        """
        # 收集所有已标注的关键词
        all_keywords = []

        for subtitle in subtitles:
            if subtitle.get('removed') == 1:
                continue

            keywords = subtitle.get('keywords', [])
            if keywords:
                all_keywords.extend(keywords)

        # 去重并统计频率
        keyword_freq = {}
        for kw in all_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

        # 按频率排序
        sorted_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 返回前N个关键词
        return [kw for kw, _ in sorted_keywords[:max_keywords]]

    # ==================== 素材插入 ====================

    def insert_materials(
        self,
        subtitles: List[Dict],
        config: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        插入素材到字幕数据

        参数:
            subtitles: 字幕列表
            config: 配置字典

        返回:
            (更新后的字幕列表, 素材列表)
        """
        if not config.get('enabled', False):
            print("  ⏭️  素材插入未启用")
            return subtitles, []

        # 分析插入点
        insert_interval = config.get('insert_interval', 45)
        clip_duration = config.get('clip_duration', 4)

        insertion_points = self.analyze_insertion_points(
            subtitles, insert_interval, clip_duration
        )

        if not insertion_points:
            print("  ⚠️  未找到合适的插入点")
            return subtitles, []

        print(f"  找到 {len(insertion_points)} 个插入点")

        # 提取关键词
        keywords = self.extract_keywords_for_materials(subtitles)

        if not keywords:
            print("  ⚠️  未找到关键词")
            return subtitles, []

        print(f"  提取关键词: {', '.join(keywords)}")

        # 获取素材
        materials = self.get_material_for_content(keywords, len(insertion_points))

        if not materials:
            print("  ⚠️  未获取到素材")
            return subtitles, []

        print(f"  获取到 {len(materials)} 个素材")

        # 在字幕数据中标记插入点
        for i, point in enumerate(insertion_points):
            if i < len(materials):
                subtitle_idx = point['index']
                if subtitle_idx < len(subtitles):
                    subtitles[subtitle_idx]['material_insert'] = {
                        'time_ms': point['time_ms'],
                        'duration_ms': point['duration_ms'],
                        'material_path': materials[i]['local_path'],
                        'keyword': materials[i]['keyword']
                    }

        return subtitles, materials

    # ==================== 文件处理方法 ====================

    def process_subtitle_file(
        self,
        json_path: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        处理字幕JSON文件，插入素材

        参数:
            json_path: 字幕JSON文件路径
            config: 配置字典

        返回:
            处理结果
        """
        if config is None:
            config = {
                'enabled': True,
                'insert_interval': 45,
                'clip_duration': 4
            }

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'subtitles' in data:
            subtitles = data['subtitles']
        else:
            subtitles = data

        # 插入素材
        subtitles, materials = self.insert_materials(subtitles, config)

        # 保存回文件
        if isinstance(data, dict) and 'subtitles' in data:
            data['subtitles'] = subtitles
        else:
            data = subtitles

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            'status': 'success',
            'json_path': json_path,
            'materials_count': len(materials),
            'materials': materials
        }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='素材管理工具')
    parser.add_argument('json_path', help='字幕JSON文件路径')
    parser.add_argument('--interval', type=int, default=45, help='插入间隔（秒）')
    parser.add_argument('--duration', type=int, default=4, help='素材时长（秒）')

    args = parser.parse_args()

    manager = MaterialManager()
    config = {
        'enabled': True,
        'insert_interval': args.interval,
        'clip_duration': args.duration
    }

    result = manager.process_subtitle_file(args.json_path, config)

    print(f"\n✅ 处理完成！插入了 {result['materials_count']} 个素材")
