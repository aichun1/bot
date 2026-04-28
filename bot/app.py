import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from config import cfg
from database.db import Database
from userbot.client import UserBotClient
from scheduler.tasks import Scheduler

from bot.middleware import AuthMiddleware
from bot.handlers import system, messaging, groups, ai_bridge, google_handler, schedule_handler, blacklist_handler

log = logging.getLogger("bot")

async def start_bot(userbot: UserBotClient, db: Database, scheduler: Scheduler):
    bot = Bot(
        token=cfg.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(AuthMiddleware(db, cfg.OWNER_ID, cfg.BOT_PASSWORD))

    # Context data
    dp["userbot"] = userbot
    dp["db"] = db
    dp["scheduler"] = scheduler

    # Handlerlarni ro'yxatdan o'tkazish
    for router in [
        system.router,
        messaging.router,
        groups.router,
        ai_bridge.router,
        google_handler.router,
        schedule_handler.router,
        blacklist_handler.router,
    ]:
        dp.include_router(router)

    log.info("🤖 Bot polling ishga tushdi...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
