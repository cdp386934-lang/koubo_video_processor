from setuptools import setup, find_packages
import os

# 读取README
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = '口播视频自动处理工具'

setup(
    name="koubo-video-processor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'moviepy==1.0.3',
        'requests',
        'python-dotenv',
        'fastapi',
        'uvicorn',
        'python-multipart',
    ],
    extras_require={
        'gui': ['pyautogui'],
    },
    entry_points={
        'console_scripts': [
            'koubo-process=koubo_video_processor.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="口播视频自动处理工具：ASR、字幕、去气口、关键词标注、美颜",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/koubo-video-processor",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.10',
    include_package_data=True,
    package_data={
        'koubo_video_processor': ['templates/*.json'],
    },
)
