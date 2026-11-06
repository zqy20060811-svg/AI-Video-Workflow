from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Project, Shot
from app.schemas.shot import ShotRead

router = APIRouter(prefix="/api/projects/{project_id}/shots", tags=["shots"])


@router.get("", response_model=list[ShotRead])
def list_shots(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Shot).filter(Shot.project_id == project_id).order_by(Shot.shot_no).all()
