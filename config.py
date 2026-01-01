from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMIN_ID: int
    DB_URL: str
    CHANNEL_ID: int
    CHANNEL_URL: str
    GEMINI_API_KEY: Optional[str] = "no_key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

config = Settings()