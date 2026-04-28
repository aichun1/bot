import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from google_apis import google_api

router = Router()

def _check_google(message) -> bool:
    if not google_api.is_available():
        return False
    return True

# ─── CALENDAR ──────────────────────────────────────────────

@router.message(Command("cal"))
async def cmd_cal(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "❓ Format:\n"
            "`/cal bugun` — bugungi tadbirlar\n"
            "`/cal ertaga` — ertangi tadbirlar\n"
            "`/cal qosh HH:MM | sarlavha` — yangi tadbir"
        )
        return

    if not _check_google(message):
        await message.answer("⚠️ Google API o'rnatilmagan yoki sozlanmagan. README ga qarang.")
        return

    action = parts[1].lower()

    if action in ("bugun", "today"):
        try:
            events = google_api.get_events(day_offset=0)
            if not events:
                await message.answer("📅 Bugun hech qanday tadbir yo'q.")
                return
            lines = ["📅 **Bugungi tadbirlar:**\n"]
            for e in events:
                lines.append(f"🕐 {e['start']} — **{e['title']}**")
                if e["location"]:
                    lines.append(f"   📍 {e['location']}")
            await message.answer("\n".join(lines))
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")

    elif action in ("ertaga", "tomorrow"):
        try:
            events = google_api.get_events(day_offset=1)
            if not events:
                await message.answer("📅 Ertaga hech qanday tadbir yo'q.")
                return
            lines = ["📅 **Ertangi tadbirlar:**\n"]
            for e in events:
                lines.append(f"🕐 {e['start']} — **{e['title']}**")
            await message.answer("\n".join(lines))
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")

    elif action in ("qosh", "add"):
        rest = parts[2] if len(parts) > 2 else ""
        if "|" not in rest:
            await message.answer("❌ Format: `/cal qosh HH:MM | sarlavha`")
            return
        time_str, title = rest.split("|", 1)
        time_str = time_str.strip()
        title = title.strip()
        try:
            created = google_api.add_event(title, time_str)
            await message.answer(f"✅ Tadbir qo'shildi: **{title}** — {created['start']}")
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")
    else:
        await message.answer("❓ `/cal bugun`, `/cal ertaga`, yoki `/cal qosh HH:MM | sarlavha`")

# ─── GMAIL ─────────────────────────────────────────────────

@router.message(Command("gmail"))
async def cmd_gmail(message: Message):
    parts = message.text.split(maxsplit=3)
    
    if not _check_google(message):
        await message.answer("⚠️ Google API sozlanmagan.")
        return

    if len(parts) < 2:
        # Default: oxirgi 5 ta email
        _show_emails(message, 5)
        return

    action = parts[1]

    if action.isdigit():
        count = min(int(action), 20)
        try:
            emails = google_api.get_emails(count)
            if not emails:
                await message.answer("📧 Inbox bo'sh.")
                return
            lines = [f"📧 **Oxirgi {len(emails)} email:**\n"]
            for e in emails:
                lines.append(
                    f"👤 {e['from']}\n"
                    f"📌 {e['subject']}\n"
                    f"📅 {e['date'][:16]}\n"
                    f"💬 {e['snippet']}\n"
                )
            await message.answer("\n".join(lines)[:4000])
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")

    elif action == "yuborish":
        # /gmail yuborish email@... | mavzu | matn
        rest = " ".join(parts[2:]) if len(parts) > 2 else ""
        token = rest.split("|")
        if len(token) < 3:
            await message.answer("❌ Format: `/gmail yuborish email@... | mavzu | matn`")
            return
        to_email, subject, body = token[0].strip(), token[1].strip(), token[2].strip()
        try:
            google_api.send_email(to_email, subject, body)
            await message.answer(f"✅ Email yuborildi → {to_email}")
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")
    else:
        await message.answer("❓ `/gmail 10` yoki `/gmail yuborish email | mavzu | matn`")

async def _show_emails(message: Message, count: int):
    try:
        emails = google_api.get_emails(count)
        if not emails:
            await message.answer("📧 Inbox bo'sh.")
            return
        lines = [f"📧 **Oxirgi {len(emails)} email:**\n"]
        for e in emails:
            lines.append(f"👤 {e['from']}\n📌 {e['subject']}\n")
        await message.answer("\n".join(lines)[:4000])
    except Exception as ex:
        await message.answer(f"❌ Xato: `{ex}`")

# ─── DRIVE ─────────────────────────────────────────────────

@router.message(Command("drive"))
async def cmd_drive(message: Message):
    parts = message.text.split(maxsplit=2)
    
    if not _check_google(message):
        await message.answer("⚠️ Google API sozlanmagan.")
        return

    if len(parts) < 2:
        await message.answer(
            "❓ Format:\n"
            "`/drive search nomi` — fayl qidirish\n"
            "`/drive upload` — fayl yuklash (xabar bilan fayl yuboring)"
        )
        return

    action = parts[1].lower()

    if action == "search":
        query = parts[2] if len(parts) > 2 else ""
        if not query:
            await message.answer("❌ Format: `/drive search fayl_nomi`")
            return
        try:
            files = google_api.search_files(query)
            if not files:
                await message.answer(f"🔍 '{query}' bo'yicha hech narsa topilmadi.")
                return
            lines = [f"💾 **'{query}' natijalari:**\n"]
            for f in files:
                lines.append(
                    f"📄 **{f['name']}**\n"
                    f"   📅 {f['modified']} | 📦 {f['size']}\n"
                    f"   🔗 {f['link']}\n"
                )
            await message.answer("\n".join(lines)[:4000])
        except Exception as ex:
            await message.answer(f"❌ Xato: `{ex}`")

    elif action == "upload":
        await message.answer("📤 Faylni shu xabarga javob sifatida yuboring.")
    else:
        await message.answer("❓ `search` yoki `upload` buyrug'ini yozing.")

@router.message(F.document & F.caption.startswith("/drive upload"))
async def handle_drive_upload(message: Message):
    wait = await message.answer("⬇️ Fayl yuklanmoqda...")
    try:
        file = await message.bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        local_path = f"downloads/{file_name}"
        os.makedirs("downloads", exist_ok=True)
        await message.bot.download_file(file.file_path, local_path)
        
        await wait.edit_text("☁️ Drive ga yuklanmoqda...")
        result = google_api.upload_file(local_path)
        await wait.edit_text(
            f"✅ **Drive ga yuklandi:**\n"
            f"📄 {result['name']}\n"
            f"🔗 {result['link']}"
        )
        os.remove(local_path)
    except Exception as ex:
        await wait.edit_text(f"❌ Xato: `{ex}`")
