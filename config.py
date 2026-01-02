import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional, List, Dict


class Settings(BaseSettings):
    # Bot va Admin
    BOT_TOKEN: SecretStr
    ADMIN_ID: int
    BOT_USERNAME: str
    ADMIN_USERNAME: str

    # Baza
    DB_URL: str

    # Majburiy obuna ma'lumotlari (FORMAT: ID|URL,ID|URL)
    REQ_CHANNELS_DATA: str

    # Maxfiy kino kanali
    MOVIE_CHANNEL_ID: int

    # AI (Ixtiyoriy)
    GEMINI_API_KEY: Optional[str] = None

    @property
    def mandatory_channels(self) -> List[Dict[str, str]]:
        """
        Xom satrni qulay listga aylantirib beradi.
        """
        channels = []
        if not self.REQ_CHANNELS_DATA:
            return channels

        for item in self.REQ_CHANNELS_DATA.split(","):
            if "|" in item:
                try:
                    channel_id, channel_url = item.strip().split("|")
                    channels.append({
                        "id": int(channel_id),
                        "url": channel_url
                    })
                except ValueError:
                    logging.error(f"Kanal formati noto'g'ri: {item}")
        return channels

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


# Obyektni yaratish
try:
    config = Settings()
except Exception as e:
    print(f"❌ .env faylini yuklashda xatolik: {e}")
    exit(1)