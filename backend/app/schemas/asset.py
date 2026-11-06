from datetime import datetime

from pydantic import BaseModel


class AssetRead(BaseModel):
    id: int
    project_id: int
    shot_id: int | None
    asset_type: str
    file_path: str
    version: int
    status: str
    provider: str
    model: str
    prompt: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
