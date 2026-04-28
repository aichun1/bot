import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
    BOT_PASSWORD: str = os.getenv("BOT_PASSWORD", "supersecret123")

    # Telegram Userbot (my.telegram.org dan)
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    PHONE: str = os.getenv("PHONE", "")
    SESSION_STRING: str = os.getenv("SESSION_STRING", "")

    # Google APIs
    GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
    GOOGLE_TOKEN_JSON: str = os.getenv("GOOGLE_TOKEN_JSON", "")
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    GMAIL_USER: str = os.getenv("GMAIL_USER", "")

    # AI Telegram Botlari (username)
    WHISPER_BOT: str = os.getenv("WHISPER_BOT", "@whisperrobot")
    AI_BOT: str = os.getenv("AI_BOT", "@ChatGPTelegramBot")

    # Railway
    PORT: int = int(os.getenv("PORT", "8080"))
    RAILWAY_ENV: bool = os.getenv("RAILWAY_ENVIRONMENT") is not None

cfg = Config()
