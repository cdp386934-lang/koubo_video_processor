# 快速使用指南

## 设置完成 ✅

你的系统已经配置完成，现在可以自动将草稿生成到本地剪映 app 中！

## 使用步骤

### 1. 启动 CapCut Mate API 服务

在一个终端窗口中运行：

```bash
cd /Users/lottery/intership/code/capcut-mate
uv run main.py
```

保持这个服务运行。

### 2. 生成视频草稿

在另一个终端窗口中运行：

```bash
cd /Users/lottery/intership/code/koubo_video_processor
python3 main.py assets/videos/未加工.mp4 -o "我的草稿名称"
```

### 3. 在剪映中打开

1. 打开剪映 app
2. 在草稿列表中找到你的草稿（按名称搜索："我的草稿名称"）
3. 点击打开即可编辑和导出

## 工作流程

```
视频文件 → API 生成草稿 → 自动复制到本地 → 剪映 app 中打开
```

## 草稿位置

生成的草稿会自动保存到：
```
~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/草稿名称
```

## 示例输出

```
步骤9/9: 生成剪映草稿...
  正在通过 API 生成剪映草稿...
  ✅ 草稿已创建: https://capcut-mate.jcaigc.cn/openapi/capcut-mate/v1/get_draft?draft_id=xxx
  ✅ 背景已添加
  ✅ 主视频已添加
  ✅ 已添加 5 个素材
  ✅ 已添加 66 条字幕
  ✅ 已添加 2 个信息文本
  ✅ 草稿已保存: https://capcut-mate.jcaigc.cn/openapi/capcut-mate/v1/get_draft?draft_id=xxx
  ✅ 草稿已复制到本地: /Users/lottery/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/我的草稿名称
  ✅ 草稿已生成: /Users/lottery/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/我的草稿名称
```

## 常见问题

### Q: 草稿在剪映中看不到？
A:
1. 确保剪映 app 已完全关闭后重新打开
2. 检查草稿目录是否正确
3. 确认草稿文件已成功复制（查看输出日志）

### Q: API 服务连接失败？
A:
1. 确认 CapCut Mate API 服务正在运行
2. 访问 http://localhost:30000/docs 验证服务状态
3. 检查防火墙设置

### Q: 如何修改 API 地址？
A: 编辑 `modules/video/draft_generator.py`，修改 `__init__` 方法中的 `api_base_url` 参数

## 技术细节

- **API 服务**: CapCut Mate (FastAPI)
- **草稿格式**: 剪映原生格式
- **自动复制**: 从 API 服务的 output/draft 目录复制到本地剪映目录
- **支持平台**: macOS, Windows

## 更多信息

详细的技术文档请参考：
- [API_INTEGRATION.md](API_INTEGRATION.md) - API 集成说明
- [WORKFLOW.md](WORKFLOW.md) - 完整工作流程
