#!/usr/bin/env python3
"""
口播视频自动处理工具 - 命令行接口
"""
import argparse
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from modules.video.processor import KouboVideoProcessor
from modules.video.exporter import JianyingExporter


def main():
    parser = argparse.ArgumentParser(
        description='口播视频自动处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s video.mp4                          # 基本使用
  %(prog)s video.mp4 -o "我的视频"             # 指定标题
  %(prog)s video.mp4 -t custom.json           # 使用自定义模板
  %(prog)s video.mp4 --no-export              # 只生成草稿
        """
    )
    parser.add_argument(
        'video_path',
        help='输入视频路径'
    )
    parser.add_argument(
        '-t', '--template',
        help='模板配置路径（可选）',
        default=None
    )
    parser.add_argument(
        '-o', '--output-title',
        help='输出标题（可选）',
        default=None
    )
    parser.add_argument(
        '--no-export',
        action='store_true',
        help='不尝试自动导出，只生成草稿'
    )
    parser.add_argument(
        '-m', '--music-config',
        help='背景音乐配置文件路径（JSON格式）',
        default=None
    )
    parser.add_argument(
        '-c', '--config',
        help='完整配置文件路径（包含所有模块配置）',
        default=None
    )
    parser.add_argument(
        '-v', '--video-info',
        help='视频信息配置文件路径（标题、简介、作者信息）',
        default=None
    )

    args = parser.parse_args()

    # 检查视频文件是否存在
    if not os.path.exists(args.video_path):
        print(f"❌ 错误: 视频文件不存在: {args.video_path}")
        sys.exit(1)

    print("==" * 60)
    print("口播视频自动处理工具")
    print("=" * 60)
    print(f"输入视频: {args.video_path}")
    if args.output_title:
        print(f"输出标题: {args.output_title}")
    if args.template:
        print(f"使用模板: {args.template}")
    if args.config:
        print(f"配置文件: {args.config}")
    if args.music_config:
        print(f"音乐配置: {args.music_config}")
    if args.video_info:
        print(f"视频信息: {args.video_info}")
    print("=" * 60)
    print()

    # 创建处理器
    try:
        processor = KouboVideoProcessor(
            video_path=args.video_path,
            template_path=args.template,
            output_title=args.output_title
        )

        # 加载完整配置文件（如果提供）
        if args.config:
            import json
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 设置各模块配置
            if 'config' in config_data:
                # 预先创建JSON文件路径以便设置配置
                folder_path = os.path.dirname(args.video_path)
                video_name = os.path.splitext(os.path.basename(args.video_path))[0]
                json_path = os.path.join(folder_path, f"{video_name}.json")

                for module, module_config in config_data['config'].items():
                    processor.subtitle_json_manager.set_config(json_path, module, module_config)
                print(f"✅ 已加载配置: {', '.join(config_data['config'].keys())}")

            # 设置音乐配置（从config文件）
            if 'music' in config_data:
                processor.set_background_music(music_segments=config_data['music'])

        # 设置背景音乐（如果提供单独的音乐配置文件）
        if args.music_config:
            processor.set_background_music(music_config_path=args.music_config)

        # 设置视频信息（如果提供）
        if args.video_info:
            processor.set_video_info(video_info_config_path=args.video_info)

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    # 执行处理
    result = processor.process()

    # 输出结果
    print()
    print("=" * 60)
    if result['status'] == 'success':
        print("✅ 处理成功！")
        print()
        print(f"📁 草稿路径: {result['draft_path']}")
        print(f"📄 字幕文件: {result['json_path']}")
        print()

        if not args.no_export:
            print("尝试自动导出...")
            try:
                exporter = JianyingExporter(result['draft_path'])
                export_result = exporter.export()

                if export_result.get('auto_export'):
                    print("✅ 视频已自动导出")
                else:
                    print()
                    print(f"⚠️  需要手动导出 ({export_result.get('platform', 'Unknown')}平台):")
                    print()
                    for instruction in export_result.get('instructions', []):
                        print(f"  {instruction}")
                    print()
                    if export_result.get('tips'):
                        print("📌 提示:")
                        for tip in export_result['tips']:
                            print(f"  {tip}")
            except Exception as e:
                print(f"⚠️  自动导出失败: {e}")
                print()
                print("请手动在剪映中打开草稿并导出")
        else:
            print("ℹ️  已跳过自动导出（使用了 --no-export 选项）")
            print("   请手动在剪映中打开草稿并导出")

        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ 处理失败")
        print()
        print(f"错误信息: {result['message']}")
        if 'traceback' in result:
            print()
            print("详细错误:")
            print(result['traceback'])
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
