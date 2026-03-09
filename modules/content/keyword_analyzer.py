#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词分析模块 - 整合DeepSeek和AI关键词提取功能
"""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class KeywordAnalyzer:
    """统一的关键词分析器"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化关键词分析器

        参数:
            api_key: DeepSeek API密钥（可选，默认从环境变量读取）
            base_url: API基础URL（可选，默认从环境变量读取）
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url or os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    # ==================== DeepSeek关键词提取 ====================

    def analyze_keywords(self, subtitles: List[Dict]) -> List[Dict]:
        """
        分析字幕内容，标注关键词

        参数:
            subtitles: 字幕列表

        返回:
            更新后的字幕列表
        """
        if not self.client:
            print("  ⚠️  DeepSeek API未配置，跳过关键词分析")
            return subtitles

        # 过滤掉已删除的字幕
        valid_subtitles = [s for s in subtitles if s.get('removed') != 1]

        # 构建完整文本
        full_text = ''.join([s.get('FinalSentence', s.get('text', '')) for s in valid_subtitles])

        if not full_text.strip():
            print("  ⚠️  没有有效的字幕文本")
            return subtitles

        # 调用DeepSeek API分析关键词
        try:
            print(f"  正在分析文本（共{len(full_text)}字）...")
            keywords_data = self._call_deepseek_api(full_text)

            if not keywords_data:
                print("  ⚠️  DeepSeek未返回关键词")
                return subtitles

            print(f"  DeepSeek返回 {len(keywords_data)} 个关键词")

            # 保存关键词
            self._save_keywords(keywords_data)

            # 将关键词映射到字幕
            updated_subtitles = self._map_keywords_to_subtitles(
                subtitles, keywords_data
            )

            return updated_subtitles

        except Exception as e:
            print(f"  ⚠️  DeepSeek分析失败: {e}")
            import traceback
            traceback.print_exc()
            return subtitles

    def _call_deepseek_api(self, text: str) -> List[Dict]:
        """调用DeepSeek API进行关键词分析"""
        prompt = self._build_prompt(text)

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是专业的视频内容关键词提取专家，只专注于从口播字幕中提取核心关键词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        # 解析响应
        keywords_text = response.choices[0].message.content.strip()

        keywords = []
        if keywords_text:
            keyword_list = keywords_text.replace('、', ',').split(',')
            for kw in keyword_list:
                kw = kw.strip().strip('"').strip('"').strip('"')
                if kw and len(kw) <= 4:
                    keywords.append({
                        "keyword": kw,
                        "importance": 2
                    })

        return keywords

    def _build_prompt(self, text: str) -> str:
        """构建分析提示词"""
        return f"""请从以下口播视频字幕中提取核心关键词。

提取规则：
1. 每句字幕提取3-5个核心关键词
2. 关键词为名词/动词，避免语气词、虚词
3. 关键词需简洁，不超过4个字
4. 输出的关键词用顿号（、）分隔，无空格、无引号、无多余标点
5. 只返回关键词本身，不添加任何解释

示例：
输入："恋爱到深处，人会变成孩子，因为爱情让人卸下防备。"
输出：恋爱、深处、孩子、爱情、防备

需要提取关键词的字幕：
{text}

请进行提取："""

    def _map_keywords_to_subtitles(
        self, subtitles: List[Dict], keywords_data: List[Dict]
    ) -> List[Dict]:
        """将关键词映射到字幕"""
        keyword_dict = {kw['keyword']: kw['importance'] for kw in keywords_data}

        for subtitle in subtitles:
            if subtitle.get('removed') == 1:
                continue

            text = subtitle.get('FinalSentence', subtitle.get('Text', subtitle.get('text', '')))

            # 查找该句中的所有关键词
            found_keywords = []
            max_importance = 0

            for keyword, importance in keyword_dict.items():
                if keyword in text:
                    found_keywords.append(keyword)
                    max_importance = max(max_importance, importance)

            # 如果找到关键词
            if found_keywords:
                subtitle['text_grade'] = max_importance + 1
                subtitle['keywords'] = found_keywords
                subtitle['keyword'] = '、'.join([f'"{kw}"' for kw in found_keywords])

                # 在FinalSentence中给关键词加引号
                if '"' not in text:
                    modified_text = text
                    for kw in sorted(found_keywords, key=len, reverse=True):
                        if kw in modified_text:
                            modified_text = modified_text.replace(kw, f'"{kw}"', 1)
                    subtitle['FinalSentence'] = modified_text
                else:
                    subtitle['FinalSentence'] = text

        return subtitles

    def _save_keywords(self, keywords_data: List[Dict]):
        """保存关键词到文件"""
        beautified = self._beautify_keywords(keywords_data)

        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)

        # 保存JSON
        keywords_file = os.path.join(output_dir, 'keywords.json')
        with open(keywords_file, 'w', encoding='utf-8') as f:
            json.dump(beautified, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 关键词已保存到: {keywords_file}")

        # 保存文本版本
        keywords_txt = os.path.join(output_dir, 'keywords.txt')
        with open(keywords_txt, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("关键词分析结果\n")
            f.write("=" * 60 + "\n\n")

            for level in [3, 2, 1]:
                level_name = {3: "超重点", 2: "重点", 1: "普通重点"}[level]
                level_keywords = [kw for kw in beautified['keywords'] if kw['importance'] == level]

                if level_keywords:
                    f.write(f"\n【{level_name}】（{len(level_keywords)}个）\n")
                    f.write("-" * 60 + "\n")
                    for kw in level_keywords:
                        f.write(f"  • {kw['keyword']}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write(f"总计: {beautified['total']} 个关键词\n")
            f.write("=" * 60 + "\n")

        print(f"  ✅ 关键词文本版已保存到: {keywords_txt}")

    def _beautify_keywords(self, keywords_data: List[Dict]) -> Dict:
        """美化关键词数据"""
        seen = set()
        unique_keywords = []
        for kw in keywords_data:
            if kw['keyword'] not in seen:
                seen.add(kw['keyword'])
                unique_keywords.append(kw)

        sorted_keywords = sorted(
            unique_keywords,
            key=lambda x: (-x['importance'], x['keyword'])
        )

        importance_count = {1: 0, 2: 0, 3: 0}
        for kw in sorted_keywords:
            importance_count[kw['importance']] += 1

        return {
            'total': len(sorted_keywords),
            'by_importance': {
                'level_3_超重点': importance_count[3],
                'level_2_重点': importance_count[2],
                'level_1_普通重点': importance_count[1]
            },
            'keywords': sorted_keywords
        }

    # ==================== 文件处理方法 ====================

    def process_subtitle_file(self, json_path: str) -> Dict:
        """
        处理字幕JSON文件

        参数:
            json_path: 字幕JSON文件路径

        返回:
            处理结果
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'subtitles' in data:
            subtitles = data['subtitles']
        else:
            subtitles = data

        # 分析关键词
        subtitles = self.analyze_keywords(subtitles)

        # 保存回文件
        if isinstance(data, dict) and 'subtitles' in data:
            data['subtitles'] = subtitles
        else:
            data = subtitles

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 统计
        annotated = sum(1 for s in subtitles if s.get('keywords'))

        return {
            'status': 'success',
            'json_path': json_path,
            'annotated_count': annotated
        }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='关键词分析工具')
    parser.add_argument('json_path', help='字幕JSON文件路径')

    args = parser.parse_args()

    analyzer = KeywordAnalyzer()
    result = analyzer.process_subtitle_file(args.json_path)

    print(f"\n✅ 处理完成！标注了 {result['annotated_count']} 个字幕")
