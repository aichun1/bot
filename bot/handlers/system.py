from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database
from config import cfg

router = Router()

HELP_TEXT = """
🤖 **SuperBot — Buyruqlar**

**🔐 Kirish**
`/pass <parol>` — Parol bilan kirish
`/whoami` — Kim ekanligingni ko'rish

**📨 Xabar yuborish**
`/send @chat yoki chat_id | matn` — Xabar yuborish
`/forward @from @to msg_id` — Xabarni forward qilish
`/delete @chat msg_id` — Xabarni o'chirish
`/pin @chat msg_id` — Xabarni pin qilish
`/broadcast @chat1,@chat2 | matn` — Ko'p guruhga yuborish

**👥 Guruh boshqaruvi**
`/members @chat [limit]` — A'zolar ro'yxati
`/history @chat [limit]` — Oxirgi xabarlar
`/search @chat kalit_so'z` — Xabar qidirish
`/mute @chat 1h/30m/1d` — Jimlik rejimi
`/download @chat msg_id` — Media yuklab olish

**⏰ Rejalashtirilgan xabarlar**
`/schedule HH:MM @chat | matn` — Bugun soat HH:MM da yuborish
`/schedule_list` — Navbattagi xabarlar
`/schedule_cancel id` — Bekor qilish

**🤖 AI va Ovoz**
`/ai <savol>` — AI botdan javob olish
`/audio` — Ovozli xabarni yuborish → matn

**📅 Google Calendar**
`/cal bugun` — Bugungi tadbirlar
`/cal ertaga` — Ertangi tadbirlar
`/cal qosh HH:MM | sarlavha` — Yangi tadbir

**📧 Gmail**
`/gmail [10]` — Oxirgi emaillar
`/gmail yuborish email@... | mavzu | matn` — Email yuborish

**💾 Google Drive**
`/drive search nomi` — Fayl qidirish
`/drive upload` — Fayl yuklash (xabar bilan fayl yuboring)

**👁 Monitoring**
`/monitor @chat kalit_so'z` — Monitoring qo'shish
`/monitor_list` — Faol monitorlar
`/monitor_off id` — O'chirish

**🔄 Avtomatik javob**
`/autoreply on | javob matni` — Yoqish
`/autoreply off` — O'chirish
`/autoreply status` — Holati

**🚫 Qora ro'yxat**
`/bl add chat_id [nom]` — Qo'shish
`/bl remove chat_id` — O'chirish
`/bl list` — Ro'yxat

**📊 Tizim**
`/status` — Bot holati
`/sessions` — Kim kirgan
`/digest` — Kunlik hisobot
"""

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database):
    user = message.from_user
    is_owner = user.id == cfg.OWNER_ID
    is_authed = await db.is_authed(user.id)

    if is_owner or is_authed:
        await message.answer(
            f"👋 Salom, **{user.first_name}**!\n\n"
            f"✅ Tizimga kirgansiz.\n"
            f"📋 Barcha buyruqlar: /help"
        )
    else:
        await message.answer(
            f"👋 Salom!\n\n"
            f"🔐 Bu shaxsiy bot. Kirish uchun:\n"
            f"`/pass <parol>`"
        )

@router.message(Command("pass"))
async def cmd_pass(message: Message, db: Database):
    user = message.from_user
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Ishlatish: `/pass <parol>`")
        return

    entered = parts[1].strip()
    if entered == cfg.BOT_PASSWORD:
        await db.set_auth(user.id, user.username, True)
        await message.answer(
            "✅ **To'g'ri parol!**\n\n"
            "Endi barcha buyruqlardan foydalanishingiz mumkin.\n"
            "/help — buyruqlar ro'yxati"
        )
    else:
        await message.answer("❌ **Noto'g'ri parol!** Qaytadan urinib ko'ring.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)

@router.message(Command("whoami"))
async def cmd_whoami(message: Message):
    u = message.from_user
    is_owner = u.id == cfg.OWNER_ID
    await message.answer(
        f"👤 **Siz:**\n"
        f"ID: `{u.id}`\n"
        f"Ism: {u.full_name}\n"
        f"Username: @{u.username or '—'}\n"
        f"Rol: {'👑 Egasi' if is_owner else '✅ Ruxsatli foydalanuvchi'}"
    )

@router.message(Command("status"))
async def cmd_status(message: Message, db: Database):
    sessions = await db.fetchall("SELECT * FROM sessions WHERE authed=1")
    scheduled = await db.schedule_list()
    monitors = await db.monitor_list()
    ar = await db.get_autoreply()

    await message.answer(
        f"📊 **Bot holati:**\n\n"
        f"👥 Ruxsatli foydalanuvchilar: {len(sessions)}\n"
        f"⏰ Navbatdagi xabarlar: {len(scheduled)}\n"
        f"👁 Faol monitorlar: {len(monitors)}\n"
        f"🔄 Avtomatik javob: {'✅ Yoqiq' if ar and ar['active'] else '❌ O\'chiq'}\n"
    )

@router.message(Command("sessions"))
async def cmd_sessions(message: Message, db: Database):
    if message.from_user.id != cfg.OWNER_ID:
        await message.answer("❌ Faqat egasi uchun.")
        return
    sessions = await db.fetchall("SELECT * FROM sessions ORDER BY last_seen DESC")
    if not sessions:
        await message.answer("Hech kim kirmagan.")
        return
    lines = ["👥 **Kirgan foydalanuvchilar:**\n"]
    for s in sessions:
        lines.append(
            f"• ID: `{s['user_id']}` @{s['username'] or '—'}\n"
            f"  So'nggi: {(s['last_seen'] or '')[:16]}\n"
        )
    await message.answer("\n".join(lines))

@router.message(Command("digest"))
async def cmd_digest(message: Message, db: Database):
    scheduled = await db.schedule_list()
    monitors = await db.monitor_list()
    bl = await db.blacklist_get()

    lines = [
        "📋 **Kunlik hisobot:**\n",
        f"⏰ Navbatdagi xabarlar: {len(scheduled)}",
        f"👁 Faol monitorlar: {len(monitors)}",
        f"🚫 Qora ro'yxat: {len(bl)} chat",
    ]

    if scheduled:
        lines.append("\n**📅 Xabarlar:**")
        for s in scheduled[:5]:
            lines.append(f"  • {s['send_at'][:16]} → {s['chat_id']}: {s['message'][:40]}...")

    await message.answer("\n".join(lines))
