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

    # 图片生成配置：none（未配置）| comfyui | pollinations | openai_compatible
    IMAGE_PROVIDER: str = "none"
    IMAGE_MODEL: str = ""
    # openai_compatible 图片 API（硅基流动 / OpenAI / 其他兼容服务）
    IMAGE_BASE_URL: str = "https://api.siliconflow.cn/v1"
    IMAGE_API_KEY: str = ""

    # 视频生成配置：none（未配置）| comfyui
    VIDEO_PROVIDER: str = "none"
    VIDEO_MODEL: str = ""
    VIDEO_CLIP_MODEL: str = ""
    VIDEO_VAE_MODEL: str = ""
    VIDEO_FPS: int = 24

    # ComfyUI 连接地址（图片/视频 Provider 共用）
    COMFYUI_URL: str = "http://127.0.0.1:8188"

    # 生成任务轮询间隔与超时（秒）
    GEN_POLL_INTERVAL: float = 2.0
    GEN_TIMEOUT: float = 600.0


settings = Settings()
