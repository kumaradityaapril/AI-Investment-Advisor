from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "AI Investment Advisor"
    app_env: str = "development"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    upload_dir: str = "uploads"
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, gt=0)

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", ".env"),
        extra="ignore",
    )


settings = Settings()