from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Project, Shot
from app.schemas.shot import ShotRead
from app.workflow.graph import storyboard_graph

router = APIRouter(prefix="/api/projects/{project_id}/storyboard", tags=["storyboard"])


def _build_characters_info(project: Project) -> str:
    if not project.characters:
        return "（项目尚未添加角色）"
    lines = []
    for c in project.characters:
        has_images = "已有三视图素材" if c.front_image else "暂无三视图素材"
        desc = f"，描述：{c.description}" if c.description else ""
        lines.append(f"- {c.name}{desc}（{has_images}）")
    return "\n".join(lines)


@router.post("/story/analyze")
def analyze_story(project_id: int, db: Session = Depends(get_db)):
    """AI 故事结构化分析（独立调用，保存分析结果，不生成分镜）。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.story or not project.story.strip():
        raise HTTPException(status_code=400, detail="请先填写故事梗概")

    result = storyboard_graph.invoke(
        {
            "project_id": project.id,
            "story": project.story,
            "characters_info": _build_characters_info(project),
        },
        config={"recursion_limit": 10},
    )
    if result.get("error"):
        raise HTTPException(status_code=502, detail="生成失败，请重试")

    project.story_analysis = result["story_analysis"]
    db.commit()
    return {"story_analysis": project.story_analysis}


@router.post("/generate", response_model=list[ShotRead])
def generate_storyboard(project_id: int, db: Session = Depends(get_db)):
    """AI 生成分镜：故事分析 → 分镜生成，结果直接入库（draft 状态）。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status == "storyboard_confirmed":
        raise HTTPException(status_code=400, detail="分镜已确认，如需重新生成请先修改分镜")
    if not project.story or not project.story.strip():
        raise HTTPException(status_code=400, detail="请先填写故事梗概")

    # 标记分析中，让前端可以区分等待阶段
    project.status = "story_analyzing"
    db.commit()

    result = storyboard_graph.invoke(
        {
            "project_id": project.id,
            "story": project.story,
            "characters_info": _build_characters_info(project),
        },
        config={"recursion_limit": 10},
    )
    if result.get("error"):
        db.rollback()
        raise HTTPException(status_code=502, detail="生成失败，请重试")

    # 保存故事分析
    project.story_analysis = result["story_analysis"]

    # 覆盖旧的草稿分镜
    db.query(Shot).filter(Shot.project_id == project_id, Shot.status == "draft").delete()
    existing = db.query(Shot).filter(Shot.project_id == project_id).count()
    shots = []
    for s in result["shots"]:
        s["shot_no"] += existing
        shots.append(Shot(project_id=project_id, status="draft", **s))
    db.add_all(shots)

    project.status = "storyboard_generated"
    db.commit()
    db.refresh(project)
    return sorted(project.shots, key=lambda x: x.shot_no)


@router.post("/confirm")
def confirm_storyboard(project_id: int, db: Session = Depends(get_db)):
    """人工确认全部分镜。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    if not shots:
        raise HTTPException(status_code=400, detail="暂无分镜可确认，请先生成分镜")

    for shot in shots:
        shot.status = "confirmed"
    project.status = "storyboard_confirmed"
    db.commit()
    return {"message": "分镜已确认", "shot_count": len(shots)}
