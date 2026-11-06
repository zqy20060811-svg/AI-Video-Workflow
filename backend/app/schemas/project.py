from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    story: str | None = None
    aspect_ratio: str = "9:16"


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    story: str | None
    status: str
    aspect_ratio: str
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    characters: list["CharacterRead"] = []
    shots: list["ShotRead"] = []
    shot_count: int = 0


from app.schemas.character import CharacterRead  # noqa: E402
from app.schemas.shot import ShotRead  # noqa: E402

ProjectDetail.model_rebuild()
