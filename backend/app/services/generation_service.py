"""图片/视频生成服务：连接 Shot 与 Provider，产物落盘并写入 Asset 记录。

流程约定：
- 图片：shot.image_prompt + 项目画面比例 → ImageProvider → storage/projects/{pid}/shots/{sid}/images/
- 视频：已确认的图片 + shot.video_prompt + duration → VideoProvider → .../videos/
- 重新生成保留旧文件，每次生成产生 version+1 的新 Asset。
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Asset, Project, Shot
from app.services import storage_service
from app.services.providers import get_image_provider, get_video_provider
from app.services.providers.base import ImageRequest, ProviderError, VideoRequest

# 画面比例 → 像素尺寸（宽高为 8 的倍数）
ASPECT_SIZES: dict[str, tuple[int, int]] = {
    "16:9": (768, 432),
    "9:16": (432, 768),
    "4:3": (640, 480),
    "3:4": (480, 640),
    "1:1": (512, 512),
}

DEFAULT_SIZE = (768, 432)


def size_for_aspect(aspect_ratio: str | None) -> tuple[int, int]:
    return ASPECT_SIZES.get((aspect_ratio or "").strip(), DEFAULT_SIZE)


def _latest_asset(db: Session, shot_id: int, asset_type: str) -> Asset | None:
    return (
        db.query(Asset)
        .filter(Asset.shot_id == shot_id, Asset.asset_type == asset_type)
        .order_by(Asset.id.desc())
        .first()
    )


def _next_version(db: Session, shot_id: int, asset_type: str) -> int:
    latest = _latest_asset(db, shot_id, asset_type)
    return (latest.version + 1) if latest else 1


def generate_scene_image(db: Session, shot: Shot, project: Project) -> Asset:
    """为镜头生成场景图。provider 未配置时抛 ProviderError（带用户引导）。"""
    if not shot.image_prompt or not shot.image_prompt.strip():
        raise ProviderError("该镜头没有 image_prompt，请先在分镜中填写图片提示词")

    provider = get_image_provider()
    width, height = size_for_aspect(project.aspect_ratio)
    data = provider.generate_image(ImageRequest(prompt=shot.image_prompt, width=width, height=height))

    file_path = storage_service.save_generated_file(
        project.id, shot.id, "images", ".png", data
    )
    asset = Asset(
        project_id=project.id,
        shot_id=shot.id,
        asset_type="scene_image",
        file_path=file_path,
        version=_next_version(db, shot.id, "scene_image"),
        status="ready",
        provider=provider.name,
        model=provider.model,
        prompt=shot.image_prompt,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def confirm_scene_image(db: Session, shot_id: int) -> Asset:
    latest = _latest_asset(db, shot_id, "scene_image")
    if latest is None:
        raise ProviderError("该镜头还没有场景图，请先生成")
    latest.status = "confirmed"
    db.commit()
    db.refresh(latest)
    return latest


def generate_shot_video(db: Session, shot: Shot, project: Project) -> Asset:
    """为镜头生成视频。前置条件：最新场景图已人工确认。"""
    image_asset = _latest_asset(db, shot.id, "scene_image")
    if image_asset is None:
        raise ProviderError("该镜头还没有场景图，请先生成并确认场景图")
    if image_asset.status != "confirmed":
        raise ProviderError("最新场景图尚未人工确认，请先在页面确认图片，再生成视频")
    if not shot.video_prompt or not shot.video_prompt.strip():
        raise ProviderError("该镜头没有 video_prompt，请先在分镜中填写视频提示词")

    image_abs = Path(settings.STORAGE_DIR) / image_asset.file_path
    if not image_abs.exists():
        raise ProviderError(f"场景图文件丢失：{image_asset.file_path}，请重新生成图片")

    provider = get_video_provider()
    width, height = size_for_aspect(project.aspect_ratio)
    data = provider.generate_video(
        VideoRequest(
            prompt=shot.video_prompt,
            image=image_abs.read_bytes(),
            image_ext=image_abs.suffix.lower(),
            duration=float(shot.duration or 4),
            width=width,
            height=height,
        )
    )

    file_path = storage_service.save_generated_file(
        project.id, shot.id, "videos", ".mp4", data
    )
    asset = Asset(
        project_id=project.id,
        shot_id=shot.id,
        asset_type="shot_video",
        file_path=file_path,
        version=_next_version(db, shot.id, "shot_video"),
        status="ready",
        provider=provider.name,
        model=provider.model,
        prompt=shot.video_prompt,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def confirm_shot_video(db: Session, shot_id: int) -> Asset:
    latest = _latest_asset(db, shot_id, "shot_video")
    if latest is None:
        raise ProviderError("该镜头还没有视频，请先生成")
    latest.status = "confirmed"
    db.commit()
    db.refresh(latest)
    return latest
