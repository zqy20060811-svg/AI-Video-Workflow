"""Provider 工厂：业务代码统一通过这里获取 Provider。"""

from app.services.providers.factory import get_image_provider, get_video_provider

__all__ = ["get_image_provider", "get_video_provider"]
