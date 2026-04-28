from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from userbot.client import UserBotClient
from database.db import Database

router = Router()

DURATION_MAP = {"m": 60, "h": 3600, "d": 86400}

def parse_duration(s: str) -> int:
    """'30m', '2h', '1d' → sekundlar"""
    try:
        unit = s[-1].lower()
        value = int(s[:-1])
        return value * DURATION_MAP.get(unit, 60)
    except:
        return 3600  # default 1 soat

@router.message(Command("members"))
async def cmd_members(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: `/members @chat [limit]`")
        return

    chat = parts[1]
    limit = int(parts[2]) if len(parts) > 2 else 30
    limit = min(limit, 100)

    wait = await message.answer("⏳ Yuklanmoqda...")
    try:
        members = await userbot.get_members(chat, limit)
        lines = [f"👥 **{chat} — {len(members)} ta a'zo:**\n"]
        for i, m in enumerate(members, 1):
            lines.append(f"{i}. {m['name']} {m['username']}")
        await wait.edit_text("\n".join(lines)[:4000])
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")

@router.message(Command("history"))
async def cmd_history(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: `/history @chat [limit]`")
        return

    chat = parts[1]
    limit = int(parts[2]) if len(parts) > 2 else 10
    limit = min(limit, 50)

    wait = await message.answer("⏳ Yuklanmoqda...")
    try:
        msgs = await userbot.get_history(chat, limit)
        lines = [f"📜 **{chat} — oxirgi {len(msgs)} xabar:**\n"]
        for m in msgs:
            lines.append(f"[{m['date']}] **{m['sender']}** (ID:{m['id']})\n{m['text']}\n")
        await wait.edit_text("\n".join(lines)[:4000])
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")

@router.message(Command("search"))
async def cmd_search(message: Message, userbot: UserBotClient):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ Format: `/search @chat kalit_so'z`")
        return

    chat, keyword = parts[1], parts[2]
    wait = await message.answer(f"🔍 Qidirilmoqda: **{keyword}**...")
    try:
        results = await userbot.search_messages(chat, keyword)
        if not results:
            await wait.edit_text(f"🔍 **{keyword}** bo'yicha hech narsa topilmadi.")
            return
        lines = [f"🔍 **'{keyword}'** — {len(results)} ta natija:\n"]
        for r in results:
            lines.append(f"ID:{r['id']} [{r['date']}]\n{r['text']}\n")
        await wait.edit_text("\n".join(lines)[:4000])
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")

@router.message(Command("mute"))
async def cmd_mute(message: Message, userbot: UserBotClient):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: `/mute @chat [30m/2h/1d]`")
        return

    chat = parts[1]
    duration_str = parts[2] if len(parts) > 2 else "1h"
    seconds = parse_duration(duration_str)

    try:
        await userbot.mute_chat(chat, seconds)
        await message.answer(f"🔇 {chat} — {duration_str} ga jim qilindi.")
    except Exception as e:
        await message.answer(f"❌ Xato: `{e}`")

@router.message(Command("monitor"))
async def cmd_monitor(message: Message, db: Database):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("❌ Format: `/monitor @chat kalit_so'z`")
        return
    chat, keyword = parts[1], parts[2]
    await db.monitor_add(chat, keyword)
    await message.answer(f"👁 Monitor qo'shildi: **{chat}** → `{keyword}`")

@router.message(Command("monitor_list"))
async def cmd_monitor_list(message: Message, db: Database):
    monitors = await db.monitor_list()
    if not monitors:
        await message.answer("Hech qanday monitor yo'q.")
        return
    lines = ["👁 **Faol monitorlar:**\n"]
    for m in monitors:
        lines.append(f"ID:{m['id']} | {m['chat_id']} → `{m['keyword']}`")
    await message.answer("\n".join(lines))

@router.message(Command("monitor_off"))
async def cmd_monitor_off(message: Message, db: Database):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Format: `/monitor_off ID`")
        return
    await db.monitor_remove(int(parts[1]))
    await message.answer(f"✅ Monitor {parts[1]} o'chirildi.")

@router.message(Command("autoreply"))
async def cmd_autoreply(message: Message, db: Database):
    parts = message.text.split(maxsplit=1)
    body = parts[1].strip() if len(parts) > 1 else ""

    if body.startswith("status"):
        ar = await db.get_autoreply()
        status = "✅ Yoqiq" if ar and ar["active"] else "❌ O'chiq"
        text = ar["reply_text"] if ar else "—"
        await message.answer(f"🔄 Avtomatik javob: {status}\nMatn: {text}")

    elif body.startswith("off"):
        ar = await db.get_autoreply()
        await db.set_autoreply(False, ar["reply_text"] if ar else "")
        await message.answer("❌ Avtomatik javob o'chirildi.")

    elif body.startswith("on"):
        reply_text = body[2:].strip(" |").strip()
        if not reply_text:
            reply_text = "Hozir band, keyinroq javob beraman."
        await db.set_autoreply(True, reply_text)
        await message.answer(f"✅ Avtomatik javob yoqildi:\n_{reply_text}_")

    else:
        await message.answer(
            "❓ Ishlatish:\n"
            "`/autoreply status` — holat\n"
            "`/autoreply on | Hozir band...` — yoqish\n"
            "`/autoreply off` — o'chirish"
        )
