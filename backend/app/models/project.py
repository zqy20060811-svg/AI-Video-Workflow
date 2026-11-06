from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    story: Mapped[str | None] = mapped_column(Text, nullable=True)
    # AI 故事结构化分析结果（title/summary/characters/main_conflict/story_structure/key_events）
    story_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="9:16", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    characters: Mapped[list["Character"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    shots: Mapped[list["Shot"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
    assets: Mapped[list["Asset"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )
