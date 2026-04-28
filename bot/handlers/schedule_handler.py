from datetime import datetime, timedelta
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router()

@router.message(Command("schedule"))
async def cmd_schedule(message: Message, db: Database):
    """Format: /schedule HH:MM @chat | matn"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Format: `/schedule HH:MM @chat | matn`\nMisol: `/schedule 18:30 @guruhim | Salom!`")
        return

    body = parts[1].strip()
    tokens = body.split(maxsplit=1)
    if len(tokens) < 2 or "|" not in tokens[1]:
        await message.answer("❌ Format: `/schedule HH:MM @chat | matn`")
        return

    time_str = tokens[0]
    rest = tokens[1]
    chat, text = rest.split("|", 1)
    chat = chat.strip()
    text = text.strip()

    try:
        hour, minute = map(int, time_str.split(":"))
    except:
        await message.answer("❌ Vaqt formati noto'g'ri. Misol: `18:30`")
        return

    now = datetime.now()
    send_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if send_at <= now:
        send_at += timedelta(days=1)

    msg_id = await db.schedule_add(chat, text, send_at.isoformat())
    await message.answer(
        f"✅ **Rejalashtirildi:**\n"
        f"🕐 Vaqt: {send_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📍 Chat: {chat}\n"
        f"💬 Matn: {text[:100]}\n"
        f"ID: `{msg_id}`"
    )

@router.message(Command("schedule_list"))
async def cmd_schedule_list(message: Message, db: Database):
    items = await db.schedule_list()
    if not items:
        await message.answer("📅 Navbatdagi xabarlar yo'q.")
        return
    lines = ["📅 **Navbatdagi xabarlar:**\n"]
    for s in items:
        lines.append(
            f"ID:{s['id']} | {s['send_at'][:16]}\n"
            f"  → {s['chat_id']}: {s['message'][:60]}\n"
        )
    await message.answer("\n".join(lines))

@router.message(Command("schedule_cancel"))
async def cmd_schedule_cancel(message: Message, db: Database):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: `/schedule_cancel ID`")
        return
    await db.schedule_mark_done(int(parts[1]))
    await message.answer(f"✅ Xabar ID:{parts[1]} bekor qilindi.")
