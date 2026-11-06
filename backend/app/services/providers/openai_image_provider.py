"""OpenAI 兼容图片生成 Provider（硅基流动 / OpenAI / 其他 /v1/images/generations 服务）。

通过 .env 配置：
  IMAGE_PROVIDER=openai_compatible
  IMAGE_BASE_URL=https://api.siliconflow.cn/v1   （硅基流动，注册免费送额度）
  IMAGE_API_KEY=sk-xxx
  IMAGE_MODEL=Kwai-Kolors/Kolors

响应同时兼容 OpenAI 格式（data[].url / data[].b64_json）与硅基流动格式（images[].url）。
"""

import base64

import httpx

from app.core.config import settings
from app.services.providers.base import BaseImageProvider, ImageRequest, ProviderError

NO_KEY_MSG = (
    "IMAGE_PROVIDER=openai_compatible 但未配置 IMAGE_API_KEY。\n"
    "推荐：注册硅基流动 https://cloud.siliconflow.cn（免费送额度），\n"
    "创建 API Key 后填入 backend/.env 的 IMAGE_API_KEY，重启后端即可。"
)


class OpenAICompatibleImageProvider(BaseImageProvider):
    name = "openai_compatible"
    model = settings.IMAGE_MODEL

    def generate_image(self, request: ImageRequest) -> bytes:
        if not settings.IMAGE_API_KEY:
            raise ProviderError(NO_KEY_MSG)

        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "image_size": f"{request.width}x{request.height}",
            "batch_size": 1,
            # 注：硅基流动 Kolors 强制「AI 生成」水印，watermark=0/False 均实测无效
        }
        headers = {"Authorization": f"Bearer {settings.IMAGE_API_KEY}"}
        base = settings.IMAGE_BASE_URL.rstrip("/")
        try:
            resp = httpx.post(
                f"{base}/images/generations",
                json=payload,
                headers=headers,
                timeout=180.0,
            )
        except httpx.HTTPError as e:
            raise ProviderError(
                f"图片生成 API 请求失败（{base}）：{e}\n"
                "请检查网络 / IMAGE_BASE_URL / IMAGE_API_KEY 配置。"
            ) from e
        if resp.status_code >= 400:
            raise ProviderError(
                f"图片生成 API 返回错误（HTTP {resp.status_code}）：{resp.text[:200]}\n"
                "请检查 IMAGE_MODEL 名称与账户额度。"
            )

        body = resp.json()
        # 硅基流动格式：images[].url；OpenAI 格式：data[].url / data[].b64_json
        items = body.get("images") or body.get("data") or []
        if not items:
            raise ProviderError(f"图片生成 API 返回内容为空：{str(body)[:200]}")
        item = items[0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"])
        url = item.get("url")
        if not url:
            raise ProviderError(f"图片生成 API 返回中没有图片地址：{str(item)[:200]}")
        try:
            img = httpx.get(url, timeout=120.0, follow_redirects=True)
        except httpx.HTTPError as e:
            raise ProviderError(f"下载生成图片失败：{e}") from e
        if img.status_code >= 400:
            raise ProviderError(f"下载生成图片失败（HTTP {img.status_code}）")
        return img.content
