"""
口播视频自动处理工具 - Web API接口
"""
import os
import sys
import tempfile
import shutil

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("错误: 需要安装FastAPI")
    print("请运行: pip install fastapi uvicorn python-multipart")
    sys.exit(1)

from modules.video.processor import KouboVideoProcessor

app = FastAPI(
    title="口播视频处理API",
    description="自动处理口播视频：ASR、字幕、去气口、关键词标注、美颜",
    version="0.1.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API根路径"""
    return {
        "name": "口播视频处理API",
        "version": "0.1.0",
        "endpoints": {
            "POST /process": "处理视频",
            "GET /health": "健康检查"
        }
    }


@app.post("/process")
async def process_video(
    video: UploadFile = File(..., description="视频文件"),
    template_path: str = Form(None, description="模板路径（可选）"),
    output_title: str = Form(None, description="输出标题（可选）")
):
    """
    处理口播视频

    参数:
        video: 视频文件
        template_path: 模板路径（可选）
        output_title: 输出标题（可选）

    返回:
        {
            "status": "success" or "failed",
            "draft_path": "草稿路径",
            "json_path": "字幕文件路径",
            "message": "处理信息"
        }
    """
    # 验证文件类型
    if not video.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        raise HTTPException(
            status_code=400,
            detail="不支持的视频格式，请上传 MP4, MOV, AVI 或 MKV 文件"
        )

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="koubo_")
    tmp_path = None

    try:
        # 保存上传的视频到临时文件
        tmp_path = os.path.join(temp_dir, video.filename)
        with open(tmp_path, 'wb') as f:
            content = await video.read()
            f.write(content)

        # 创建处理器
        processor = KouboVideoProcessor(
            video_path=tmp_path,
            template_path=template_path,
            output_title=output_title or os.path.splitext(video.filename)[0]
        )

        # 执行处理
        result = processor.process()

        return JSONResponse(content=result)

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        )

    finally:
        # 清理临时文件
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {e}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "koubo-video-processor"
    }


if __name__ == "__main__":
    import uvicorn
    print("启动口播视频处理API服务...")
    print("访问 http://localhost:8000/docs 查看API文档")
    uvicorn.run(app, host="0.0.0.0", port=8000)
