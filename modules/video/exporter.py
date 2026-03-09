import os
import time
import subprocess
import sys
import platform

# 判断操作系统
IS_WINDOWS = platform.system() == 'Windows'


class JianyingExporter:
    """剪映自动化导出器"""

    def __init__(self, draft_path):
        self.draft_path = draft_path
        self.jianying_path = self._find_jianying()

    def _find_jianying(self):
        """查找剪映可执行文件"""
        if IS_WINDOWS:
            # Windows路径
            possible_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''),
                           'JianyingPro/JianyingPro.exe'),
                'C:/Program Files/JianyingPro/JianyingPro.exe',
            ]
        else:
            # macOS路径
            possible_paths = [
                '/Applications/JianyingPro.app',
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise Exception("未找到剪映安装路径")

    def export(self, output_path=None):
        """
        尝试自动导出视频

        策略：
        1. 尝试使用剪映命令行接口（如果存在）
        2. 如果不存在，使用GUI自动化（pyautogui）
        3. 如果都失败，返回手动导出指引
        """
        # 策略1: 尝试命令行导出
        try:
            return self._export_via_cli(output_path)
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"命令行导出失败: {e}")

        # 策略2: 尝试GUI自动化
        try:
            return self._export_via_gui(output_path)
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"GUI自动化导出失败: {e}")

        # 策略3: 返回详细的手动导出指引
        return self._get_manual_export_guide()

    def _export_via_cli(self, output_path):
        """通过命令行导出（如果剪映支持）"""
        # 注意：剪映可能不支持命令行导出，这里是预留接口
        raise NotImplementedError("剪映暂不支持命令行导出")

    def _export_via_gui(self, output_path):
        """通过GUI自动化导出"""
        try:
            import pyautogui
        except ImportError:
            raise NotImplementedError("需要安装pyautogui: pip install pyautogui")

        # 1. 打开剪映
        if IS_WINDOWS:
            subprocess.Popen([self.jianying_path])
        else:
            subprocess.Popen(['open', self.jianying_path])

        time.sleep(5)  # 等待剪映启动

        # 2. 打开草稿（这里需要根据实际情况调整）
        # 注意：这部分高度依赖剪映的UI，可能需要调整

        # 3. 导出视频
        # ...

        raise NotImplementedError("GUI自动化导出尚未完全实现")

    def _get_manual_export_guide(self):
        """
        获取详细的手动导出指引

        返回:
            包含详细导出步骤的字典
        """
        if IS_WINDOWS:
            instructions = [
                "1. 打开剪映专业版",
                f"2. 在草稿列表中找到并打开草稿",
                f"   草稿路径: {self.draft_path}",
                "3. 检查视频效果：",
                "   - 字幕是否正确显示",
                "   - 重点字是否有特效（颜色、动画）",
                "   - 素材是否正确插入",
                "   - 美颜效果是否应用",
                "4. 点击右上角的「导出」按钮",
                "5. 在导出设置中：",
                "   - 分辨率：建议选择 1080p 或更高",
                "   - 帧率：建议选择 30fps 或 60fps",
                "   - 码率：建议选择「高」或「超高」",
                "   - 格式：建议选择 MP4",
                "6. 选择导出路径",
                "7. 点击「开始导出」",
                "8. 等待导出完成（时间取决于视频长度和电脑性能）"
            ]

            tips = [
                "💡 导出前建议先预览视频，确保效果符合预期",
                "💡 如果视频较长，导出可能需要较长时间，请耐心等待",
                "💡 导出时建议关闭其他占用资源的程序，以提高导出速度",
                "💡 导出完成后，建议检查视频质量和音画同步"
            ]
        else:
            # macOS
            instructions = [
                "1. 打开剪映专业版",
                "   方式1: 在启动台中找到「剪映专业版」",
                "   方式2: 使用Spotlight搜索「剪映」",
                f"2. 在草稿列表中找到并打开草稿",
                f"   草稿路径: {self.draft_path}",
                "   提示: 草稿通常按创建时间排序，最新的在最上面",
                "3. 检查视频效果：",
                "   - 字幕是否正确显示",
                "   - 重点字是否有特效（颜色、动画）",
                "   - 素材是否正确插入",
                "   - 美颜效果是否应用",
                "   - 视频标题是否显示",
                "4. 点击右上角的「导出」按钮（或使用快捷键 ⌘E）",
                "5. 在导出设置中：",
                "   - 分辨率：建议选择 1080p (1080×1920) 或更高",
                "   - 帧率：建议选择 30fps 或 60fps",
                "   - 码率：建议选择「高」或「超高」",
                "   - 格式：建议选择 MP4（兼容性最好）",
                "   - 编码：建议选择 H.264（兼容性好）或 H.265（文件更小）",
                "6. 选择导出路径（建议保存到「下载」或「桌面」文件夹）",
                "7. 点击「开始导出」",
                "8. 等待导出完成（时间取决于视频长度和电脑性能）",
                "   - 可以在导出窗口查看进度",
                "   - 导出期间可以继续使用电脑，但建议不要关闭剪映"
            ]

            tips = [
                "💡 导出前建议先预览视频（按空格键播放），确保效果符合预期",
                "💡 如果视频较长，导出可能需要较长时间，请耐心等待",
                "💡 导出时建议连接电源，避免电量不足导致导出中断",
                "💡 导出时建议关闭其他占用资源的程序（如视频编辑软件、游戏等），以提高导出速度",
                "💡 导出完成后，建议检查视频质量、音画同步和字幕显示",
                "💡 如果导出失败，可以尝试降低分辨率或码率后重新导出"
            ]

        return {
            'auto_export': False,
            'message': '请按以下步骤手动导出视频',
            'draft_path': self.draft_path,
            'instructions': instructions,
            'tips': tips,
            'platform': 'Windows' if IS_WINDOWS else 'macOS'
        }
