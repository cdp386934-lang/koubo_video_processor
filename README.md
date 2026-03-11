# 口播视频自动处理工具

这是一个完全独立的口播视频自动处理工具，不依赖任何外部项目接口。

## 最新更新 (v1.2.0)

### 🎉 流程优化

- ✨ **明确的处理流程** - 在生成草稿前完成所有字幕和关键字处理
- ✨ **关键字处理细化** - 生成关键字 → 贴入字幕 → 保存到JSON
- ✨ **详细的进度提示** - 每个步骤都有清晰的进度显示
- ✨ **完善的文档** - 新增WORKFLOW.md详细流程说明

### 处理流程

```
视频 → 音频 → 字幕 → 去气口 → 关键字 → 保存JSON → 草稿
```

**关键步骤：**
1. 生成字幕（ASR）
2. 生成关键字（DeepSeek AI）
3. 贴入字幕（加引号标记）
4. 保存到JSON
5. 生成草稿

## 最新更新 (v1.1.0)

### 🎉 新功能

- ✨ **音频去气口** - 自动生成去除气口后的音频文件
- ✨ **视频去气口** - 自动生成去除气口后的视频文件
- ✨ **画板背景配置** - 支持从assets目录读取背景图片
- ✨ **完整处理流程** - 从原始视频到去气口音频/视频的一站式处理

## 功能特性

- ✅ **视频转音频** - 使用 MoviePy 提取音频
- ✅ **语音识别 (ASR)** - 支持本地 Whisper 模型
- ✅ **去气口处理** - 自动检测、标记并生成去气口音频/视频
- ✅ **关键词标注** - 使用 AI 智能标注关键词
- ✅ **背景音乐** - 支持添加背景音乐
- ✅ **素材插入** - 支持 Pexels 素材获取
- ✅ **剪映草稿生成** - 独立实现，无需外部依赖
- ✅ **视频信息管理** - 标题、简介、作者信息

## 安装依赖

```bash
pip install -r requirements.txt
```

### 必需依赖

```bash
pip install moviepy pydub
```

### 可选依赖

如果需要使用本地 ASR 功能，请安装 Whisper：

```bash
pip install openai-whisper
```

如果需要音频分析功能：

```bash
pip install librosa numpy
```

## 使用方法

### 基本使用

```bash
python3 main.py video.mp4
```

### 指定标题

```bash
python3 main.py video.mp4 -o "我的视频"
```

### 使用自定义模板

```bash
python3 main.py video.mp4 -t custom.json
```

### 只生成草稿，不导出

```bash
python3 main.py video.mp4 --no-export
```

### 使用音乐配置

```bash
python3 main.py video.mp4 -m music_config.json
```

### 使用完整配置

```bash
python3 main.py video.mp4 -c config.json
```

### 使用视频信息配置

```bash
python3 main.py video.mp4 -v video_info.json
```

## 手动提供字幕

如果没有安装 Whisper 或 ASR 失败，可以手动提供字幕：

### 1. 创建字幕模板

```bash
python3 -m modules.asr.simple_asr template video.mp4
```

### 2. 导入 SRT 字幕

```bash
python3 -m modules.asr.simple_asr srt video.mp4 subtitle.srt
```

### 3. 导入文本文件

```bash
python3 -m modules.asr.simple_asr import video.mp4 subtitle.txt
```

## 文档

- 📖 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考（关键字处理流程）
- 📖 [WORKFLOW.md](WORKFLOW.md) - 详细处理流程说明
- 📖 [USAGE.md](USAGE.md) - 使用指南
- 📖 [agent.md](agent.md) - 完整功能模块文档
- 📖 [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - 流程优化总结

## 项目结构

```
koubo_video_processor/
├── main.py                          # 命令行入口
├── config.py                        # 配置管理
├── modules/
│   ├── video/
│   │   ├── processor.py            # 核心处理器
│   │   ├── draft_generator.py      # 独立草稿生成器
│   │   └── exporter.py             # 导出功能
│   ├── asr/
│   │   ├── local_asr.py            # 本地 ASR (Whisper)
│   │   └── simple_asr.py           # 简单 ASR (手动导入)
│   ├── audio/
│   │   ├── background_music_manager.py  # 背景音乐
│   │   └── breath_remover.py            # 去气口
│   ├── content/
│   │   ├── keyword_analyzer.py     # 关键词分析
│   │   ├── material_manager.py     # 素材管理
│   │   └── title_generator.py      # 标题生成
│   └── subtitle/
│       └── subtitle_json_manager.py # 字幕管理
├── assets/
│   └── templates/
│       └── koubo_default.json      # 默认模板
└── .env                            # 环境变量
```

## 环境变量配置

创建 `.env` 文件：

```env
# DeepSeek API (可选，用于关键词标注)
DEEPSEEK_API_KEY=your_deepseek_key

# Pexels API (可选，用于素材获取)
PEXELS_API_KEY=your_pexels_key
```

## 工作流程

1. **输入视频** → 视频文件路径
2. **视频转音频** → 提取音频轨道
3. **ASR识别** → 生成字幕JSON (使用本地 Whisper)
4. **去气口处理** → 标记气口片段
5. **关键词标注** → AI分析关键词 (可选)
6. **素材插入** → 下载并插入素材 (可选)
7. **背景音乐** → 添加背景音乐
8. **视频信息** → 添加标题和作者信息
9. **生成草稿** → 创建剪映草稿 (独立实现)
10. **导出视频** → 自动或手动导出

## 技术栈

- **Python 3.x** - 主要开发语言
- **MoviePy** - 视频处理
- **Whisper** - 本地语音识别 (可选)
- **DeepSeek** - AI分析 (可选)
- **Pexels** - 素材获取 (可选)

## 更新日志

### v2.0.0 - 完全独立版本

- ✅ 移除所有外部项目依赖
- ✅ 实现独立的 ASR 功能 (基于 Whisper)
- ✅ 实现独立的剪映草稿生成器
- ✅ 支持手动导入字幕 (SRT/文本)
- ✅ 完全自主的处理流程

## 许可证

请查看项目根目录的 LICENSE 文件。
