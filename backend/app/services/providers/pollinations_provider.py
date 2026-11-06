"""Pollinations.ai 图片生成 Provider。

完全免费、无需 API Key、无需注册：直接 GET 请求返回图片（默认 Flux 模型）。
适合个人工作流的零成本内部图片生成；失败时（限流/网络）前端会明确报错。
"""

import random
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.services.providers.base import BaseImageProvider, ImageRequest, ProviderError


class PollinationsImageProvider(BaseImageProvider):
    name = "pollinations"
    model = settings.IMAGE_MODEL or "flux"

    def generate_image(self, request: ImageRequest) -> bytes:
        params = {
            "width": request.width,
            "height": request.height,
            "seed": random.randint(0, 2**31 - 1),
            "nologo": "true",
            "model": self.model,
        }
        url = f"https://image.pollinations.ai/prompt/{quote(request.prompt, safe='')}"
        try:
            resp = httpx.get(url, params=params, timeout=300.0, follow_redirects=True)
        except httpx.HTTPError as e:
            raise ProviderError(
                f"Pollinations 图片生成请求失败：{e}\n"
                "可检查网络后重试，或在 .env 切换 IMAGE_PROVIDER（comfyui / manual 上传）。"
            ) from e
        if resp.status_code >= 400:
            raise ProviderError(
                f"Pollinations 返回错误（HTTP {resp.status_code}），可能触发了限流，请稍后重试。"
            )
        content_type = resp.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ProviderError(f"Pollinations 返回的不是图片（content-type: {content_type}）")
        return resp.content
