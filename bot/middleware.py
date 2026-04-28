import logging
from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import Message
from database.db import Database

log = logging.getLogger("middleware")

class AuthMiddleware(BaseMiddleware):
    def __init__(self, db: Database, owner_id: int, password: str):
        self.db = db
        self.owner_id = owner_id
        self.password = password

    async def __call__(
        self,
        handler: Callable[[Message, dict], Awaitable[Any]],
        event: Message,
        data: dict
    ) -> Any:
        user = event.from_user
        if not user:
            return

        # Owner har doim o'tadi
        if user.id == self.owner_id:
            await self.db.set_auth(user.id, user.username, True)
            await self.db.update_last_seen(user.id)
            return await handler(event, data)

        # /start va /pass buyruqlari ochiq
        text = event.text or ""
        if text.startswith("/start") or text.startswith("/pass"):
            return await handler(event, data)

        # Autentifikatsiya tekshiruvi
        is_authed = await self.db.is_authed(user.id)
        if not is_authed:
            await event.answer(
                "🔐 **Kirish uchun parol kerak!**\n\n"
                "Buyruq: `/pass <parol>`\n\n"
                "Misol: `/pass mysecret123`"
            )
            return

        await self.db.update_last_seen(user.id)
        return await handler(event, data)
