import asyncio
import logging
from bot.app import start_bot
from userbot.client import UserBotClient
from scheduler.tasks import Scheduler
from database.db import Database
from config import cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("main")

async def main():
    log.info("🚀 SuperBot ishga tushmoqda...")
    db = Database()
    await db.init()

    # Gemini API sozlash
    if cfg.GEMINI_API_KEY:
        from google_apis.gemini_api import gemini
        gemini.setup(cfg.GEMINI_API_KEY)
        log.info("✅ Gemini API ulandi.")
    else:
        log.warning("⚠️ GEMINI_API_KEY yo'q — AI funksiyalar ishlamaydi.")

    userbot = UserBotClient(db)
    await userbot.start()

    scheduler = Scheduler(userbot, db)
    scheduler.start()

    await start_bot(userbot, db, scheduler)

if __name__ == "__main__":
    asyncio.run(main())
