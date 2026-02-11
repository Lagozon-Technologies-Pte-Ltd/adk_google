import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env ONLY in local/dev environments
if os.getenv("ENV", "dev") == "dev":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    load_dotenv(PROJECT_ROOT / ".env")

class Settings:
    GOOGLE_API_KEY: str | None = os.getenv("gemini_api_key")
    Weather_API: str | None = os.getenv("OPENWEATHER_API_KEY")
    # VERTEX_AI_LOCATION: str | None = os.getenv("VERTEX_AI_LOCATION")

    @classmethod
    def validate(cls):
        if not cls.GOOGLE_API_KEY and not cls.Weather_API_KEY:
            raise RuntimeError(
                "Missing AI credentials: set GOOGLE_API_KEY or Weather_API_KEY"
            )

settings = Settings()
settings.validate()
