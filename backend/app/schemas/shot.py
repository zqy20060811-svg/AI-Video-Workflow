from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShotBase(BaseModel):
    scene: str | None = None
    location: str | None = None
    time: str | None = None
    characters: list[str] | None = None
    action: str | None = None
    camera: str | None = None
    visual_description: str | None = None
    dialogue: str | None = None
    duration: float | None = None
    image_prompt: str | None = None
    video_prompt: str | None = None


class ShotCreate(ShotBase):
    pass


class ShotUpdate(ShotBase):
    # shot_no 单独提供，用于调整顺序
    shot_no: int | None = None
    status: str | None = None


class ShotRead(ShotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    shot_no: int
    status: str
    created_at: datetime
    updated_at: datetime


class ShotReorderItem(BaseModel):
    id: int
    shot_no: int


class ShotReorderRequest(BaseModel):
    shots: list[ShotReorderItem] = Field(min_length=1)
