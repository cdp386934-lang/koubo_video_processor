# 口播视频自动处理工具 - Agent 功能模块文档

## 项目概述

这是一个自动化处理口播视频的工具，可以将视频转换为剪映草稿，支持字幕生成、去气口、关键词标注、背景音乐、素材插入等功能。

## 核心功能模块

### 1. 视频处理核心模块 (processor.py)

**功能描述：** 视频处理的主控制器，协调所有子模块完成完整的处理流程。

**主要功能：**
- 视频转音频提取
- 音频转文字（ASR）
- 去气口处理
- 关键词标注
- 背景音乐添加
- 视频信息应用（标题、简介、作者）
- 剪映草稿生成

**处理流程：**
1. 步骤1: 视频转音频
2. 步骤2: 音频转文字（ASR）
3. 步骤3: 去气口处理
4. 步骤4: DeepSeek 关键词标注
5. 步骤5: 添加背景音乐
6. 步骤6: 应用视频信息
7. 步骤7: 生成剪映草稿

**关键类：**
- `KouboVideoProcessor`: 主处理器类

**配置项：**
- `video_path`: 输入视频路径
- `template_path`: 模板配置路径
- `output_title`: 输出标题

---

### 2. ASR（语音识别）模块

#### 2.1 本地ASR (local_asr.py)
**功能描述：** 本地语音识别服务，将音频转换为文字字幕。

**主要功能：**
- 音频文件转文字
- 生成带时间戳的字幕JSON

#### 2.2 简单ASR (simple_asr.py)
**功能描述：** 简化的ASR工具，支持模板生成和SRT导入。

**主要功能：**
- 生成字幕模板
- 导入SRT字幕文件
- 转换为标准JSON格式

**使用示例：**
```bash
# 生成模板
python3 simple_asr.py template video.mp4

# 导入SRT
python3 simple_asr.py srt video.mp4 subtitle.srt
```

---

### 3. 字幕管理模块 (subtitle_json_manager.py)

**功能描述：** 统一管理字幕JSON文件，支持新旧格式转换和配置管理。

**主要功能：**
- 加载和保存字幕JSON文件
- 新旧格式自动转换
- 模块配置管理（ASR、去气口、DeepSeek等）
- 处理步骤记录和追踪
- 音乐配置读取

**数据格式：**
```json
{
  "subtitles": [...],
  "config": {
    "asr": {...},
    "breath_removal": {...},
    "deepseek": {...}
  },
  "music": [...],
  "processing_steps": [...]
}
```

**关键方法：**
- `load_subtitle_json()`: 加载字幕文件
- `save_subtitle_json()`: 保存字幕文件
- `get_config()`: 获取模块配置
- `set_config()`: 设置模块配置
- `add_processing_step()`: 记录处理步骤

---

### 4. 背景音乐模块 (background_music_manager.py)

**功能描述：** 管理视频的背景音乐，支持多段音乐配置。

**主要功能：**
- 加载音乐配置文件
- 创建音乐片段配置
- 音乐时间轴管理
- 音量和淡入淡出控制

**配置格式：**
```json
{
  "music": [
    {
      "path": "music/bgm.mp3",
      "start_time": 0,
      "duration": 30000,
      "volume": 0.3,
      "fade_in": 1000,
      "fade_out": 1000
    }
  ]
}
```

**关键类：**
- `BackgroundMusicManager`: 音乐管理器

---

### 5. 素材插入模块

#### 5.1 Pexels素材获取 (pexels_fetcher.py)
**功能描述：** 从Pexels平台获取免费视频素材。

**主要功能：**
- 根据关键词搜索视频素材
- 下载高质量视频
- 素材缓存管理

**配置项：**
- `PEXELS_API_KEY`: Pexels API密钥
- `enabled`: 是否启用素材获取

#### 5.2 关键词提取 (material_keyword_extractor.py)
**功能描述：** 使用AI提取字幕中的关键词，用于素材搜索。

**主要功能：**
- AI智能关键词提取
- 上下文分析
- 关键词优化

**关键类：**
- `MaterialKeywordExtractor`: 关键词提取器

#### 5.3 素材插入器 (material_inserter.py)
**功能描述：** 分析字幕并在合适位置插入素材。

**主要功能：**
- 分析字幕段落
- 识别素材插入点
- 插入素材标记到字幕JSON

**配置项：**
```json
{
  "pexels_config": {
    "enabled": true,
    "min_segment_duration": 5000,
    "max_materials": 10
  }
}
```

---

### 6. AI分析模块 (deepseek_analyzer.py)

**功能描述：** 使用DeepSeek AI分析字幕内容，标注关键词。

**主要功能：**
- 字幕内容分析
- 关键词智能标注
- 重点内容识别

**配置项：**
- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `enable_deepseek`: 是否启用DeepSeek分析

**关键类：**
- `DeepSeekAnalyzer`: DeepSeek分析器

**使用场景：**
- 自动识别视频中的重点内容
- 为关键词添加特殊样式
- 辅助素材搜索

---

### 7. 标题生成模块 (title_generator.py)

**功能描述：** 管理视频信息，包括标题、简介、作者信息。

**主要功能：**
- 视频标题生成
- 作者信息配置
- 视频简介管理

**配置格式：**
```json
{
  "title": {
    "enabled": true,
    "text": "视频标题",
    "style": {...}
  },
  "author_info": {
    "enabled": true,
    "name": "作者名称",
    "title": "职位",
    "subtitle": "简介"
  }
}
```

**关键类：**
- `VideoInfoManager`: 视频信息管理器

---

