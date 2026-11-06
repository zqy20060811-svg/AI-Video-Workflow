from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import characters, media, projects, shots, storyboard, system
from app.core.config import settings
from app.core.database import Base, engine
from app.models import Asset, Character, Project, Shot  # noqa: F401 确保模型注册
from app.services import storage_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化本地存储目录 + 建表（第一阶段不使用 Alembic）
    storage_service.get_temp_dir()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5180", "http://127.0.0.1:5180"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(characters.router)
app.include_router(shots.router)
app.include_router(storyboard.router)
app.include_router(media.router)
app.include_router(system.router)

# 本地生成产物（场景图 / 视频）通过 /storage/ 直接访问
storage_abs = Path(settings.STORAGE_DIR).resolve()
storage_abs.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_abs)), name="storage")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "AI Video Workflow backend is running",
    }
