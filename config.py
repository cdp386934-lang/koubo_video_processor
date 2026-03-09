"""
配置管理模块
"""
import os
from pathlib import Path


class Config:
    """配置类"""

    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent

    # 模板目录
    TEMPLATES_DIR = PROJECT_ROOT / "templates"

    # 默认模板
    DEFAULT_TEMPLATE = TEMPLATES_DIR / "koubo_default.json"

    # 临时文件目录
    TEMP_DIR = Path(os.environ.get('TMPDIR', '/tmp')) / "koubo_video_processor"

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = PROJECT_ROOT / "koubo_processor.log"

    # API配置
    API_HOST = os.environ.get('API_HOST', '0.0.0.0')
    API_PORT = int(os.environ.get('API_PORT', 8000))

    # 视频处理配置
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']
    MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1GB

    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


# 创建全局配置实例
config = Config()
