import os
import tempfile
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from userbot.client import UserBotClient
from config import cfg

router = Router()

@router.message(Command("ai"))
async def cmd_ai(message: Message, userbot: UserBotClient):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Format: `/ai <savol>`")
        return

    question = parts[1].strip()
    wait = await message.answer(f"🤖 AI dan javob kutilmoqda...")

    try:
        answer = await userbot.ask_ai_bot(cfg.AI_BOT, question, timeout=25)
        await wait.edit_text(f"🤖 **AI Javobi:**\n\n{answer[:4000]}")
    except Exception as e:
        await wait.edit_text(f"❌ AI bot bilan xato: `{e}`")

@router.message(Command("audio"))
async def cmd_audio(message: Message):
    await message.answer(
        "🎙️ Endi menga **ovozli xabar** yuboring.\n"
        "Men uni matnга aylantiraman."
    )

@router.message(F.voice | F.audio)
async def handle_voice(message: Message, userbot: UserBotClient):
    wait = await message.answer("🎙️ Ovoz yuklanmoqda...")

    try:
        os.makedirs("downloads", exist_ok=True)

        # Faylni yuklab olamiz
        if message.voice:
            file = await message.bot.get_file(message.voice.file_id)
            ext = "ogg"
        else:
            file = await message.bot.get_file(message.audio.file_id)
            ext = "mp3"

        file_path = f"downloads/audio_{message.message_id}.{ext}"
        await message.bot.download_file(file.file_path, file_path)

        await wait.edit_text("🔤 Whisper botga yuborilmoqda...")
        text = await userbot.send_audio_to_whisper(file_path, cfg.WHISPER_BOT, timeout=45)

        await wait.edit_text(f"📝 **Matn:**\n\n{text}")

        # Faylni o'chiramiz
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        await wait.edit_text(f"❌ Xato: `{e}`")
