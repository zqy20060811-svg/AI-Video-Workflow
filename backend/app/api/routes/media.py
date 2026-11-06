"""镜头图片/视频生成与人工确认 API。"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Asset, Project, Shot
from app.schemas.asset import AssetRead
from app.services import generation_service
from app.services.providers.base import ProviderError

router = APIRouter(tags=["media"])

ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov"}


def _get_shot_or_404(shot_id: int, db: Session) -> tuple[Shot, Project]:
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    project = db.query(Project).filter(Project.id == shot.project_id).first()
    return shot, project


def _handle_provider_error(exc: ProviderError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/api/shots/{shot_id}/assets", response_model=list[AssetRead])
def list_shot_assets(shot_id: int, db: Session = Depends(get_db)):
    shot, _ = _get_shot_or_404(shot_id, db)
    return (
        db.query(Asset)
        .filter(Asset.shot_id == shot.id)
        .order_by(Asset.id.desc())
        .all()
    )


@router.post("/api/shots/{shot_id}/images/generate", response_model=AssetRead)
def generate_image(shot_id: int, db: Session = Depends(get_db)):
    """生成场景图（调用 .env 配置的 ImageProvider）。"""
    shot, project = _get_shot_or_404(shot_id, db)
    try:
        return generation_service.generate_scene_image(db, shot, project)
    except ProviderError as e:
        raise _handle_provider_error(e)


@router.post("/api/shots/{shot_id}/images/confirm", response_model=AssetRead)
def confirm_image(shot_id: int, db: Session = Depends(get_db)):
    """人工确认最新的场景图。"""
    _get_shot_or_404(shot_id, db)
    try:
        return generation_service.confirm_scene_image(db, shot_id)
    except ProviderError as e:
        raise _handle_provider_error(e)


@router.post("/api/shots/{shot_id}/videos/generate", response_model=AssetRead)
def generate_video(shot_id: int, db: Session = Depends(get_db)):
    """生成视频（Image-to-Video，要求最新场景图已确认）。"""
    shot, project = _get_shot_or_404(shot_id, db)
    try:
        return generation_service.generate_shot_video(db, shot, project)
    except ProviderError as e:
        raise _handle_provider_error(e)


@router.post("/api/shots/{shot_id}/videos/confirm", response_model=AssetRead)
def confirm_video(shot_id: int, db: Session = Depends(get_db)):
    """人工确认最新的视频，确认后该镜头视为完成。"""
    _get_shot_or_404(shot_id, db)
    try:
        return generation_service.confirm_shot_video(db, shot_id)
    except ProviderError as e:
        raise _handle_provider_error(e)


@router.post("/api/shots/{shot_id}/images/upload", response_model=AssetRead)
async def upload_image(shot_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传外部工具生成的场景图（零成本人工闭环，provider=manual）。"""
    shot, project = _get_shot_or_404(shot_id, db)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="仅支持 png / jpg / jpeg / webp 图片")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    return generation_service.register_manual_asset(
        db, shot, project, "scene_image", ext, data, prompt=shot.image_prompt
    )


@router.post("/api/shots/{shot_id}/videos/upload", response_model=AssetRead)
async def upload_video(shot_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传外部工具生成的视频（零成本人工闭环，provider=manual）。"""
    shot, project = _get_shot_or_404(shot_id, db)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(status_code=400, detail="仅支持 mp4 / webm / mov 视频")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件为空")
    return generation_service.register_manual_asset(
        db, shot, project, "shot_video", ext, data, prompt=shot.video_prompt
    )
