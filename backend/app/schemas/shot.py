from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    shot_no: int
    duration: float | None
    scene: str | None
    characters: str | None
    action: str | None
    camera: str | None
    dialogue: str | None
    image_prompt: str | None
    video_prompt: str | None
    status: str
    created_at: datetime
    updated_at: datetime
