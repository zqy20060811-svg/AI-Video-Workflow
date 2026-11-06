"""未配置 Provider：明确告知用户如何配置，绝不假装能生成。"""

from app.services.providers.base import (
    BaseImageProvider,
    BaseVideoProvider,
    ImageRequest,
    ProviderError,
    VideoRequest,
)

IMAGE_NOT_CONFIGURED_MSG = (
    "当前未配置图片生成模型（IMAGE_PROVIDER=none）。\n"
    "你可以：\n"
    "1. 本地安装 ComfyUI，并在 .env 设置 IMAGE_PROVIDER=comfyui、IMAGE_MODEL=模型名\n"
    "2. 配置其他图片生成模型 API\n"
    "详见「模型设置」页面或 README。"
)

VIDEO_NOT_CONFIGURED_MSG = (
    "当前未配置视频生成模型（VIDEO_PROVIDER=none）。\n"
    "你可以：\n"
    "1. 本地安装 ComfyUI + LTX-Video 等开源 I2V 模型，并在 .env 设置 VIDEO_PROVIDER=comfyui\n"
    "2. 配置其他视频生成模型 API\n"
    "详见「模型设置」页面或 README。"
)


class NoneImageProvider(BaseImageProvider):
    name = "none"

    def generate_image(self, request: ImageRequest) -> bytes:
        raise ProviderError(IMAGE_NOT_CONFIGURED_MSG)


class NoneVideoProvider(BaseVideoProvider):
    name = "none"

    def generate_video(self, request: VideoRequest) -> bytes:
        raise ProviderError(VIDEO_NOT_CONFIGURED_MSG)
