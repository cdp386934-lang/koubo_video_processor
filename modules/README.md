# 功能模块说明

本目录包含口播视频处理的所有核心功能模块，每个模块负责一个独立的功能领域。

## 模块列表

### 1. breath_remover.py - 去气口模块

**功能**：
- 基于文本检测气口（填充词、语气词）
- 基于音频分析检测气口（低能量+高过零率）
- 手动标记/取消标记气口
- 气口统计和报告

**主要类**：
- `BreathRemover`: 统一的去气口处理器

**使用示例**：
```python
from modules import BreathRemover

# 创建处理器
remover = BreathRemover()

# 处理字幕文件
result = remover.process_subtitle_file(
    'subtitles.json',
    audio_path='audio.wav',
    use_audio_analysis=True
)

# 查看统计
remover.print_statistics(result['statistics'])
```

**命令行使用**：
```bash
# 基础去气口
python modules/breath_remover.py subtitles.json

# 使用音频分析
python modules/breath_remover.py subtitles.json --audio audio.wav --audio-analysis

# 只查看统计
python modules/breath_remover.py subtitles.json --stats
```

---

### 2. keyword_analyzer.py - 关键词分析模块

**功能**：
- 使用DeepSeek大模型提取关键词
- 智能提取3-5个核心关键词（名词/动词，不超过4字）
- 自动在字幕中为关键词添加引号
- 保存关键词到JSON和TXT文件

**主要类**：
- `KeywordAnalyzer`: 统一的关键词分析器

**使用示例**：
```python
from modules import KeywordAnalyzer

# 创建分析器
analyzer = KeywordAnalyzer()

# 处理字幕文件
result = analyzer.process_subtitle_file('subtitles.json')

print(f"标注了 {result['annotated_count']} 个字幕")
```

**命令行使用**：
```bash
# 分析关键词
python modules/keyword_analyzer.py subtitles.json
```

**环境变量**：
```bash
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

---

### 3. material_manager.py - 素材管理模块

**功能**：
- 从Pexels搜索和下载视频素材
- 分析字幕，确定素材插入点
- 提取关键词用于素材搜索
- 素材缓存管理

**主要类**：
- `MaterialManager`: 统一的素材管理器

**使用示例**：
```python
from modules import MaterialManager

# 创建管理器
manager = MaterialManager()

# 配置
config = {
    'enabled': True,
    'insert_interval': 45,  # 每45秒插入一次
    'clip_duration': 4      # 素材时长4秒
}

# 处理字幕文件
result = manager.process_subtitle_file('subtitles.json', config)

print(f"插入了 {result['materials_count']} 个素材")
```

**命令行使用**：
```bash
# 插入素材
python modules/material_manager.py subtitles.json

# 自定义参数
python modules/material_manager.py subtitles.json --interval 60 --duration 5
```

**环境变量**：
```bash
PEXELS_API_KEY=your_api_key
```

---

## 模块整合使用

所有模块可以组合使用，实现完整的视频处理流程：

```python
from modules import BreathRemover, KeywordAnalyzer, MaterialManager

# 1. 去气口
remover = BreathRemover()
remover.process_subtitle_file('subtitles.json', 'audio.wav')

# 2. 关键词分析
analyzer = KeywordAnalyzer()
analyzer.process_subtitle_file('subtitles.json')

# 3. 素材插入
manager = MaterialManager()
config = {'enabled': True, 'insert_interval': 45, 'clip_duration': 4}
manager.process_subtitle_file('subtitles.json', config)
```

---

## 模块设计原则

1. **单一职责**：每个模块只负责一个功能领域
2. **独立运行**：每个模块都可以独立使用，也可以组合使用
3. **统一接口**：所有模块都提供 `process_subtitle_file()` 方法
4. **命令行支持**：所有模块都可以作为命令行工具使用
5. **错误处理**：所有模块都有完善的错误处理和日志输出

---

## 与原有代码的关系

这些模块是对原有代码的重构和整合：

- `breath_remover.py` 整合了 `audio_breath_remover.py` 和 `breath_remover_advanced.py`
- `keyword_analyzer.py` 整合了 `deepseek_analyzer.py` 和相关关键词提取功能
- `material_manager.py` 整合了 `pexels_fetcher.py`、`material_inserter.py` 和 `material_keyword_extractor.py`

原有文件仍然保留，以保持向后兼容。新代码可以使用这些模块，旧代码继续使用原有文件。

---

## 迁移指南

如果要将现有代码迁移到新模块：

### 旧代码：
```python
from audio_breath_remover import AudioBreathRemover
remover = AudioBreathRemover()
subtitles, count = remover.remove_breaths_from_subtitles(subtitles)
```

### 新代码：
```python
from modules import BreathRemover
remover = BreathRemover()
subtitles, count = remover.remove_breaths_from_subtitles(subtitles)
```

API保持一致，只需修改import语句即可。

---

## 测试

每个模块都可以独立测试：

```bash
# 测试去气口
python modules/breath_remover.py test_data/subtitles.json --stats

# 测试关键词分析
python modules/keyword_analyzer.py test_data/subtitles.json

# 测试素材管理
python modules/material_manager.py test_data/subtitles.json
```

---

## 扩展

如果需要添加新功能模块：

1. 在 `modules/` 目录下创建新的 `.py` 文件
2. 实现主要功能类
3. 提供 `process_subtitle_file()` 方法
4. 添加命令行入口（`if __name__ == '__main__'`）
5. 在 `__init__.py` 中导出类
6. 更新本文档

---

## 依赖

各模块的依赖：

- `breath_remover.py`:
  - 基础功能：无额外依赖
  - 音频分析：`librosa`, `numpy`

- `keyword_analyzer.py`:
  - `openai` (用于DeepSeek API)
  - `python-dotenv`

- `material_manager.py`:
  - `requests`
  - `python-dotenv`

安装所有依赖：
```bash
pip install openai python-dotenv requests librosa numpy
```
