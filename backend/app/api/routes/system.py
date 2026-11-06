"""系统信息 API：当前模型配置 + 本地生成环境检查。"""

import subprocess

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/config")
def get_config():
    """返回当前生效的模型配置（供前端「模型设置」页展示）。"""
    image_configured = settings.IMAGE_PROVIDER.strip().lower() not in ("", "none")
    video_configured = settings.VIDEO_PROVIDER.strip().lower() not in ("", "none")
    return {
        "llm": {
            "provider": "openai_compatible",
            "base_url": settings.LLM_BASE_URL,
            "model": settings.LLM_MODEL,
        },
        "image": {
            "provider": settings.IMAGE_PROVIDER,
            "model": settings.IMAGE_MODEL,
            "configured": image_configured,
        },
        "video": {
            "provider": settings.VIDEO_PROVIDER,
            "model": settings.VIDEO_MODEL,
            "clip_model": settings.VIDEO_CLIP_MODEL,
            "vae_model": settings.VIDEO_VAE_MODEL,
            "fps": settings.VIDEO_FPS,
            "configured": video_configured,
        },
        "comfyui_url": settings.COMFYUI_URL,
    }


def _check_nvidia_gpu() -> dict:
    """通过 nvidia-smi 获取 GPU 名称、显存、驱动。"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return {"available": False, "detail": "nvidia-smi 执行失败（可能没有 NVIDIA 显卡）"}
        name, vram, driver = [x.strip() for x in result.stdout.strip().split(",")]
        return {"available": True, "name": name, "vram": vram, "driver": driver}
    except FileNotFoundError:
        return {"available": False, "detail": "未检测到 nvidia-smi（没有 NVIDIA 显卡或未装驱动）"}
    except Exception as e:  # noqa: BLE001
        return {"available": False, "detail": f"nvidia-smi 检查失败：{e}"}


def _check_pytorch() -> dict:
    try:
        import torch  # noqa: PLC0415

        return {
            "installed": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        }
    except ImportError:
        return {"installed": False, "detail": "后端未安装 PyTorch（不影响通过 ComfyUI 生成）"}


def _check_comfyui() -> dict:
    base = settings.COMFYUI_URL.rstrip("/")
    try:
        resp = httpx.get(f"{base}/system_stats", timeout=3.0)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        return {"reachable": False, "url": base, "detail": f"无法连接 ComfyUI（{base}）：{type(e).__name__}"}

    data = {}
    # 检查已安装的 checkpoint / unet 模型
    try:
        ckpts = httpx.get(f"{base}/object_info/CheckpointLoaderSimple", timeout=5.0).json()
        ckpt_list = ckpts["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        data["image_models"] = ckpt_list
        data["image_model_ready"] = bool(settings.IMAGE_MODEL) and settings.IMAGE_MODEL in ckpt_list
    except Exception:  # noqa: BLE001
        data["image_models"] = []
        data["image_model_ready"] = None
    try:
        unets = httpx.get(f"{base}/object_info/UNETLoader", timeout=5.0).json()
        unet_list = unets["UNETLoader"]["input"]["required"]["unet_name"][0]
        data["video_models"] = unet_list
        data["video_model_ready"] = bool(settings.VIDEO_MODEL) and settings.VIDEO_MODEL in unet_list
    except Exception:  # noqa: BLE001
        data["video_models"] = []
        data["video_model_ready"] = None
    return {"reachable": True, "url": base, **data}


@router.get("/check-env")
def check_env():
    """检查本地生成环境：GPU / 显存 / PyTorch / ComfyUI / 模型是否就绪。"""
    gpu = _check_nvidia_gpu()
    return JSONResponse(
        content={
            "gpu": gpu,
            "pytorch": _check_pytorch(),
            "comfyui": _check_comfyui(),
            "image_provider": settings.IMAGE_PROVIDER,
            "video_provider": settings.VIDEO_PROVIDER,
        }
    )
