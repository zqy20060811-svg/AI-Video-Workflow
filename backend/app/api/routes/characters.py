from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Character, Project
from app.schemas.character import CharacterRead
from app.services import storage_service

router = APIRouter(prefix="/api/projects/{project_id}/characters", tags=["characters"])


@router.post("", response_model=CharacterRead)
async def create_character(
    project_id: int,
    name: str = Form(...),
    description: str | None = Form(None),
    front_image: UploadFile = File(...),
    side_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # 校验并保存三张角色图
    paths: dict[str, str] = {}
    for field, upload in (
        ("front_image", front_image),
        ("side_image", side_image),
        ("back_image", back_image),
    ):
        if upload.filename is None or not storage_service.validate_image_filename(upload.filename):
            raise HTTPException(status_code=400, detail=f"{field} 不是支持的图片格式")
        content = await upload.read()
        paths[field] = await storage_service.save_upload_file(
            project_id, "characters", upload.filename, content
        )

    character = Character(
        project_id=project_id,
        name=name,
        description=description,
        **paths,
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("", response_model=list[CharacterRead])
def list_characters(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Character).filter(Character.project_id == project_id).all()
