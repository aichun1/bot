import os
import tempfile
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from userbot.client import UserBotClient
from database.db import Database

router = Router()

def parse_pipe(text: str, cmd: str):
    """'/cmd chat | matn' ni ajratadi"""
    body = text[len(cmd):].strip()
    if "|" in body:
        parts = body.split("|", 1)
        return parts[0].strip(), parts[1].strip()
    return body.strip(), ""

@router.message(Command("send"))
async def cmd_send(message: Message, userbot: UserBotClient, db: Database):
    chat, text = parse_pipe(message.text, "/send")
    if not chat or not text:
        await message.answer("❌ Format: `/send @chat | matn`")
        return

    if await db.is_blacklisted(chat):
        await message.answer(f"🚫 {chat} qora ro'yxatda!")
        return

    try:
        await userbot.send_message(chat, text)
        await message.answer(f"✅ Xabar yuborildi → {chat}")
    except Exception as e:
        await message.answer(f"❌ Xato: `{e}`")

@router.message(Command("forward"))
async def cmd_forward(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 4:
        await message.answer("❌ Format: `/forward @from @to msg_id`")
        return
    _, from_chat, to_chat, msg_id = parts[0], parts[1], parts[2], parts[3]
    try:
        await userbot.forward_message(from_chat, to_chat, int(msg_id))
        await message.answer(f"✅ Forward: {from_chat} → {to_chat}")
    except Exception as e:
        await message.answer(f"❌ Xato: `{e}`")

@router.message(Command("delete"))
async def cmd_delete(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Format: `/delete @chat msg_id`")
        return
    _, chat, msg_id = parts[0], parts[1], parts[2]
    try:
        await userbot.delete_message(chat, int(msg_id))
        await message.answer(f"✅ Xabar o'chirildi (ID: {msg_id})")
    except Exception as e:
        await message.answer(f"❌ Xato: `{e}`")

@router.message(Command("pin"))
async def cmd_pin(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Format: `/pin @chat msg_id`")
        return
    _, chat, msg_id = parts[0], parts[1], parts[2]
    try:
        await userbot.pin_message(chat, int(msg_id))
        await message.answer(f"✅ Xabar pin qilindi")
    except Exception as e:
        await message.answer(f"❌ Xato: `{e}`")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, userbot: UserBotClient, db: Database):
    chat_str, text = parse_pipe(message.text, "/broadcast")
    if not chat_str or not text:
        await message.answer("❌ Format: `/broadcast @chat1,@chat2 | matn`")
        return

    chats = [c.strip() for c in chat_str.split(",")]
    # Blacklist filtratsiya
    filtered = []
    for c in chats:
        if await db.is_blacklisted(c):
            await message.answer(f"⚠️ {c} qora ro'yxatda, o'tkazildi.")
        else:
            filtered.append(c)

    if not filtered:
        await message.answer("❌ Barcha chatlar qora ro'yxatda!")
        return

    wait_msg = await message.answer(f"📤 {len(filtered)} ta chatga yuborilmoqda...")
    result = await userbot.broadcast(filtered, text)
    await wait_msg.edit_text(
        f"✅ **Broadcast tugadi:**\n"
        f"✅ Muvaffaqiyat: {result['ok']}\n"
        f"❌ Xato: {result['fail']}"
    )

@router.message(Command("download"))
async def cmd_download(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Format: `/download @chat msg_id`")
        return
    _, chat, msg_id = parts[0], parts[1], parts[2]
    wait = await message.answer("⬇️ Yuklab olinmoqda...")
    try:
        os.makedirs("downloads", exist_ok=True)
        path = await userbot.download_media(chat, int(msg_id))
        if path:
            await message.answer_document(path)
            await wait.delete()
        else:
            await wait.edit_text("⚠️ Bu xabarda media yo'q.")
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")
