from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，全部来自环境变量 / .env 文件。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Video Workflow"
    APP_ENV: str = "development"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ai_video_workflow"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_DIR: str = "./storage"

    # LLM 配置（OpenAI 兼容 API：OpenAI / DeepSeek / Ollama / 其他兼容服务）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7


settings = Settings()
