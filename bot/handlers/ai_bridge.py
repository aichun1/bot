import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from google_apis.gemini_api import gemini
from config import cfg

router = Router()

# ─── AI CHAT ───────────────────────────────────────────────

@router.message(Command("ai"))
async def cmd_ai(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❓ Format: `/ai <savol>`\n\n"
            "Misol:\n"
            "`/ai Python da list nima?`\n"
            "`/ai Bugungi eng yaxshi yangiliklar?`"
        )
        return
    question = parts[1].strip()
    wait = await message.answer("🤖 Gemini fikrlamoqda...")
    answer = await gemini.ask(question)
    await wait.edit_text(f"🤖 **Gemini:**\n\n{answer[:4000]}")


@router.message(Command("sum"))
async def cmd_summarize(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Format: `/sum <uzun matn>`")
        return
    wait = await message.answer("📝 Qisqartirilmoqda...")
    result = await gemini.summarize(parts[1])
    await wait.edit_text(f"📝 **Xulosa:**\n\n{result[:4000]}")


@router.message(Command("tr"))
async def cmd_translate(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Format: `/tr til | matn`\nMisol: `/tr english | Salom dunyo`")
        return
    body = parts[1]
    if "|" in body:
        lang, text = body.split("|", 1)
        lang, text = lang.strip(), text.strip()
    else:
        lang, text = "english", body.strip()
    wait = await message.answer("🌐 Tarjima qilinmoqda...")
    result = await gemini.translate(text, lang)
    await wait.edit_text(f"🌐 **{lang.capitalize()}:**\n\n{result[:4000]}")


# ─── AUDIO → TEXT (Gemini, Whisper o'rniga) ────────────────

@router.message(Command("audio"))
async def cmd_audio(message: Message):
    await message.answer("🎙️ Ovozli xabar yuboring — Gemini matnга aylantiradi.")


@router.message(F.voice | F.audio)
async def handle_voice(message: Message):
    wait = await message.answer("🎙️ Ovoz yuklanmoqda...")
    try:
        os.makedirs("downloads", exist_ok=True)
        if message.voice:
            file = await message.bot.get_file(message.voice.file_id)
            ext = "ogg"
        else:
            file = await message.bot.get_file(message.audio.file_id)
            ext = "mp3"
        file_path = f"downloads/audio_{message.message_id}.{ext}"
        await message.bot.download_file(file.file_path, file_path)
        await wait.edit_text("🔤 Gemini audio o'girmoqda...")
        text = await gemini.audio_to_text(file_path)
        await wait.edit_text(f"📝 **Matn:**\n\n{text[:4000]}")
        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")


# ─── RASM TAHLILI ──────────────────────────────────────────

@router.message(F.photo)
async def handle_photo(message: Message):
    wait = await message.answer("🔍 Rasm tahlil qilinmoqda...")
    try:
        os.makedirs("downloads", exist_ok=True)
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        file_path = f"downloads/photo_{message.message_id}.jpg"
        await message.bot.download_file(file.file_path, file_path)
        question = message.caption or "Bu rasmda nima bor? Batafsil tushuntir."
        result = await gemini.analyze_image(file_path, question)
        await wait.edit_text(f"🖼️ **Gemini:**\n\n{result[:4000]}")
        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")
