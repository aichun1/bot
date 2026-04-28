import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.db import Database
from userbot.client import UserBotClient
from config import cfg

log = logging.getLogger("scheduler")

class Scheduler:
    def __init__(self, userbot: UserBotClient, db: Database):
        self.userbot = userbot
        self.db = db
        self._scheduler = AsyncIOScheduler()

    def start(self):
        self._scheduler.add_job(
            self._check_scheduled_messages,
            trigger=IntervalTrigger(minutes=1),
            id="scheduled_msgs",
            replace_existing=True
        )
        self._scheduler.add_job(
            self._send_morning_digest,
            trigger="cron",
            hour=8,
            minute=0,
            id="morning_digest",
            replace_existing=True
        )
        self._scheduler.start()
        log.info("✅ Scheduler ishga tushdi.")

    async def _check_scheduled_messages(self):
        """Har daqiqada rejalashtirilgan xabarlarni tekshiradi"""
        try:
            pending = await self.db.schedule_pending()
            for msg in pending:
                try:
                    await self.userbot.send_message(msg["chat_id"], msg["message"])
                    await self.db.schedule_mark_done(msg["id"])
                    log.info(f"✅ Rejalashtirilgan xabar yuborildi: {msg['id']} → {msg['chat_id']}")
                except Exception as e:
                    log.error(f"❌ Xabar yuborishda xato (ID:{msg['id']}): {e}")
        except Exception as e:
            log.error(f"Scheduler tekshiruv xatosi: {e}")

    async def _send_morning_digest(self):
        """Har kuni ertalab 08:00 da xabar yuboradi"""
        try:
            scheduled = await self.db.schedule_list()
            monitors = await self.db.monitor_list()

            if not scheduled and not monitors:
                return

            lines = ["☀️ **Kunlik hisobot:**\n"]
            if scheduled:
                lines.append(f"⏰ Bugungi rejalashtirilgan xabarlar: {len(scheduled)}")
                for s in scheduled[:5]:
                    lines.append(f"  • {s['send_at'][11:16]} → {s['chat_id']}")
            if monitors:
                lines.append(f"\n👁 Faol monitorlar: {len(monitors)}")

            await self.userbot.send_message(cfg.OWNER_ID, "\n".join(lines))
        except Exception as e:
            log.error(f"Morning digest xatosi: {e}")

    def stop(self):
        self._scheduler.shutdown()
