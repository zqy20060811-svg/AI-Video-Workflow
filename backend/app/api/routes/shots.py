from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Project, Shot
from app.schemas.shot import ShotCreate, ShotRead, ShotReorderRequest, ShotUpdate

router = APIRouter(tags=["shots"])


def _get_shot_or_404(shot_id: int, db: Session) -> Shot:
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@router.get("/api/projects/{project_id}/shots", response_model=list[ShotRead])
def list_shots(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db.query(Shot).filter(Shot.project_id == project_id).order_by(Shot.shot_no).all()


@router.post("/api/projects/{project_id}/shots", response_model=ShotRead)
def create_shot(project_id: int, payload: ShotCreate, db: Session = Depends(get_db)):
    """手动新增一个分镜（排在末尾）。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    max_no = db.query(Shot).filter(Shot.project_id == project_id).count()
    shot = Shot(project_id=project_id, shot_no=max_no + 1, status="draft", **payload.model_dump())
    db.add(shot)
    db.commit()
    db.refresh(shot)
    return shot


@router.get("/api/shots/{shot_id}", response_model=ShotRead)
def get_shot(shot_id: int, db: Session = Depends(get_db)):
    return _get_shot_or_404(shot_id, db)


@router.put("/api/shots/{shot_id}", response_model=ShotRead)
def update_shot(shot_id: int, payload: ShotUpdate, db: Session = Depends(get_db)):
    """修改分镜（含 image_prompt / video_prompt / shot_no 调整顺序）。"""
    shot = _get_shot_or_404(shot_id, db)
    data = payload.model_dump(exclude_unset=True)

    new_no = data.pop("shot_no", None)
    for field, value in data.items():
        setattr(shot, field, value)

    if new_no is not None and new_no != shot.shot_no:
        # 与目标位置的镜头交换编号，简单实现顺序调整
        target = (
            db.query(Shot)
            .filter(Shot.project_id == shot.project_id, Shot.shot_no == new_no, Shot.id != shot.id)
            .first()
        )
        old_no = shot.shot_no
        shot.shot_no = new_no
        if target:
            target.shot_no = old_no

    # 个人工作流：已确认分镜修改后保持确认状态，不回退审核
    db.commit()
    db.refresh(shot)
    return shot


@router.delete("/api/shots/{shot_id}")
def delete_shot(shot_id: int, db: Session = Depends(get_db)):
    shot = _get_shot_or_404(shot_id, db)
    project_id = shot.project_id
    deleted_no = shot.shot_no
    db.delete(shot)
    # 后续镜头编号前移，保持连续
    remain = (
        db.query(Shot)
        .filter(Shot.project_id == project_id, Shot.shot_no > deleted_no)
        .order_by(Shot.shot_no)
        .all()
    )
    for s in remain:
        s.shot_no -= 1
    db.commit()
    return {"message": "分镜已删除"}


@router.post("/api/projects/{project_id}/shots/reorder")
def reorder_shots(project_id: int, payload: ShotReorderRequest, db: Session = Depends(get_db)):
    """批量调整分镜顺序：按传入的 shots 列表顺序重新编号。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    shots = {s.id: s for s in db.query(Shot).filter(Shot.project_id == project_id).all()}
    listed = []
    for item in payload.shots:
        shot = shots.get(item.id)
        if shot is None:
            raise HTTPException(status_code=400, detail=f"分镜 {item.id} 不存在")
        listed.append(shot)
    # 未在请求中的镜头按原相对顺序排在后面
    listed_ids = {s.id for s in listed}
    unlisted = sorted(
        (s for s in shots.values() if s.id not in listed_ids), key=lambda s: s.shot_no
    )
    # 先赋临时编号避免位置冲突，再落最终编号
    for idx, shot in enumerate(listed + unlisted):
        shot.shot_no = 10000 + idx
    db.flush()
    for idx, shot in enumerate(listed + unlisted, start=1):
        shot.shot_no = idx
    db.commit()
    return {"message": "顺序已更新"}
