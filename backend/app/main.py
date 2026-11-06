from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import characters, projects, shots
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


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "AI Video Workflow backend is running",
    }