### 8. 导出功能模块 (exporter.py)

**功能描述：** 将生成的草稿导出为视频文件。

**主要功能：**
- 自动导出检测
- 平台适配（Mac/Windows）
- 导出指令生成

**关键类：**
- `JianyingExporter`: 剪映导出器

**使用方式：**
```python
exporter = JianyingExporter(draft_path)
result = exporter.export()
```

---

### 9. API客户端模块 (api_client.py)

**功能描述：** 封装所有外部API调用。

**主要功能：**
- ASR服务调用
- 草稿生成服务调用
- API错误处理

**关键方法：**
- `video_to_text()`: 视频转文字
- `create_draft()`: 创建草稿

---

### 10. 音频处理模块

#### 10.1 音频去气口 (audio_breath_remover.py)
**功能描述：** 检测并标记音频中的气口声。

**主要功能：**
- 气口声检测
- 静音片段识别
- 字幕标记更新

#### 10.2 高级去气口 (breath_remover_advanced.py)
**功能描述：** 更高级的气口检测算法。

**主要功能：**
- 多维度气口检测
- 自适应阈值
- 更精确的识别

**配置项：**
```json
{
  "breath_removal": {
    "enabled": true,
    "threshold": 0.02,
    "min_duration": 200
  }
}
```

---

## 命令行接口 (main.py)

**使用方式：**
```bash
# 基本使用
python3 main.py video.mp4

# 指定标题
python3 main.py video.mp4 -o "我的视频"

# 使用自定义模板
python3 main.py video.mp4 -t custom.json

# 只生成草稿，不导出
python3 main.py video.mp4 --no-export

# 使用音乐配置
python3 main.py video.mp4 -m music_config.json

# 使用完整配置
python3 main.py video.mp4 -c config.json

# 使用视频信息配置
python3 main.py video.mp4 -v video_info.json
```

**参数说明：**
- `-t, --template`: 模板配置路径
- `-o, --output-title`: 输出标题
- `--no-export`: 不自动导出
- `-m, --music-config`: 背景音乐配置
- `-c, --config`: 完整配置文件
- `-v, --video-info`: 视频信息配置

---

## 配置文件说明

### 模板配置 (templates/koubo_default.json)
包含视频处理的所有默认配置，包括：
- 视频布局设置
- 字幕样式
- 背景音乐
- 素材插入规则
- AI分析配置

### 环境变量 (.env)
```env
# API密钥
PEXELS_API_KEY=your_pexels_key
DEEPSEEK_API_KEY=your_deepseek_key

# 火山引擎配置（ASR）
VOLC_ACCESS_KEY=your_access_key
VOLC_SECRET_KEY=your_secret_key
```

---

## 工作流程

1. **输入视频** → 视频文件路径
2. **视频转音频** → 提取音频轨道
3. **ASR识别** → 生成字幕JSON
4. **去气口处理** → 标记气口片段
5. **关键词标注** → AI分析关键词
6. **素材插入** → 下载并插入素材
7. **背景音乐** → 添加背景音乐
8. **视频信息** → 添加标题和作者信息
9. **生成草稿** → 创建剪映草稿
10. **导出视频** → 自动或手动导出

---

## 扩展开发指南

### 添加新的处理模块

1. 在 `processor.py` 中添加新的处理方法
2. 在处理流程中调用新方法
3. 在 `subtitle_json_manager.py` 中添加配置支持
4. 更新模板配置文件

### 自定义模板

1. 复制 `templates/koubo_default.json`
2. 修改配置项
3. 使用 `-t` 参数指定自定义模板

### 集成新的AI服务

1. 创建新的分析器类（参考 `deepseek_analyzer.py`）
2. 在 `processor.py` 中初始化分析器
3. 在处理流程中调用分析方法

---

## 常见问题

### Q: ASR识别失败怎么办？
A: 可以使用以下方式手动提供字幕：
- `python3 simple_asr.py template video.mp4` 生成模板
- `python3 simple_asr.py srt video.mp4 subtitle.srt` 导入SRT

### Q: 如何禁用某个功能模块？
A: 在配置文件中设置对应模块的 `enabled: false`

### Q: 素材下载失败？
A: 检查 PEXELS_API_KEY 是否正确配置

### Q: 草稿生成失败？
A: 确保剪映已安装，且路径正确

---

## 技术栈

- **Python 3.x**: 主要开发语言
- **MoviePy**: 视频处理
- **火山引擎**: ASR服务
- **DeepSeek**: AI分析
- **Pexels**: 素材获取
- **剪映API**: 草稿生成

---

## 项目结构

```
koubo_video_processor/
├── main.py                          # 命令行入口
├── processor.py                     # 核心处理器
├── api_client.py                    # API客户端
├── subtitle_json_manager.py         # 字幕管理
├── background_music_manager.py      # 背景音乐
├── deepseek_analyzer.py            # AI分析
├── pexels_fetcher.py               # 素材获取
├── material_inserter.py            # 素材插入
├── material_keyword_extractor.py   # 关键词提取
├── title_generator.py              # 标题生成
├── exporter.py                     # 导出功能
├── local_asr.py                    # 本地ASR
├── simple_asr.py                   # 简单ASR
├── audio_breath_remover.py         # 去气口
├── breath_remover_advanced.py      # 高级去气口
├── config.py                       # 配置管理
├── templates/                      # 模板目录
│   └── koubo_default.json         # 默认模板
└── .env                           # 环境变量
```

---

## 更新日志

查看各模块的更新历史和功能变更。

---

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

---

## 许可证

请查看项目根目录的LICENSE文件。
