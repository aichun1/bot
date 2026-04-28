from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import Database

router = Router()

@router.message(Command("bl"))
async def cmd_blacklist(message: Message, db: Database):
    """
    /bl add chat_id [nom]
    /bl remove chat_id
    /bl list
    """
    parts = message.text.split(maxsplit=3)
    if len(parts) < 2:
        await message.answer(
            "❌ Format:\n"
            "`/bl add @chat [nom]`\n"
            "`/bl remove @chat`\n"
            "`/bl list`"
        )
        return

    action = parts[1].lower()

    if action == "list":
        items = await db.blacklist_get()
        if not items:
            await message.answer("🚫 Qora ro'yxat bo'sh.")
            return
        lines = ["🚫 **Qora ro'yxat:**\n"]
        for b in items:
            label = f" ({b['label']})" if b["label"] else ""
            lines.append(f"• `{b['chat_id']}`{label}")
        await message.answer("\n".join(lines))

    elif action == "add":
        if len(parts) < 3:
            await message.answer("❌ Format: `/bl add @chat [nom]`")
            return
        chat_id = parts[2]
        label = parts[3] if len(parts) > 3 else ""
        await db.blacklist_add(chat_id, label)
        await message.answer(f"✅ Qora ro'yxatga qo'shildi: `{chat_id}`")

    elif action == "remove":
        if len(parts) < 3:
            await message.answer("❌ Format: `/bl remove @chat`")
            return
        chat_id = parts[2]
        await db.blacklist_remove(chat_id)
        await message.answer(f"✅ Qora ro'yxatdan o'chirildi: `{chat_id}`")

    else:
        await message.answer("❌ Noma'lum buyruq. `add`, `remove`, yoki `list` yozing.")
