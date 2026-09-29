"""Environment-driven application settings."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    api_base: str | None = os.getenv("OPENAI_API_BASE") or None
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    port: int = int(os.getenv("PORT", "7860"))
    database_url: str = os.getenv(
        "CHINOOK_SQL_URL",
        "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql",
    )


settings = Settings()

