from pathlib import Path

import aiofiles  # type: ignore[import-not-found]

from app.core.config import settings

# 支持的图片扩展名
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_project_dir(project_id: int) -> Path:
    """返回项目存储根目录：storage/projects/{project_id}/"""
    base = Path(settings.STORAGE_DIR) / "projects" / str(project_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_character_dir(project_id: int) -> Path:
    """返回角色图片目录：storage/projects/{project_id}/characters/"""
    base = get_project_dir(project_id) / "characters"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_temp_dir() -> Path:
    """返回临时目录：storage/temp/"""
    base = Path(settings.STORAGE_DIR) / "temp"
    base.mkdir(parents=True, exist_ok=True)
    return base


def validate_image_filename(filename: str) -> bool:
    """校验上传文件扩展名是否为允许的图片格式。"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


async def save_upload_file(project_id: int, subdir: str, filename: str, content: bytes) -> str:
    """
    保存上传文件到 storage/projects/{project_id}/{subdir}/uuid.ext，
    返回相对路径（存入数据库的 file_path）。
    """
    directory = get_project_dir(project_id) / subdir
    directory.mkdir(parents=True, exist_ok=True)

    import uuid

    ext = Path(filename).suffix.lower()
    saved_name = f"{uuid.uuid4().hex}{ext}"
    target = directory / saved_name

    async with aiofiles.open(target, "wb") as f:
        await f.write(content)

    # 返回相对路径，例如 projects/1/characters/xxx.png
    return str(Path("projects") / str(project_id) / subdir / saved_name)
