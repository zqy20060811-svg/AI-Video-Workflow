from app.core.config import settings
from app.services.providers.base import (
    BaseImageProvider,
    BaseVideoProvider,
    ImageRequest,
    ProviderError,
    VideoRequest,
)
from app.services.providers.comfyui_provider import ComfyUIImageProvider, ComfyUIVideoProvider
from app.services.providers.none_provider import (
    IMAGE_NOT_CONFIGURED_MSG,
    NoneImageProvider,
    NoneVideoProvider,
    VIDEO_NOT_CONFIGURED_MSG,
)

__all__ = [
    "BaseImageProvider",
    "BaseVideoProvider",
    "ImageRequest",
    "VideoRequest",
    "ProviderError",
    "get_image_provider",
    "get_video_provider",
    "IMAGE_NOT_CONFIGURED_MSG",
    "VIDEO_NOT_CONFIGURED_MSG",
]


def get_image_provider() -> BaseImageProvider:
    """根据 .env 的 IMAGE_PROVIDER 返回图片生成 Provider。"""
    name = settings.IMAGE_PROVIDER.strip().lower()
    if name in ("", "none"):
        raise ProviderError(IMAGE_NOT_CONFIGURED_MSG)
    if name == "comfyui":
        return ComfyUIImageProvider()
    raise ProviderError(f"未知的 IMAGE_PROVIDER：{settings.IMAGE_PROVIDER}（支持：none / comfyui）")


def get_video_provider() -> BaseVideoProvider:
    """根据 .env 的 VIDEO_PROVIDER 返回视频生成 Provider。"""
    name = settings.VIDEO_PROVIDER.strip().lower()
    if name in ("", "none"):
        raise ProviderError(VIDEO_NOT_CONFIGURED_MSG)
    if name == "comfyui":
        return ComfyUIVideoProvider()
    raise ProviderError(f"未知的 VIDEO_PROVIDER：{settings.VIDEO_PROVIDER}（支持：none / comfyui）")
