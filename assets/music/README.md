# 音乐文件目录

将你的背景音乐文件放在这个目录中。

## 支持的格式

- MP3（推荐）
- WAV
- M4A
- AAC
- FLAC

## 使用方法

1. 将音乐文件复制到此目录
2. 在配置文件中引用文件名
3. 运行处理程序

## 示例

```bash
# 复制音乐文件
cp ~/Downloads/background.mp3 music/bgm1.mp3

# 在配置文件中使用
{
  "music_segments": [
    {
      "start_time": 0,
      "end_time": 60,
      "music_file": "bgm1.mp3",
      "volume": 0.3
    }
  ]
}
```

## 查看可用音乐

```bash
python3 background_music_manager.py --list
```

## 注意事项

- 文件名不要包含中文或特殊字符
- 建议使用MP3格式（兼容性好）
- 音乐文件不要太大（建议<10MB）
