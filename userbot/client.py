import asyncio
import logging
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from config import cfg
from database.db import Database

log = logging.getLogger("userbot")

class UserBotClient:
    def __init__(self, db: Database):
        self.db = db
        self._owner_notify_id = cfg.OWNER_ID  # xabar borishi uchun
        
        session = StringSession(cfg.SESSION_STRING) if cfg.SESSION_STRING else "superbot_session"
        self.client = TelegramClient(
            session,
            cfg.API_ID,
            cfg.API_HASH,
        )

    async def start(self):
        if cfg.SESSION_STRING:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                log.error("SESSION_STRING noto'g'ri yoki eskirgan!")
        else:
            # Birinchi marta: telefon orqali kirish (local dev uchun)
            await self.client.start(phone=cfg.PHONE)
        
        me = await self.client.get_me()
        log.info(f"✅ Userbot ulandi: {me.first_name} (@{me.username})")
        self._setup_handlers()

    def _setup_handlers(self):
        """Monitoring va autoreply uchun event handlers"""

        @self.client.on(events.NewMessage(incoming=True))
        async def on_message(event):
            try:
                await self._handle_incoming(event)
            except Exception as e:
                log.error(f"Handler xato: {e}")

    async def _handle_incoming(self, event):
        # Autoreply
        ar = await self.db.get_autoreply()
        if ar and ar["active"] and event.is_private:
            sender = await event.get_sender()
            if sender and not sender.bot:
                await asyncio.sleep(1)
                await event.reply(ar["reply_text"])

        # Monitor
        monitors = await self.db.monitor_list()
        for m in monitors:
            if event.text and m["keyword"].lower() in event.text.lower():
                chat = await event.get_chat()
                chat_name = getattr(chat, "title", None) or getattr(chat, "username", "??")
                sender = await event.get_sender()
                sender_name = getattr(sender, "first_name", "??")
                notify_text = (
                    f"🔔 **Monitor:** `{m['keyword']}`\n"
                    f"📍 Chat: {chat_name}\n"
                    f"👤 Yuboruvchi: {sender_name}\n"
                    f"💬 Xabar: {event.text[:300]}"
                )
                await self.client.send_message(cfg.OWNER_ID, notify_text)

    # ─────────────────────── ACTIONS ───────────────────────

    async def search_peer(self, name: str) -> str | None:
        """Ism yoki username bo'yicha peer (entity) qidiradi va uning username yoki ID sini qaytaradi."""
        try:
            entity = await self.client.get_entity(name)
            return getattr(entity, 'username', None) or str(entity.id)
        except ValueError:
            pass
            
        async for dialog in self.client.iter_dialogs():
            title = dialog.name or ""
            if name.lower() in title.lower():
                entity = dialog.entity
                return getattr(entity, 'username', None) or str(entity.id)
        return None

    async def execute_telethon_code(self, code: str) -> str:
        """Agent tomonidan berilgan Telethon Python kodini dinamik ishga tushiradi."""
        env = {
            "client": self.client,
            "asyncio": asyncio,
            "os": os,
            "log": log,
            "result": None,
            "functions": __import__('telethon.tl.functions', fromlist=[''])
        }
        
        wrapper = f"async def _dynamic_run():\n    global result\n"
        for line in code.split('\n'):
            wrapper += f"    {line}\n"
            
        try:
            exec(wrapper, env)
            await env["_dynamic_run"]()
            return str(env.get("result", "Muvaffaqiyatli bajarildi."))
        except Exception as e:
            log.error(f"Dinamik kod xatosi: {e}")
            return f"Xatolik yuz berdi: {e}"

    async def send_message(self, chat, text: str):
        entity = await self.client.get_entity(chat)
        await self.client.send_message(entity, text)
        return True

    async def forward_message(self, from_chat, to_chat, msg_id: int):
        from_entity = await self.client.get_entity(from_chat)
        to_entity = await self.client.get_entity(to_chat)
        await self.client.forward_messages(to_entity, msg_id, from_entity)
        return True

    async def delete_message(self, chat, msg_id: int, revoke: bool = True):
        entity = await self.client.get_entity(chat)
        await self.client.delete_messages(entity, [msg_id], revoke=revoke)
        return True

    async def pin_message(self, chat, msg_id: int, silent: bool = True):
        from telethon.tl.functions.messages import UpdatePinnedMessageRequest
        entity = await self.client.get_entity(chat)
        await self.client(UpdatePinnedMessageRequest(peer=entity, id=msg_id, silent=silent))
        return True

    async def mute_chat(self, chat, seconds: int):
        from telethon.tl.functions.account import UpdateNotifySettingsRequest
        from telethon.tl.types import InputPeerNotifySettings, InputNotifyPeer
        entity = await self.client.get_entity(chat)
        mute_until = int(asyncio.get_event_loop().time()) + seconds
        await self.client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(peer=entity),
            settings=InputPeerNotifySettings(mute_until=mute_until)
        ))
        return True

    async def get_members(self, chat, limit: int = 50) -> list:
        entity = await self.client.get_entity(chat)
        participants = await self.client(GetParticipantsRequest(
            entity, ChannelParticipantsSearch(""), 0, limit, 0
        ))
        result = []
        for p in participants.users:
            result.append({
                "id": p.id,
                "name": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                "username": f"@{p.username}" if p.username else "—"
            })
        return result

    async def get_history(self, chat, limit: int = 20) -> list:
        entity = await self.client.get_entity(chat)
        messages = []
        async for msg in self.client.iter_messages(entity, limit=limit):
            if msg.text:
                sender_name = "??"
                try:
                    sender = await msg.get_sender()
                    sender_name = getattr(sender, "first_name", "??")
                except:
                    pass
                messages.append({
                    "id": msg.id,
                    "sender": sender_name,
                    "text": msg.text[:200],
                    "date": msg.date.strftime("%d.%m %H:%M")
                })
        return messages

    async def search_messages(self, chat, keyword: str, limit: int = 20) -> list:
        entity = await self.client.get_entity(chat)
        results = []
        async for msg in self.client.iter_messages(entity, search=keyword, limit=limit):
            if msg.text:
                results.append({
                    "id": msg.id,
                    "text": msg.text[:300],
                    "date": msg.date.strftime("%d.%m %H:%M")
                })
        return results

    async def download_media(self, chat, msg_id: int) -> str | None:
        entity = await self.client.get_entity(chat)
        message = await self.client.get_messages(entity, ids=msg_id)
        if message and message.media:
            path = await self.client.download_media(message, file="downloads/")
            return path
        return None

    async def broadcast(self, chats: list, text: str, delay: float = 2.0) -> dict:
        ok, fail = 0, 0
        for chat in chats:
            try:
                await self.send_message(chat, text)
                ok += 1
            except Exception as e:
                log.error(f"Broadcast xato ({chat}): {e}")
                fail += 1
            await asyncio.sleep(delay)
        return {"ok": ok, "fail": fail}

    # ─── AI Bridge ───────────────────────────────────────────

    async def ask_ai_bot(self, bot_username: str, question: str, timeout: int = 30) -> str:
        """Telegram AI bot ga savol yuboradi, javob kutadi"""
        bot_entity = await self.client.get_entity(bot_username)
        await self.client.send_message(bot_entity, question)
        
        await asyncio.sleep(timeout)
        
        async for msg in self.client.iter_messages(bot_entity, limit=5):
            if msg.text and msg.out is False:
                return msg.text
        return "⚠️ AI bot javob bermadi."

    async def send_audio_to_whisper(self, audio_path: str, bot_username: str, timeout: int = 60) -> str:
        """Audio faylni Whisper botga yuboradi, matn qaytaradi"""
        bot_entity = await self.client.get_entity(bot_username)
        await self.client.send_file(bot_entity, audio_path)
        
        await asyncio.sleep(timeout)
        
        async for msg in self.client.iter_messages(bot_entity, limit=5):
            if msg.text and msg.out is False:
                return msg.text
        return "⚠️ Whisper bot javob bermadi."

    async def stop(self):
        await self.client.disconnect()
        log.info("Userbot to'xtatildi.")
