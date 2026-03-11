# CapCut Mate API 集成说明

## 概述

`draft_generator.py` 已修改为使用 CapCut Mate API 来生成剪映草稿，并自动将草稿复制到本地剪映 app 的草稿目录中。

## 前置条件

1. **启动 CapCut Mate API 服务**

   在使用草稿生成功能之前，需要先启动 CapCut Mate API 服务：

   ```bash
   cd /Users/lottery/intership/code/capcut-mate
   uv run main.py
   ```

   服务默认运行在 `http://localhost:30000`

2. **验证 API 服务**

   访问 API 文档页面确认服务正常运行：
   ```
   http://localhost:30000/docs
   ```

## 工作流程

1. **通过 API 生成草稿** - 调用 CapCut Mate API 创建草稿，草稿保存在 `capcut-mate/output/draft` 目录
2. **自动复制到本地** - 将生成的草稿自动复制到本地剪映 app 的草稿目录
3. **在剪映中打开** - 打开剪映 app，在草稿列表中找到并打开草稿

## 草稿路径

### API 生成的草稿
- 位置：`/Users/lottery/intership/code/capcut-mate/output/draft/{draft_id}`
- 返回 URL：`https://capcut-mate.jcaigc.cn/openapi/capcut-mate/v1/get_draft?draft_id={draft_id}`

### 本地剪映草稿
- macOS：`~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/{草稿名称}`
- Windows：`%LOCALAPPDATA%/JianyingPro/User Data/Projects/com.lveditor.draft/{草稿名称}`

生成器会自动将 API 生成的草稿复制到本地剪映目录，这样你就可以直接在剪映 app 中打开了。

## 使用方法

### 基本用法

```python
from modules.video.draft_generator import JianyingDraftGenerator

# 创建生成器实例（使用默认配置）
generator = JianyingDraftGenerator()

# 或指定自定义配置
generator = JianyingDraftGenerator(
    api_base_url="http://localhost:30000",
    capcut_mate_path="/path/to/capcut-mate"
)

# 生成草稿（会自动复制到本地剪映目录）
draft_path = generator.create_draft(
    video_path="path/to/video.mp4",
    json_path="path/to/subtitles.json",
    template_config=template_config,
    output_title="我的视频草稿"
)

print(f"草稿已生成: {draft_path}")
# 输出: 草稿已生成: /Users/lottery/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/我的视频草稿
```

### 命令行使用

```bash
python3 main.py assets/videos/未加工.mp4 -o "我的草稿"
```

执行后会：
1. 通过 API 生成草稿
2. 自动复制到本地剪映目录
3. 显示草稿路径

### 在剪映中打开

1. 打开剪映 app
2. 在草稿列表中找到你的草稿（按名称搜索）
3. 点击打开即可编辑

### 基本用法

```python
from modules.video.draft_generator import JianyingDraftGenerator

# 创建生成器实例（使用默认 API 地址）
generator = JianyingDraftGenerator()

# 或指定自定义 API 地址
generator = JianyingDraftGenerator(api_base_url="http://localhost:30000")

# 生成草稿
draft_url = generator.create_draft(
    video_path="path/to/video.mp4",
    json_path="path/to/subtitles.json",
    template_config=template_config,
    output_title="我的视频草稿"
)

print(f"草稿已生成: {draft_url}")
```

### API 端点说明

生成器会调用以下 CapCut Mate API 端点：

1. **创建草稿**: `POST /openapi/capcut-mate/v1/create_draft`
   - 创建一个新的剪映草稿

2. **添加视频**: `POST /openapi/capcut-mate/v1/add_videos`
   - 添加主视频和素材视频

3. **添加图片**: `POST /openapi/capcut-mate/v1/add_images`
   - 添加背景图片

4. **添加字幕**: `POST /openapi/capcut-mate/v1/add_captions`
   - 添加字幕、标题和作者信息

5. **保存草稿**: `POST /openapi/capcut-mate/v1/save_draft`
   - 保存并完成草稿

## 主要变化

### 之前（使用 pyJianYingDraft）
- 直接在本地生成草稿文件
- 需要导入 pyJianYingDraft 库
- 所有操作都在本地完成

### 现在（使用 CapCut Mate API）
- 通过 HTTP API 调用生成草稿
- 不再直接依赖 pyJianYingDraft（API 服务内部使用）
- 支持远程部署和服务化

## 优势

1. **服务化**: 可以将草稿生成功能部署为独立服务
2. **解耦**: 业务逻辑与草稿生成逻辑分离
3. **可扩展**: 易于添加新功能和优化
4. **统一接口**: 使用标准的 RESTful API
5. **云渲染**: 可以对接剪映云渲染功能

## 错误处理

如果 API 调用失败，会抛出 `RuntimeError` 异常：

```python
try:
    draft_url = generator.create_draft(...)
except RuntimeError as e:
    print(f"草稿生成失败: {e}")
```

常见错误：
- API 服务未启动
- 网络连接问题
- 文件路径不存在
- API 参数错误

## 配置

可以通过环境变量或配置文件设置 API 地址：

```python
import os

api_url = os.getenv('CAPCUT_API_URL', 'http://localhost:30000')
generator = JianyingDraftGenerator(api_base_url=api_url)
```

## 注意事项

1. 确保 CapCut Mate API 服务在调用前已启动
2. 视频和素材文件路径必须是 API 服务可访问的路径
3. API 调用有超时设置（默认 30-60 秒）
4. 大文件上传可能需要更长时间
