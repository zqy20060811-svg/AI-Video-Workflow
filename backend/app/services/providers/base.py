"""Provider 抽象：图片 / 视频生成服务的统一接口。

具体实现由 .env 配置决定（IMAGE_PROVIDER / VIDEO_PROVIDER），
业务代码只依赖这里的抽象，不耦合任何具体模型。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(Exception):
    """Provider 调用失败（含未配置、连接失败、生成失败）。"""


@dataclass
class ImageRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 768
    height: int = 432


@dataclass
class VideoRequest:
    prompt: str
    image: bytes  # 首帧参考图（已确认的场景图）
    image_ext: str  # 如 ".png"
    duration: float = 4.0  # 秒
    width: int = 768
    height: int = 432


class BaseImageProvider(ABC):
    """图片生成 Provider。返回图片二进制数据。"""

    name: str = "base"
    model: str = ""

    @abstractmethod
    def generate_image(self, request: ImageRequest) -> bytes: ...


class BaseVideoProvider(ABC):
    """视频生成 Provider（Image-to-Video）。返回视频二进制数据。"""

    name: str = "base"
    model: str = ""

    @abstractmethod
    def generate_video(self, request: VideoRequest) -> bytes: ...
